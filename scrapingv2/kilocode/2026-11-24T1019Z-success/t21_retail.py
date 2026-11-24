import json, time
from curl_cffi import requests as creq
targets={
 "canada_computers":"https://www.canadacomputers.com/en/xbox/184244/microsoft-xbox-series-x-1tb-black-rrt-00001.html",
 "bestbuy_product":"https://www.bestbuy.ca/en-ca/product/xbox-series-s-512gb-console/19422130",
 "walmart_search":"https://www.walmart.ca/en/search?q=playstation+5",
 "staples_search":"https://www.staples.ca/search?query=playstation+5",
 "memoryexpress":"https://www.memoryexpress.com/",
}
out={}
for name,url in targets.items():
    t=time.time()
    try:
        r=creq.get(url, impersonate="chrome", timeout=30, allow_redirects=True)
        body=r.text
        low=body.lower()
        markers=[m for m in ["access denied","cloudflare","captcha","just a moment","verify you are human","forbidden","bot"] if m in low]
        out[name]={"status":r.status_code,"final_url":str(r.url)[:110],"bytes":len(body),
                   "title":(r.text.split("<title>")[1].split("</title>")[0][:90] if "<title>" in body else None),
                   "markers":markers,"secs":round(time.time()-t,2)}
    except Exception as e:
        out[name]={"error":f"{type(e).__name__}: {str(e)[:120]}","secs":round(time.time()-t,2)}
    time.sleep(4)
# Best Buy public availability API (per-SKU JSON used by the tracker)
try:
    api=("https://www.bestbuy.ca/ecomm-api/availability/products?accept=application%2Fvnd.bestbuy.standardproduct.v1%2Bjson"
         "&accept-language=en-CA&skus=19422130")
    r=creq.get(api, impersonate="chrome", timeout=30,
               headers={"Referer":"https://www.bestbuy.ca/"})
    out["bestbuy_availability_api"]={"status":r.status_code,"bytes":len(r.text),"head":r.text[:300]}
except Exception as e:
    out["bestbuy_availability_api"]={"error":f"{type(e).__name__}: {str(e)[:120]}"}
print(json.dumps(out,indent=2))
