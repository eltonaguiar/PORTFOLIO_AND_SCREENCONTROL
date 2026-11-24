import json, traceback
res={}
try:
    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            b=p.chromium.launch(headless=True)
            how="bundled"
        except Exception as e1:
            b=p.chromium.launch(headless=True, channel="chrome")
            how="channel:chrome"
        pg=b.new_page()
        pg.set_content("<html><body><h1 id='h'>ok</h1></body></html>")
        res["render"]={"how":how,"text":pg.inner_text("#h")}
        res["fingerprint"]=pg.evaluate("() => ({webdriver: navigator.webdriver, ua: navigator.userAgent, langs: navigator.languages.length, plugins: navigator.plugins.length})")
        b.close()
except Exception as e:
    res["error"]=f"{type(e).__name__}: {str(e)[:300]}"
print(json.dumps(res,indent=2))
