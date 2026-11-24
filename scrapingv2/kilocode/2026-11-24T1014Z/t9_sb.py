import json
res={}
try:
    from seleniumbase import SB
    for kw in ({"uc": True, "headless": True}, {"uc": True, "headless2": True}, {"headless": True}):
        try:
            with SB(binary_location="/usr/bin/google-chrome", **kw) as sb:
                sb.open("data:text/html,<html><body><h1 id='h'>ok</h1></body></html>")
                res["runtime"]={"kwargs":list(kw),"text":sb.get_text("#h")}
            break
        except Exception as e:
            res.setdefault("attempts",[]).append({"kwargs":list(kw),"error":f"{type(e).__name__}: {str(e)[:160]}"})
except Exception as e:
    res["import_error"]=f"{type(e).__name__}: {str(e)[:200]}"
print(json.dumps(res,indent=2))
