"""Drive the multi-model chat sites over CDP instead of pixels, UIA or OCR.

Why this exists: measured 2026-11-22, all three sites hide their composer from the accessibility
tree (arena.ai exposes only a `Group` for the whole page; 1min.ai exposes the sidebar and search box
but not the editor; chatplayground drops `Edit 'Message every model'` once a chat has messages).
Coordinate clicks also land wrong on this machine's second monitor, so UIA + pixels are both dead
ends for these surfaces. A Chrome launched with `--remote-debugging-port` gives the DOM, which has
selectors, text and a real `value` setter — the API rung of the ladder, and the only one that works
unattended here.

Setup (once):
    chrome.exe --remote-debugging-port=9222 --user-data-dir=C:/Users/zerou/chrome-agent-profile
    # sign in to arena.ai, web.chatplayground.ai, app.1min.ai in that window; the session persists

Then:
    python prototype/cdp_multi_site.py --discover
    python prototype/cdp_multi_site.py --ask "your prompt" --site chatplayground

`--discover` prints what each site actually exposes (editors, buttons, mode selects) so selectors are
recorded from the live DOM instead of guessed. Nothing here types into a password field: if a login
wall is detected the site is reported as NEEDS_HUMAN and skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

SITES = {
    "arena": {"url": "https://arena.ai/", "mode_select": "Agent"},
    "chatplayground": {"url": "https://web.chatplayground.ai/", "mode_select": None},
    "1min": {"url": "https://app.1min.ai/chat-with-ai", "mode_select": None},
}

LOGIN_WALL = re.compile(r"log ?in|sign ?in|continue with google|enter your email", re.I)

#: Selector families tried in order. Discovery reports which one is live per site.
EDITOR_SELECTORS = ["textarea", "div[contenteditable='true']", "[role='textbox']"]
SEND_SELECTORS = [
    "button[aria-label*='Send' i]", "button:has-text('Send')", "button[type='submit']",
    "[data-testid*='send' i]", "button[aria-label*='send' i]",
]


def connect(port: int):
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    ctx = browser.contexts[0]
    return pw, browser, ctx


def page_for(ctx, url: str):
    host = url.split("//")[1].split("/")[0]
    for pg in ctx.pages:
        if host in pg.url:
            return pg
    pg = ctx.new_page()
    pg.goto(url, wait_until="domcontentloaded")
    return pg


def inventory(page) -> dict:
    """What this page actually exposes. Run this first; record the result, never guess."""
    def count(sel: str) -> int:
        try:
            return page.locator(sel).count()
        except Exception:
            return -1

    editors = {sel: count(sel) for sel in EDITOR_SELECTORS}
    buttons = []
    try:
        buttons = page.eval_on_selector_all(
            "button", "els => els.slice(0,80).map(e => (e.innerText||'').trim().slice(0,40) || e.getAttribute('aria-label') || '(icon)')"
        )
    except Exception:
        pass
    selects = []
    try:
        selects = page.eval_on_selector_all(
            "select,[role='combobox'],[role='listbox']",
            "els => els.map(e => ({tag:e.tagName, label:(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,40)}))",
        )
    except Exception:
        pass
    body = ""
    try:
        body = page.inner_text("body")[:1200]
    except Exception:
        pass
    return {
        "url": page.url,
        "title": page.title(),
        "login_wall": bool(LOGIN_WALL.search(body)),
        "editors": editors,
        "buttons": buttons,
        "mode_controls": selects,
    }


def first_match(page, selectors: list[str]):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                return sel, loc
        except Exception:
            continue
    return None, None


def ask(page, prompt: str, timeout_s: int = 240) -> dict:
    """Fill, submit, wait for the answer to settle, return the text. Never types credentials."""
    inv = inventory(page)
    if inv["login_wall"]:
        return {"verdict": "NEEDS_HUMAN", "reason": "login wall", "url": inv["url"]}

    ed_sel, editor = first_match(page, EDITOR_SELECTORS)
    if editor is None:
        return {"verdict": "BLOCKED", "reason": "no composer found", "inventory": inv}

    editor.click()
    editor.fill(prompt)  # works for textarea; contenteditable needs keyboard
    if not editor.input_value() if hasattr(editor, "input_value") else False:
        pass

    send_sel, send = first_match(page, SEND_SELECTORS)
    if send is not None:
        send.click()
    else:
        editor.press("Enter")

    # settle: text length stops changing for 3 consecutive polls
    last, stable, t0 = -1, 0, time.time()
    while time.time() - t0 < timeout_s:
        time.sleep(3)
        try:
            txt = page.inner_text("body")
        except Exception:
            continue
        if len(txt) == last:
            stable += 1
            if stable >= 3:
                return {"verdict": "OK", "editor": ed_sel, "send": send_sel,
                        "elapsed_s": round(time.time() - t0, 1), "chars": len(txt)}
        else:
            stable = 0
            last = len(txt)
    return {"verdict": "TIMEOUT", "editor": ed_sel, "send": send_sel,
            "elapsed_s": round(time.time() - t0, 1)}


def extract(page) -> str:
    """Best-effort transcript text for the whole page, one line per block."""
    try:
        return page.inner_text("body")
    except Exception as exc:
        return f"(extract failed: {type(exc).__name__})"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9222)
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--ask")
    ap.add_argument("--site", choices=list(SITES), action="append")
    ap.add_argument("--out", default=str(Path(__file__).parent / "transcripts"))
    args = ap.parse_args(argv)

    sites = args.site or list(SITES)
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    pw, browser, ctx = connect(args.port)
    report = {}
    try:
        for name in sites:
            pg = page_for(ctx, SITES[name]["url"])
            if args.discover:
                inv = inventory(pg)
                report[name] = inv
                print(json.dumps({name: inv}, indent=2)[:2500])
                continue
            if not args.ask:
                continue
            res = ask(pg, args.ask)
            report[name] = res
            if res.get("verdict") == "OK":
                stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
                path = out_dir / f"cdp_{name}_{stamp}.txt"
                path.write_text(extract(pg), encoding="utf-8")
                res["saved"] = str(path)
            print(json.dumps({name: res}, indent=2)[:1500])
    finally:
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        (out_dir / f"cdp_report_{stamp}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        browser.close(); pw.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
