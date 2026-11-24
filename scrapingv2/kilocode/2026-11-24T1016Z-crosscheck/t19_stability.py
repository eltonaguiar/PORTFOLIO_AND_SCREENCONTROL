import json
from curl_cffi import requests as creq
profiles=["chrome","chrome110","chrome120","chrome124","safari17_0","firefox133","edge101"]
res={}
for imp in profiles:
    ja3=set(); ja4=set(); errs=[]
    for i in range(3):
        try:
            r=creq.get("https://tls.browserleaks.com/json", impersonate=imp, timeout=25)
            j=r.json()
            if j.get("ja3_hash"): ja3.add(j["ja3_hash"])
            if j.get("ja4"): ja4.add(j["ja4"])
        except Exception as e:
            errs.append(f"{type(e).__name__}: {str(e)[:60]}")
    res[imp]={"ja3_unique":sorted(ja3),"ja3_n":len(ja3),
              "ja4_unique":sorted(ja4),"ja4_n":len(ja4),"errors":errs}
print(json.dumps(res,indent=2))
