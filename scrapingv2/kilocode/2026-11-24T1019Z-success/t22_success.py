import json, time
from curl_cffi import requests as creq
import requests as preq
skus={"xbox_s_512":"19422130","ps5_slim_1tb":"19446111"}
base=("https://www.bestbuy.ca/ecomm-api/availability/products?"
      "accept=application%2Fvnd.bestbuy.standardproduct.v1%2Bjson&accept-language=en-CA&skus=")
out={}
for name,sku in skus.items():
    for mode,fn in (("curl_cffi_chrome", lambda u: creq.get(u, impersonate="chrome", timeout=30,
                                                          headers={"Referer":"https://www.bestbuy.ca/"})),
                    ("plain_requests", lambda u: preq.get(u, timeout=30,
                                                          headers={"User-Agent":"python-requests/2.34"}))):
        try:
            r=fn(base+sku)
            rec={"status":r.status_code,"bytes":len(r.text)}
            try:
                j=r.json(); a=(j.get("availabilities") or [{}])[0]
                rec.update({"purchasable":a.get("purchasable"),
                            "status":a.get("status") or (a.get("shipping") or {}).get("status"),
                            "pickup":(a.get("pickup") or {}).get("status"),
                            "shipping":(a.get("shipping") or {}).get("status")})
            except Exception:
                rec["head"]=r.text[:120]
            out[f"{name}/{mode}"]=rec
        except Exception as e:
            out[f"{name}/{mode}"]={"error":f"{type(e).__name__}: {str(e)[:100]}"}
        time.sleep(1)
print(json.dumps(out,indent=2))
