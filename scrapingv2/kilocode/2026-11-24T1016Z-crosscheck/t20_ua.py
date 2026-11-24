import json
res={}
try:
    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True)
        pg=b.new_page()
        res["patchright_default_ua"]=pg.evaluate("navigator.userAgent")
        pg2=b.new_page(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36")
        res["patchright_explicit_ua"]=pg2.evaluate("navigator.userAgent")
        res["patchright_explicit_webdriver"]=pg2.evaluate("navigator.webdriver")
        b.close()
except Exception as e:
    res["patchright_error"]=f"{type(e).__name__}: {str(e)[:150]}"
try:
    import asyncio, nodriver as uc
    async def m():
        b=await uc.start(headless=True, browser_args=["--no-sandbox"])
        try:
            pg=await b.get("data:text/html,<h1>x</h1>")
            return await pg.evaluate("navigator.userAgent")
        finally:
            b.stop()
    res["nodriver_ua"]=asyncio.run(m())
except Exception as e:
    res["nodriver_error"]=f"{type(e).__name__}: {str(e)[:150]}"
print(json.dumps(res,indent=2))
