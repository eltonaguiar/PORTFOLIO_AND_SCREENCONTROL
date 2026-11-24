import asyncio, json
async def main():
    res={}
    try:
        import nodriver as uc
        b=await uc.start(headless=True, browser_args=["--no-sandbox"])
        try:
            pg=await b.get("data:text/html,<html><body><h1 id='h'>ok</h1></body></html>")
            txt=await pg.evaluate("document.querySelector('#h').innerText")
            fp=await pg.evaluate("({webdriver: navigator.webdriver, ua: navigator.userAgent, plugins: navigator.plugins.length})")
            res["runtime"]={"text":txt,"fingerprint":fp}
        finally:
            b.stop()
    except Exception as e:
        res["error"]=f"{type(e).__name__}: {str(e)[:300]}"
    print(json.dumps(res,indent=2))
asyncio.run(main())
