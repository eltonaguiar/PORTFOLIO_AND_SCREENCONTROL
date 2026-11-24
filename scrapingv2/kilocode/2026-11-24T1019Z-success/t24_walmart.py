import json, re
from curl_cffi import requests as creq
r=creq.get("https://www.walmart.ca/en/search?q=playstation+5", impersonate="chrome", timeout=30)
b=r.text
m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', b, re.S)
out={"status":r.status_code,"bytes":len(b),"next_data":bool(m)}
if m:
    try:
        d=json.loads(m.group(1))
        out["top_keys"]=list(d.keys())[:8]
        def walk(o,path="",hits=None):
            hits=hits if hits is not None else []
            if isinstance(o,dict):
                for k,v in o.items():
                    if k in ("name","productName","title") and isinstance(v,str) and len(v)<120:
                        hits.append((path+"/"+k,v))
                    walk(v,path+"/"+k,hits)
            elif isinstance(o,list):
                for i,v in enumerate(o[:5]): walk(v,path+f"[{i}]",hits)
            return hits
        hits=walk(d)
        out["name_like_count"]=len(hits)
        out["samples"]=[h for h in hits if any(x in h[1].lower() for x in ("playstation","ps5","console"))][:5]
        s=json.dumps(d)
        out["has_price_fields"]=bool(re.search(r'"(price|currentPrice|priceInfo)"', s))
    except Exception as e:
        out["parse_error"]=f"{type(e).__name__}: {str(e)[:120]}"
print(json.dumps(out,indent=2))
