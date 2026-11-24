import json, sys
from patchright.sync_api import sync_playwright
mode = sys.argv[1] == "headful"
res={"mode":sys.argv[1]}
try:
    with sync_playwright() as p:
        b=p.chromium.launch(headless=not mode)
        ctx=b.new_context()
        pg=ctx.new_page()
        r=pg.goto("https://www.g2.com/", wait_until="domcontentloaded", timeout=45000)
        res.update({"status": r.status if r else None,
                    "title": pg.title(),"bytes": len(pg.content()),
                    "ua": pg.evaluate("navigator.userAgent"),
                    "webdriver": pg.evaluate("navigator.webdriver")})
        b.close()
except Exception as e:
    res["error"]=f"{type(e).__name__}: {str(e)[:200]}"
print(json.dumps(res))
