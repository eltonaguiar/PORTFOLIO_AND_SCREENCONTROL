import json
from scrapling.parser import Adaptor
A='<html><body><div class="card x9f2"><h2 id="t">Xbox Series X</h2><span class="a73k">In Stock</span></div></body></html>'
B='<html><body><div class="card zz91"><h2 id="t">Xbox Series X</h2><span class="qq17">In Stock</span></div></body></html>'
res={}
try:
    pa=Adaptor(A, adaptive=True)
    got=pa.css("span.a73k::text", identifier="stock", auto_save=True).get()
    res["save"]={"got":got}
    pb=Adaptor(B, adaptive=True)
    adapt=pb.css("span.a73k::text", identifier="stock", adaptive=True).get()
    res["adaptive"]={"got":adapt,"match":bool(adapt and "In Stock" in str(adapt))}
except Exception as e:
    res["error"]=f"{type(e).__name__}: {e}"
print(json.dumps(res,indent=2))
