"""Sign in to a site with the Google session that already exists in the agent profile.

This is explicitly authorised by the user: click "Continue with Google", pick the existing account
tile, and let the site set its own session. It never types a password, a 2FA code or an email
address — if the flow asks for any of those, it stops and reports NEEDS_HUMAN.

Usage:
    python prototype/login_google.py --site chatplayground
    python prototype/login_google.py --site arena --site 1min
"""

from __future__ import annotations

import argparse
import re
import sys
import time

SITES = {
    "arena": "https://arena.ai/",
    "chatplayground": "https://web.chatplayground.ai/",
    "1min": "https://app.1min.ai/chat-with-ai",
}
ACCOUNT_HINT = "zerounderscore@gmail.com"
LOGIN_BUTTONS = ["Continue with Google", "Log in", "Log In", "Sign in", "Sign up for free", "Continue"]

#: anything that means "we are now being asked for a secret" — hard stop, never typed
SECRET_GATE = re.compile(
    r"(enter your password|enter the password|2-step verification|verify it'?s you|"
    r"type the text you hear|recaptcha challenge|passkey|use your phone to sign in)", re.I)


def find_page(ctx, host: str):
    for pg in ctx.pages:
        if host in pg.url:
            return pg
    return None


def click_first(page, texts: list[str], timeout_ms: int = 4000) -> str | None:
    for t in texts:
        try:
            loc = page.get_by_role("button", name=re.compile(re.escape(t), re.I)).first
            if loc.count() and loc.is_visible():
                loc.click(timeout=timeout_ms)
                return t
        except Exception:
            pass
        try:
            loc = page.get_by_text(t, exact=False).first
            if loc.count() and loc.is_visible():
                loc.click(timeout=timeout_ms)
                return t
        except Exception:
            pass
    return None


def body_text(page) -> str:
    try:
        return page.inner_text("body")
    except Exception:
        return ""


def signed_in(page, host: str) -> bool:
    url = page.url
    if "/login" in url or "accounts.google.com" in url:
        return False
    txt = body_text(page)
    if re.search(r"continue with google|sign up for free|log in\b", txt, re.I) and len(txt) < 1200:
        return False
    try:  # a composer is the strongest signal
        if page.locator("textarea, div[contenteditable='true']").count():
            return True
    except Exception:
        pass
    return host in url and not re.search(r"log ?in|sign ?in", txt[:600], re.I)


def login(page, want_account: str = ACCOUNT_HINT) -> dict:
    steps = []
    if signed_in(page, page.url.split("/")[2]):
        return {"verdict": "ALREADY_SIGNED_IN", "steps": steps, "url": page.url}

    hit = click_first(page, LOGIN_BUTTONS)
    steps.append(f"clicked {hit!r}" if hit else "no login button found")
    time.sleep(4)

    # the OAuth window may be a popup owned by the same context
    oauth = page
    for pg in page.context.pages:
        if "accounts.google.com" in pg.url:
            oauth = pg
            break
    steps.append(f"oauth page: {oauth.url[:60]}")

    if "accounts.google.com" in oauth.url:
        txt = body_text(oauth)
        if SECRET_GATE.search(txt):
            return {"verdict": "NEEDS_HUMAN", "reason": "google asked for a secret",
                    "steps": steps, "url": oauth.url}
        picked = None
        for sel in (f"[data-email='{want_account}']", f"text={want_account}", "text=Choose an account"):
            try:
                loc = oauth.locator(sel).first
                if loc.count() and loc.is_visible():
                    loc.click(); picked = sel; break
            except Exception:
                continue
        steps.append(f"picked account via {picked!r}" if picked else "no account tile found")
        time.sleep(5)
        if SECRET_GATE.search(body_text(oauth)):
            return {"verdict": "NEEDS_HUMAN", "reason": "secret requested after account pick",
                    "steps": steps, "url": oauth.url}

    time.sleep(3)
    ok = signed_in(page, page.url.split("/")[2])
    return {"verdict": "SIGNED_IN" if ok else "STILL_LOGGED_OUT", "steps": steps, "url": page.url}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", action="append", required=True, choices=list(SITES))
    ap.add_argument("--port", type=int, default=9222)
    args = ap.parse_args(argv)

    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{args.port}")
    ctx = browser.contexts[0]
    rc = 0
    try:
        for name in args.site:
            url = SITES[name]
            host = url.split("//")[1].split("/")[0]
            page = find_page(ctx, host) or ctx.new_page()
            if host not in page.url:
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(3)
            res = login(page)
            print(f"{name:15} {res['verdict']:18} {res.get('reason','')} | steps={res['steps']} | now={res['url'][:55]}")
            if res["verdict"] not in ("SIGNED_IN", "ALREADY_SIGNED_IN"):
                rc = 2
    finally:
        browser.close(); pw.stop()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
