import re, random
random.seed(11)
cls = lambda: "c" + "".join(random.choice("abcdef0123456789") for _ in range(6))
def page(prices):
    rows = "".join(f'<div class="{cls()}"><h2>Product {n}</h2><span class="{cls()}">{p}</span></div>'
                   for n, p in prices)
    return f"<html><body>{rows}</body></html>"
v1 = page([("Alpha","$19.99"),("Beta","$29.99"),("Gamma","$39.99")])
v2 = page([("Alpha","$21.50"),("Beta","$31.50"),("Gamma","$41.50")])

from scrapling.parser import Adaptor
first_cls = re.search(r'class="(c[0-9a-f]{6})"', v1).group(1)
sel = f".{first_cls} h2"

p1 = Adaptor(v1, url="https://example.test/", adaptive=True)
got1 = p1.css(sel, auto_save=True)
print("v1:", [e.text for e in got1])

p2 = Adaptor(v2, url="https://example.test/", adaptive=True)
print("v2 adaptive :", [e.text for e in p2.css(sel, adaptive=True)])
print("v2 plain    :", [e.text for e in p2.css(sel)])
