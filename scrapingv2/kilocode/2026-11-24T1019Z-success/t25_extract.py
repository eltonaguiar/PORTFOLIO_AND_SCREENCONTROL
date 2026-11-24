import json, re
from curl_cffi import requests as creq
r=creq.get("https://www.walmart.ca/en/search?q=playstation+5", impersonate="chrome", timeout=30)
m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
d=json.loads(m.group(1))
items=d["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][0].get("items",[])
rows=[]
for it in items:
    rows.append({"name":it.get("name"),"price":it.get("price"),"priceInfo":it.get("priceInfo"),
                 "canonicalUrl":it.get("canonicalUrl"),"availabilityStatus":it.get("availabilityStatus")})
print(json.dumps({"n_items":len(items),"samples":rows[:5]},indent=2)[:2500])
