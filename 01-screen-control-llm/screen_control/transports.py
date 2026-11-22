"""Transports: how the loop actually touches a screen.

Two implementations:

  BrowserUseTransport  — drives a live Chromium through CDP. It is a thin adapter over
                         four injected primitives (js / cdp / screenshot / navigate),
                         so it works both inside the Hermes browser sandbox and in a
                         standalone Playwright/pychrome harness.
  MockTransport        — an in-memory screen used by the tests. It exists so the loop,
                         the guard and the planner contract can be certified without a
                         browser: a mechanics bug must be findable without a model and
                         without a network.

Why CDP and not Playwright selectors: the accessibility tree gives every interactive
node a stable backendDOMNodeId and an accessible NAME, which is what an LLM can reason
about. Resolving coordinates from DOM.getBoxModel at click time means scroll, zoom and
sticky headers cannot silently redirect the click.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Optional

INTERACTIVE_ROLES = {
    "button", "link", "textbox", "checkbox", "radio", "combobox", "listbox",
    "menuitem", "tab", "switch", "searchbox", "spinbutton", "slider", "option",
}


class BrowserUseTransport:
    """Adapter over injected CDP primitives.

    js(expr) -> Any                evaluate JS in the page
    cdp(domain.method, **kw) -> dict
    screenshot() -> str path
    navigate(url) -> None
    """

    def __init__(self, js: Callable, cdp: Callable, screenshot: Callable,
                 navigate: Optional[Callable] = None, max_elements: int = 120):
        self.js = js
        self.cdp = cdp
        self._shot = screenshot
        self._nav = navigate
        self.max_elements = max_elements
        self._names: Dict[str, str] = {}

    # ------------------------------------------------------------------ observe
    def observe(self) -> dict:
        tree = self.cdp("Accessibility.getFullAXTree")
        nodes = tree.get("nodes", [])
        elements: List[dict] = []
        for n in nodes:
            role = (n.get("role") or {}).get("value", "")
            name = ((n.get("name") or {}).get("value") or "").strip()
            if role not in INTERACTIVE_ROLES or not name:
                continue
            bid = n.get("backendDOMNodeId")
            if not bid:
                continue
            handle = str(bid)
            self._names[handle] = name
            elements.append({"handle": handle, "role": role, "name": name[:120]})
            if len(elements) >= self.max_elements:
                break

        meta = self.js(
            "(() => ({url: location.href, title: document.title, "
            "w: innerWidth, h: innerHeight, scrollY: Math.round(scrollY), "
            "text: (document.body ? document.body.innerText : '').slice(0, 1200)}))()"
        )
        return {
            "url": meta.get("url"),
            "title": meta.get("title"),
            "viewport": {"w": meta.get("w"), "h": meta.get("h"), "scroll_y": meta.get("scrollY")},
            "elements": elements,
            "visible_text": meta.get("text", "")[:1200],
        }

    def element_name(self, handle: Optional[str]) -> Optional[str]:
        if not handle:
            return None
        return self._names.get(str(handle))

    # ------------------------------------------------------------------ execute
    def _center(self, handle: str) -> Optional[dict]:
        try:
            m = self.cdp("DOM.getBoxModel", backendNodeId=int(handle))
        except Exception:
            return None
        quad = (m.get("model") or {}).get("content") or []
        if len(quad) != 8:
            return None
        xs, ys = quad[0::2], quad[1::2]
        return {"x": sum(xs) / 4.0, "y": sum(ys) / 4.0}

    def _click_xy(self, x: float, y: float) -> None:
        for t in ("mousePressed", "mouseReleased"):
            self.cdp("Input.dispatchMouseEvent", type=t, x=x, y=y, button="left", clickCount=1)

    def execute(self, action) -> tuple:
        v = action.verb
        try:
            if v == "navigate":
                if self._nav:
                    self._nav(action.url)
                else:
                    self.js(f"location.href = {json.dumps(action.url)}")
                time.sleep(0.8)
                return True, f"navigated to {action.url}"

            if v == "click":
                if action.target:
                    pt = self._center(action.target)
                    if pt is None:
                        return False, f"no box model for handle {action.target} (element gone?)"
                    self._click_xy(pt["x"], pt["y"])
                    return True, f"clicked {self._names.get(action.target, action.target)} at ({pt['x']:.0f},{pt['y']:.0f})"
                if action.x is not None and action.y is not None:
                    self._click_xy(action.x, action.y)
                    return True, f"clicked coords ({action.x},{action.y})"
                return False, "no target"

            if v == "type":
                if action.target:
                    pt = self._center(action.target)
                    if pt is None:
                        return False, f"no box model for handle {action.target}"
                    self._click_xy(pt["x"], pt["y"])
                if action.text:
                    self.cdp("Input.insertText", text=action.text)
                if action.key:
                    self._press(action.key)
                return True, f"typed {len(action.text or '')} chars" + (f" + {action.key}" if action.key else "")

            if v == "key":
                self._press(action.key)
                return True, f"pressed {action.key}"

            if v == "scroll":
                dy = action.dy or 600
                # Live-testing note: some CDP daemons do not answer
                # Input.dispatchMouseEvent(type="mouseWheel") and the call times out
                # after 5s. A JS scroll is equivalent for page scrolling and never
                # blocks, so it is used as the fallback (not the primary) path.
                try:
                    self.cdp("Input.dispatchMouseEvent", type="mouseWheel", x=400, y=400,
                             deltaX=0, deltaY=dy)
                    return True, f"scrolled {dy}px via wheel event"
                except Exception:
                    before = self.js("Math.round(scrollY)")
                    self.js(f"window.scrollBy(0, {dy})")
                    time.sleep(0.15)
                    after = self.js("Math.round(scrollY)")
                    return True, f"scrolled {dy}px via js fallback ({before} -> {after})"

            if v == "wait":
                time.sleep(float(action.meta.get("seconds", 1.0)))
                return True, "waited"

            if v == "read":
                sel = action.meta.get("selector") or action.target
                text = self.js(
                    "(() => { const e = document.querySelector(%s); return e ? e.innerText : null; })()"
                    % json.dumps(sel)
                )
                if text is None:
                    return False, f"selector not found: {sel}"
                action.meta["result"] = text[:4000]
                return True, f"read {len(text)} chars from {sel}"

            return False, f"verb {v} not implemented by this transport"
        except Exception as exc:
            return False, f"transport error: {type(exc).__name__}: {exc}"

    def _press(self, combo: str) -> None:
        parts = [p.strip() for p in combo.split("+")]
        mods = 0
        for p in parts[:-1]:
            mods |= {"Alt": 1, "Control": 2, "Meta": 4, "Shift": 8}.get(p, 0)
        key = parts[-1]
        code = {"Enter": 13, "Tab": 9, "Escape": 27, "Backspace": 8}.get(key, None)
        if code is None and len(key) == 1:
            code = ord(key.upper())
        if code is None:
            raise ValueError(f"unsupported key {key}")
        for t in ("keyDown", "keyUp"):
            self.cdp("Input.dispatchKeyEvent", type=t, key=key, windowsVirtualKeyCode=code,
                     modifiers=mods, text=key if len(key) == 1 else "")

    # ------------------------------------------------------------------ verify
    def verify(self, expect: str) -> tuple:
        """Cheap, honest post-condition: does the expectation appear in the page?"""
        needle = expect.strip().lower()
        if not needle:
            return True, "empty expectation"
        state = self.js(
            "(() => ({u: location.href, t: document.title, "
            "b: (document.body ? document.body.innerText : '').slice(0, 6000)}))()"
        )
        hay = " ".join([state.get("u") or "", state.get("t") or "", state.get("b") or ""]).lower()
        # check the longest content words, not the whole sentence
        words = [w for w in needle.replace(",", " ").replace(".", " ").split() if len(w) > 3]
        if not words:
            return True, "no content words to check"
        hits = [w for w in words if w in hay]
        ok = len(hits) >= max(1, int(len(words) * 0.5))
        return ok, f"{len(hits)}/{len(words)} expectation words present"

    def screenshot(self) -> Optional[str]:
        try:
            return self._shot()
        except Exception:
            return None


class MockTransport:
    """An in-memory screen. Used by the certification tests."""

    def __init__(self, pages: Optional[Dict[str, dict]] = None, start: str = "home"):
        self.pages = pages or {"home": {"title": "Home", "text": "welcome",
                                        "elements": [{"handle": "1", "role": "button", "name": "Continue"}]}}
        self.current = start
        self.log: List[tuple] = []

    def observe(self) -> dict:
        p = self.pages[self.current]
        return {"url": f"mock://{self.current}", "title": p["title"],
                "viewport": {"w": 1280, "h": 800, "scroll_y": 0},
                "elements": p.get("elements", []), "visible_text": p.get("text", "")}

    def element_name(self, handle: Optional[str]) -> Optional[str]:
        for e in self.pages[self.current].get("elements", []):
            if e["handle"] == str(handle):
                return e["name"]
        return None

    def execute(self, action) -> tuple:
        self.log.append((action.verb, action.target, action.text))
        p = self.pages[self.current]
        if action.verb == "click":
            for e in p.get("elements", []):
                if e["handle"] == str(action.target):
                    if e.get("goes_to") and e["goes_to"] in self.pages:
                        self.current = e["goes_to"]
                        return True, f"clicked {e['name']} -> {self.current}"
                    p["text"] = p.get("text", "") + f" [clicked {e['name']}]"
                    return True, f"clicked {e['name']}"
            return False, f"no element {action.target}"
        if action.verb == "type":
            p["text"] = p.get("text", "") + f" [typed {action.text}]"
            return True, "typed"
        if action.verb == "read":
            action.meta["result"] = p.get("text", "")
            return True, "read"
        if action.verb == "wait":
            return True, "waited"
        if action.verb == "navigate":
            self.current = action.url.replace("mock://", "")
            return True, "navigated"
        return False, f"unsupported {action.verb}"

    def verify(self, expect: str) -> tuple:
        hay = (self.pages[self.current].get("text", "") + " " +
               self.pages[self.current].get("title", "")).lower()
        words = [w for w in expect.lower().replace(",", " ").split() if len(w) > 3]
        hits = [w for w in words if w in hay]
        return (len(hits) >= max(1, int(len(words) * 0.5)) if words else True), f"{len(hits)}/{len(words)}"

    def screenshot(self) -> Optional[str]:
        return None
