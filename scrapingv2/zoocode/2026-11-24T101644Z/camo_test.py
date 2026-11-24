import time
from camoufox.sync_api import Camoufox

with Camoufox(headless=True, humanize=False) as browser:
    page = browser.new_page()
    t = time.time()
    r = page.goto("https://www.g2.com/", timeout=60000, wait_until="domcontentloaded")
    time.sleep(10)
    print("RESULT status :", r.status if r else None, f"{time.time()-t:.1f}s")
    print("RESULT title  :", repr(page.title()[:60]))
    print("RESULT text   :", repr(page.evaluate("document.body ? document.body.innerText.slice(0,140) : ''")))
    print("RESULT wd     :", page.evaluate("navigator.webdriver"))
    print("RESULT ua     :", page.evaluate("navigator.userAgent")[:70])
    print("RESULT cookies:", [c["name"] for c in page.context.cookies()])
