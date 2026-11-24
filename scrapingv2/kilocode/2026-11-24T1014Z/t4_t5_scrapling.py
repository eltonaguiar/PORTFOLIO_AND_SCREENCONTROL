import json
from scrapling.parser import Adaptor
res={}
A='<html><body><div class="card x9f2"><h2 id="t">Xbox Series X</h2><span class="a73k">In Stock</span></div></body></html>'
B='<html><body><div class="card zz91"><h2 id="t">Xbox Series X</h2><span class="qq17">In Stock</span></div></body></html>'
try:
    pa=Adaptor(A)
    exact=pa.css("span.a73k::text", identifier="stock", auto_save=True).get()
    res["basic"]={"found":exact,"text":pa.get_all_text()[:80]}
except Exception as e:
    res["basic"]={"error":f"{type(e).__name__}: {e}"}
try:
    pb=Adaptor(B)
    adapt=pb.css("span.a73k::text", identifier="stock", adaptive=True).get()
    res["adaptive_after_class_change"]={"found":adapt,"expected":"In Stock","match":bool(adapt and "In Stock" in str(adapt))}
except Exception as e:
    res["adaptive_after_class_change"]={"error":f"{type(e).__name__}: {e}"}
try:
    pb2=Adaptor(B)
    sim=pb2.find_similar(pa.css("span.a73k")[0])
    res["find_similar"]={"n":len(sim) if sim else 0,"text":(sim[0].text if sim else None)}
except Exception as e:
    res["find_similar"]={"error":f"{type(e).__name__}: {e}"}
print(json.dumps(res,indent=2))
