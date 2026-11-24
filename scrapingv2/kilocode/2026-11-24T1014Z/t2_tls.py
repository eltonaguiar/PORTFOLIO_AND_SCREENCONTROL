import json
from curl_cffi import requests as creq
res={}
imps=["chrome","chrome110","chrome120","chrome124","safari17_0","safari17_2_ios","firefox133","edge101"]
for imp in imps:
    try:
        r=creq.get("https://tls.browserleaks.com/json", impersonate=imp, timeout=25)
        j=r.json()
        res[imp]={"status":r.status_code,"ja3":j.get("ja3_hash"),"ja4":j.get("ja4"),
                  "http":getattr(r,"http_version",None),"ua":(j.get("user_agent") or "")[:60]}
    except Exception as e:
        res[imp]={"error":f"{type(e).__name__}: {str(e)[:90]}"}
try:
    r=creq.get("https://httpbin.org/get", impersonate="chrome", timeout=25)
    j=r.json() if "json" in (r.headers.get("content-type") or "") else {}
    res["httpbin_json"]={"status":r.status_code,"http":getattr(r,"http_version",None),"origin":j.get("origin"),"ua":(j.get("headers",{}).get("User-Agent") or "")[:60]}
except Exception as e:
    res["httpbin_json"]={"error":f"{type(e).__name__}: {str(e)[:90]}"}
print(json.dumps(res,indent=2))
