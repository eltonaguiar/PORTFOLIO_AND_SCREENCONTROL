import json
res={}
try:
    from botasaurus.browser import browser, Driver
    @browser(headless=True, block_images=True)
    def run(driver: Driver, data):
        driver.get("data:text/html,<html><body><h1 id='h'>ok</h1></body></html>")
        el = driver.select("#h")
        txt = el.text if el else None
        return {"text": txt, "url": driver.current_url}
    res["runtime"]=run({"probe": 1})
except Exception as e:
    res["error"]=f"{type(e).__name__}: {str(e)[:250]}"
print(json.dumps(res,indent=2))
