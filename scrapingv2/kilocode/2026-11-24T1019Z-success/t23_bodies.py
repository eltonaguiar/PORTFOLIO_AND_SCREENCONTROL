import json, re, time
from curl_cffi import requests as creq
t={
 "walmart":"https://www.walmart.ca/en/search?q=playstation+5",
 "staples":"https://www.staples.ca/search?query=playstation+5",
 "memoryexpress":"https://www.memoryexpress.com/",
}
out={}
for name,u in t.items():
    r=creq.get(u, impersonate="chrome", timeout=30)
    b=r.text
    sig={
      "status":r.status_code,"bytes":len(b),
      "has_next_data":"__NEXT_DATA__" in b,
      "has_product_json":bool(re.search(r'"price"|"sku"|"productId"', b, re.I)),
      "has_ps5":"playstation 5" in b.lower() or "ps5" in b.lower(),
      "has_challenge":any(x in b.lower() for x in ["just a moment","verify you are human","cf-challenge","access denied","captcha"]) ,
      "cf_mitigated":r.headers.get("cf-mitigated"),
      "server":r.headers.get("server"),
      "title":(re.search(r"<title[^>]*>(.*?)</title>", b, re.S|re.I).group(1).strip()[:80] if re.search(r"<title",b,re.I) else None),
    }
    out[name]=sig
    time.sleep(3)
print(json.dumps(out,indent=2))
