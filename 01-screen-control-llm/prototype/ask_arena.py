"""Ask one prompt on arena.ai over CDP in Agent mode, then save the transcript.

Surface notes measured on this build (Chrome 157, 2026-11-22):
  * the Chat/Agent switch is a native `<select>`: values `chat` | `work` ("Agent")
  * the composer is `div[contenteditable='true'].tiptap.ProseMirror` — `fill()` does nothing;
    `keyboard.insert_text()` writes intact, while `keyboard.type(delay=8)` DROPS characters
  * a Terms-of-Use modal can intercept the first submit; `--accept-tos` clicks it once and logs it
  * anonymous use is allowed on some prompts; when a sign-in wall appears the script reports it
    instead of guessing
"""

from __future__ import annotations

import argparse
import pathlib
import time


def dismiss_tos(page) -> str:
    for label in ("Agree", "I agree", "Accept", "Accept all"):
        try:
            loc = page.get_by_role("button", name=label).first
            if loc.count() and loc.is_visible():
                loc.click(timeout=3000)
                return f"clicked {label!r}"
        except Exception:
            pass
        try:
            loc = page.get_by_text(label, exact=True).first
            if loc.count() and loc.is_visible():
                loc.click(timeout=3000)
                return f"clicked text {label!r}"
        except Exception:
            pass
    return "no ToS control"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--mode", default="work", choices=["chat", "work"])
    ap.add_argument("--accept-tos", action="store_true")
    ap.add_argument("--out", default="transcripts/arena_answer.txt")
    ap.add_argument("--settle-s", type=int, default=300)
    args = ap.parse_args(argv)

    from playwright.sync_api import sync_playwright

    out = pathlib.Path(args.out)
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0]
        page = next((x for x in ctx.pages if "arena.ai" in x.url), None) or ctx.new_page()
        if "arena.ai" not in page.url:
            page.goto("https://arena.ai/", wait_until="domcontentloaded", timeout=40000)
            time.sleep(4)

        try:
            page.select_option("select", args.mode)
            print("mode:", page.eval_on_selector("select", "s=>s.value"))
        except Exception as exc:
            print("mode switch failed:", type(exc).__name__)

        editor = page.locator("div[contenteditable='true']").first
        editor.click(timeout=8000)
        page.keyboard.insert_text(args.prompt)          # intact; type() loses characters
        print("typed chars:", len(editor.inner_text()))
        page.keyboard.press("Enter")
        print("submitted")

        if args.accept_tos:
            time.sleep(3)
            print("tos:", dismiss_tos(page))

        before = len(page.inner_text("body"))
        t0, last, stable = time.time(), -1, 0
        while time.time() - t0 < args.settle_s:
            time.sleep(5)
            try:
                n = len(page.inner_text("body"))
            except Exception:
                continue
            if n == last:
                stable += 1
                if stable >= 4:
                    break
            else:
                stable, last = 0, n

        body = page.inner_text("body")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        print(f"elapsed {time.time() - t0:.0f}s | body {before} -> {len(body)} | saved {out}")
        print("--- tail ---")
        print(body[-1500:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
