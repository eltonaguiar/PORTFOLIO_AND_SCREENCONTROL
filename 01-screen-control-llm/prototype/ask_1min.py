"""Ask one prompt on 1min.ai over CDP, dismiss overlays first, save the raw transcript.

Measured obstacles this handles:
  * an Ant Design modal (`ant-modal-wrap`) intercepts pointer events on load; it must be closed or
    every click retries until timeout
  * the composer is a real `<textarea>` (class `ant-input`), so `fill()` works — no keystrokes needed
  * the send control is a right-side icon button; `Enter` in the textarea is the fallback
"""

from __future__ import annotations

import argparse
import pathlib
import re
import time

URL = "https://app.1min.ai/chat-with-ai"


def dismiss_modals(page, rounds: int = 3) -> list[str]:
    done = []
    for _ in range(rounds):
        wrap = page.locator("div.ant-modal-wrap")
        try:
            if not wrap.count() or not wrap.first.is_visible():
                break
        except Exception:
            break
        clicked = False
        for sel in ["button.ant-modal-close", ".ant-modal-close-x", "button[aria-label='Close']"]:
            loc = page.locator(sel)
            try:
                if loc.count() and loc.first.is_visible():
                    loc.first.click(timeout=3000)
                    done.append(sel)
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            page.keyboard.press("Escape")
            done.append("Escape")
        time.sleep(1.5)
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", default="transcripts/1min_answer.txt")
    ap.add_argument("--settle-s", type=int, default=210)
    args = ap.parse_args(argv)

    from playwright.sync_api import sync_playwright

    out = pathlib.Path(args.out)
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0]
        page = next((x for x in ctx.pages if "1min.ai" in x.url), None) or ctx.new_page()
        if "1min.ai" not in page.url:
            page.goto(URL, wait_until="domcontentloaded", timeout=40000)
            time.sleep(4)

        print("modals closed:", dismiss_modals(page))
        before = len(page.inner_text("body"))

        ta = page.locator("textarea").first
        ta.click(timeout=8000)
        ta.fill(args.prompt)
        print("filled:", len(ta.input_value()), "chars")

        sent = None
        for sel in ["button[aria-label*='send' i]", "button.send-btn", "[class*='send' i]",
                    "button[type='submit']"]:
            loc = page.locator(sel)
            for i in range(min(loc.count(), 8)):
                c = loc.nth(i)
                try:
                    bb = c.bounding_box()
                    if c.is_visible() and bb and bb["x"] > 900:
                        c.click(timeout=4000)
                        sent = sel
                        break
                except Exception:
                    continue
            if sent:
                break
        if not sent:
            ta.press("Enter")
            sent = "Enter"
        print("submitted via:", sent)

        t0, last, stable = time.time(), -1, 0
        while time.time() - t0 < args.settle_s:
            time.sleep(5)
            try:
                n = len(page.inner_text("body"))
            except Exception:
                continue
            if n == last:
                stable += 1
                if stable >= 3:
                    break
            else:
                stable, last = 0, n

        body = page.inner_text("body")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        print(f"elapsed {time.time() - t0:.0f}s | body {before} -> {len(body)} chars | saved {out}")
        print("--- tail ---")
        print(body[-1500:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
