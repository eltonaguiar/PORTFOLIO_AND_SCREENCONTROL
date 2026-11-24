"""Drive VS Code's AI chat panels (Kilo Code, Zoo Code, GitHub Copilot) over CDP.

This module is the extracted, working form of a control channel that was proven live on
Windows 11 / VS Code 1.144.0 (Electron 43, Chrome 150) against a Remote-SSH workspace.

Why CDP and not screen automation
--------------------------------
The panels are webviews or Monaco DOM. CDP addresses them directly, so there are no coordinates
to go stale, no focus to steal, and no risk of typing into the wrong panel — the two failure
modes that make keyboard/mouse automation of IDEs unreliable.

The three non-obvious facts this module encodes
-----------------------------------------------
1. **Chromium rejects every Origin header** on the CDP websocket (HTTP 403). Connect with
   ``suppress_origin=True``. No relaunch with ``--remote-allow-origins`` is needed.
2. **Copilot Chat is native workbench DOM, not a webview.** It never appears in ``/json/list``
   as an iframe. Its input is a Monaco ``textarea.ime-text-area``, and ``Input.insertText``
   does nothing unless you first *click that textarea's own rect*. Clicking the visual centre
   of the chat surface silently fails.
3. **"Running" is not "a button said Cancel".** A hidden zero-width control
   (``{"label":"Cancel restoring this checkpoint","vis":false,"w":0}``) makes an idle agent
   look busy. Require ``offsetParent !== null`` *and* a non-zero bounding box, and prefer the
   greyed-out Send arrow as the idle signal (disabled Send == empty composer == idle).

Usage
-----
    from screen_control.vscode_panels import Panels

    p = Panels()                     # assumes a debug listener on 127.0.0.1:9333
    for name, info in p.status().items():
        print(name, info["state"])

    p.send("kilo", "Continue the PROVEIT work. Reply with the file you changed.")
    print(p.read("kilo", tail=800))

Launching with the debug port is a separate concern; see VSCODE_PANEL_CDP_CONTROL.md.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
import urllib.request

DEFAULT_PORT = 9333
CDP_HOST = "127.0.0.1"

# Text nodes inside these elements are extension source, not chat content. Kilo injects
# `window.KILO_*` assignments as <script> text, which otherwise dominates any "last N nodes" read.
_SKIP_PARENTS = ("SCRIPT", "STYLE", "NOSCRIPT")

# Read the visible chat/composer text while ignoring script payloads.
_JS_TEXT_NODES = """
(() => {
  const doc = document.querySelector('iframe') ? document.querySelector('iframe').contentDocument
                                               : document;
  const out = [];
  const w = doc.createTreeWalker(doc.body || doc, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) {
    const p = w.currentNode.parentElement;
    if (p && /^(SCRIPT|STYLE|NOSCRIPT)$/.test(p.tagName)) continue;
    const v = (w.currentNode.nodeValue || '').trim();
    if (v) out.push(v);
  }
  return out;
})()
"""

# Buttons that are actually on screen. A hidden zero-box control must never count as evidence.
_JS_VISIBLE_BUTTONS = """
(() => {
  const doc = document.querySelector('iframe') ? document.querySelector('iframe').contentDocument
                                               : document;
  return [...doc.querySelectorAll('button, [role="button"]')]
    .filter(x => { const r = x.getBoundingClientRect();
                   return r.width > 0 && r.height > 0 && x.offsetParent !== null; })
    .map(x => (x.getAttribute('aria-label') || x.innerText || x.title || '').trim())
    .filter(Boolean);
})()
"""

# Identify the panel by the extension's own JS globals, never by the model name in the footer:
# a panel's model string changes (subq-savant-1.4 -> deepseek-flash) and then two different
# panels collapse to the same identity.
_JS_WHOAMI = """
(() => {
  const d = document.querySelector('iframe').contentDocument;
  let txt = '';
  const w = d.createTreeWalker(d.body || d, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) txt += (w.currentNode.nodeValue || '');
  for (const s of d.querySelectorAll('script')) txt += (s.textContent || '');
  return /kilocode\\.kilo-code|KILO_TOP_BAR/i.test(txt) ? 'kilo' : 'zoo';
})()
"""

# Copilot: locate the chat composer's own textarea, and the Send arrow, with live rects.
_JS_COPILOT_INPUT = """
(() => {
  const surfaces = [...document.querySelectorAll('[class*="chat-input-surface"]')]
      .filter(e => e.clientHeight > 40);
  if (!surfaces.length) return JSON.stringify({err: 'no chat-input-surface'});
  // IMPORTANT: textarea.ime-text-area is readOnly in VS Code 1.144, so Input.insertText against
  // it is a silent no-op. The real editable is DIV.native-edit-context inside the composer.
  const s = surfaces[0];            // BUGFIX: `s` was never defined, so this threw and eval returned None
  const ed = s.querySelector('.native-edit-context');
  if (!ed) return JSON.stringify({err: 'no native-edit-context in composer'});
  ed.scrollIntoView({block: 'center'});   // it can sit at negative y, and an off-screen click misses
  const er = ed.getBoundingClientRect();
  const cands = [{x: Math.round(er.x + er.width / 2), y: Math.round(er.y + er.height / 2), right: true}];
  const send = [...document.querySelectorAll('button, [role="button"]')]
      .find(b => /^Send/.test(b.getAttribute('aria-label') || ''));
  let srect = null;
  if (send) { const r = send.getBoundingClientRect();
              srect = {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)}; }
  return JSON.stringify({
    x: cands[0].x, y: cands[0].y,
    send: srect,
    send_disabled: send ? /disabled/.test(send.className.toString()) : null
  });
})()
"""


def norm(texts):
    """Join text nodes, normalising Monaco's non-breaking spaces.

    Monaco renders spaces as U+00A0, so ``'git log --oneline -3' in text`` is *False* against a
    composer that visibly contains that command. Every comparison must normalise first; a token
    with no spaces in it (``CDP-RECV-OK``) passes anyway, which is how this bug hides.
    """
    return "\n".join(texts).replace("\u00a0", " ")


class CDPError(RuntimeError):
    pass


class Session:
    """One attached target (a webview iframe or the workbench page)."""

    def __init__(self, ws_url, timeout=25):
        try:
            import websocket  # websocket-client
        except ImportError as exc:  # pragma: no cover
            raise CDPError("websocket-client is required: pip install websocket-client") from exc
        self._ids = itertools.count(1)
        # suppress_origin is mandatory: Chromium 403s any Origin header on /devtools/*
        self.ws = websocket.create_connection(ws_url, timeout=timeout, suppress_origin=True)
        self.cmd("Runtime.enable")

    def cmd(self, method, **params):
        mid = next(self._ids)
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise CDPError(f"{method}: {msg['error']}")
                return msg

    def eval(self, expr):
        res = self.cmd("Runtime.evaluate", expression=expr, returnByValue=True)["result"]["result"]
        val = res.get("value")
        if isinstance(val, str) and val[:1] in "{[":
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val
        return val

    def click(self, x, y):
        for kind in ("mousePressed", "mouseReleased"):
            self.cmd("Input.dispatchMouseEvent", type=kind, x=int(x), y=int(y),
                     button="left", clickCount=1)

    def press_enter(self):
        # A `char` event inserts a newline on some surfaces; keyDown+keyUp is the sending chord.
        self.cmd("Input.dispatchKeyEvent", type="keyDown", windowsVirtualKeyCode=13,
                 nativeVirtualKeyCode=13, key="Enter", code="Enter", text="\r", unmodifiedText="\r")
        self.cmd("Input.dispatchKeyEvent", type="keyUp", windowsVirtualKeyCode=13,
                 nativeVirtualKeyCode=13, key="Enter", code="Enter")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


class Panels:
    def __init__(self, port=DEFAULT_PORT, host=CDP_HOST):
        self.base = f"http://{host}:{port}"
        self._sessions = {}

    # ---------- discovery ----------
    def targets(self):
        try:
            with urllib.request.urlopen(f"{self.base}/json/list", timeout=8) as r:
                return json.loads(r.read().decode())
        except Exception as exc:
            raise CDPError(f"cannot reach CDP on {self.base}: {exc}") from exc

    def version(self):
        with urllib.request.urlopen(f"{self.base}/json/version", timeout=8) as r:
            return json.loads(r.read().decode())

    def attach(self, name):
        """Attach to one panel: 'kilo' | 'zoo' (webviews) or 'copilot' (the page target)."""
        if name in self._sessions:
            return self._sessions[name]
        tg = self.targets()
        if name == "copilot":
            t = next((x for x in tg if x.get("type") == "page"), None)
            if not t:
                raise CDPError("no page target")
            s = Session(t["webSocketDebuggerUrl"])
        else:
            found = None
            for t in [x for x in tg if x.get("type") == "iframe"]:
                s = Session(t["webSocketDebuggerUrl"])
                if s.eval(_JS_WHOAMI) == name:
                    found = s
                    break
                s.close()
            if not found:
                raise CDPError(f"panel {name!r} is not open as a webview")
            s = found
        self._sessions[name] = s
        return s

    # ---------- read ----------
    def read(self, name, tail=1200):
        s = self.attach(name)
        if name == "copilot":
            txt = norm(s.eval(_JS_TEXT_NODES) or [])
        else:
            txt = norm(s.eval(_JS_TEXT_NODES) or [])
        return txt[-tail:]

    def newest_turn(self, name, marker, tail=1200):
        """Slice from the last occurrence of *marker* (a phrase from your own last message).

        A transcript accumulates stale BLOCKED/DONE text and stale button labels; scanning the
        whole body reverses your conclusion. Always read forward from your own last message.
        """
        body = self.read(name, tail=200_000)
        i = body.rfind(marker)
        return body[i:] if i >= 0 else body[-tail:]

    # ---------- status ----------
    def status(self, name):
        s = self.attach(name)
        buttons = s.eval(_JS_VISIBLE_BUTTONS) or []
        if name == "copilot":
            info = s.eval(_JS_COPILOT_INPUT) or {}
            running = any(b.startswith("Cancel") for b in buttons)
            idle_by_arrow = info.get("send_disabled") is True and not running
            state = "running" if running and not idle_by_arrow else "idle"
            return {"state": state, "send_disabled": info.get("send_disabled"),
                    "evidence": [b for b in buttons if b.startswith("Cancel")][:2]}
        stop = [b for b in buttons if b[:6] in ("Stop", "Cancel", "Abort")]
        return {"state": "running" if stop else "idle", "evidence": stop[:2]}

    def status_all(self):
        out = {}
        for name in ("kilo", "zoo", "copilot"):
            try:
                out[name] = self.status(name)
            except CDPError as exc:
                out[name] = {"state": "unavailable", "error": str(exc)}
        return out

    # ---------- write ----------
    def send(self, name, text, verify=True):
        """Type *text* into the panel's composer and submit it.

        Returns True only if the composer is empty afterwards AND the text is present in the
        transcript. Never trust the click; a composer that clears without the message appearing
        is a silent no-op (observed on the chat surface before the textarea-rect fix).
        """
        s = self.attach(name)
        if name == "copilot":
            info = s.eval(_JS_COPILOT_INPUT) or {}
            if "err" in info:
                raise CDPError(info["err"])
            s.click(info["x"], info["y"])          # must be the textarea's own rect
            time.sleep(0.4)
            s.cmd("Input.insertText", text=text)
            time.sleep(0.7)
            landed = " " in text and norm(s.eval(_JS_TEXT_NODES) or [])
            if not landed:
                raise CDPError("text did not land in the Copilot editor")
            s.press_enter()
        else:
            ok = s.eval("""
            (() => {
              const d = document.querySelector('iframe').contentDocument;
              const ta = [...d.querySelectorAll('textarea')][0];
              if (!ta) return false;
              const set = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
              set.call(ta, %s);                     // plain ta.value = ... is ignored by React
              ta.dispatchEvent(new Event('input', {bubbles: true}));
              ta.focus();
              return true;
            })()
            """ % json.dumps(text))
            if not ok:
                raise CDPError("no composer textarea in that panel")
            s.press_enter()
        if not verify:
            return True
        time.sleep(3)
        body = self.read(name, tail=200_000)
        probe = text[:40].replace("\u00a0", " ")
        return probe in body

    def close(self):
        for s in self._sessions.values():
            s.close()
        self._sessions.clear()


def _cli(argv=None):
    ap = argparse.ArgumentParser(description="Drive VS Code AI panels over CDP")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="show running/idle per panel")
    r = sub.add_parser("read", help="print the tail of a panel")
    r.add_argument("panel", choices=["kilo", "zoo", "copilot"])
    r.add_argument("--tail", type=int, default=1500)
    snd = sub.add_parser("send", help="type and submit a message")
    snd.add_argument("panel", choices=["kilo", "zoo", "copilot"])
    snd.add_argument("text")
    args = ap.parse_args(argv)

    p = Panels(port=args.port)
    try:
        if args.cmd == "status":
            print(json.dumps(p.status_all(), indent=1))
        elif args.cmd == "read":
            print(p.read(args.panel, tail=args.tail))
        else:
            ok = p.send(args.panel, args.text)
            print(json.dumps({"panel": args.panel, "delivered": ok}))
            return 0 if ok else 2
    finally:
        p.close()
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
