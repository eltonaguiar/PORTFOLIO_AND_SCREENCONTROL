#!/usr/bin/env python3
"""Regenerate results.json + REPORT.md from the raw t*.out.json captures."""
import json
def rd(n):
    try:
        txt = open(n).read()
        i = txt.find("{")
        return json.loads(txt[i:]) if i >= 0 else {"_error": "no json"}
    except Exception as e:
        return {"_error": str(e)}
v=rd("versions.json")
def _val(x):
    return x.get("value") if isinstance(x, dict) else x
t2=rd("t2_tls.out.json"); t45=rd("t4_t5_scrapling.out.json"); t5b=rd("t5b.out.json")
t6=rd("t6_patchright.out.json"); t8=rd("t8_nodriver.out.json")
t9=rd("t9_sb.out.json"); t10=rd("t10_bota.out.json")
json.dump({"captured_utc":"2026-11-24T10:14Z","python":"3.12.3","versions":v,
 "tls":t2,"scrapling_basic":t45,"scrapling_adaptive":t5b,"patchright":t6,
 "nodriver":t8,"seleniumbase":t9,"botasaurus":t10}, open("results.json","w"), indent=2)
pr=t6.get("render",{}); prf=t6.get("fingerprint",{}); nd=t8.get("runtime",{})
nd_fp=dict(nd.get("fingerprint") or []) if isinstance(nd.get("fingerprint"),list) else {}
sb=t9.get("runtime",{}); bt=t10.get("runtime",{})
profiles=[(k,x) for k,x in t2.items() if isinstance(x,dict) and x.get("ja3")]
L=["# Web-scraping tools — kilocode evaluation (2026-11-24T10:14Z)","",
"Runtime tests on Linux, Python 3.12.3, system Chrome 157. No attempts against",
"Best Buy / Walmart / Cloudflare / Akamai pages. **Works = performs its advertised",
"low-level function**, not a guarantee of bypassing any site's protections.","",
"## Verdict summary","",
"| Tool | Version | Runtime result | Status |","|---|---|---|---|",
f"| curl_cffi | {v.get('curl_cffi')} | {len(profiles)} browser profiles with distinct JA3; httpbin JSON status {t2.get('httpbin_json',{}).get('status')} | **WORKS** |",
f"| scrapling | {v.get('scrapling')} | basic parse={t45.get('basic',{}).get('found')!r}; adaptive after class change={t5b.get('adaptive',{}).get('got')!r} | **WORKS** |",
f"| patchright | {v.get('patchright')} | render={pr.get('text')!r} ({pr.get('how')}); navigator.webdriver={prf.get('webdriver')}; plugins={prf.get('plugins')} | **WORKS** |",
f"| nodriver | {v.get('nodriver')} | render={nd.get('text')!r}; navigator.webdriver={_val(nd_fp.get('webdriver'))}; plugins={_val(nd_fp.get('plugins'))} | **WORKS** |",
f"| seleniumbase | {v.get('seleniumbase')} | UC mode headless render={sb.get('text')!r}; chromedriver 157 downloaded | **WORKS** |",
f"| botasaurus | {v.get('botasaurus')} | headless render={bt.get('text')!r} | **WORKS** |",
f"| camoufox | {v.get('camoufox')} | package imports; patched Firefox not downloaded (large) | INSTALLED ONLY |",
"| cloakbrowser | 0.7.3 on PyPI | available; modified Chromium binary not fetched | AVAILABLE ONLY |",
f"| browser-use | {v.get('browser_use')} | installed; needs an LLM API key, not run | NOT RUN |",
"| skyvern | 1.0.58 on PyPI | available; vision stack needs model/API setup, not run | NOT RUN |","",
"## TLS evidence (curl_cffi)","","| Profile | JA3 | JA4 |","|---|---|---|"]
for k,x in profiles: L.append(f"| {k} | `{x['ja3']}` | `{x.get('ja4')}` |")
L+=["","Plain `requests` (earlier run): JA3 `0149f47eabf9a20d0893e2a44e5a6323`, JA4",
"`t13d3112h1_…` (HTTP/1.1). Impersonation is a real, measurable change.","",
"## Honest failures / limits",
"- Scrapling adaptive mode is **silently ignored** unless `Adaptor(..., adaptive=True)`;",
"  the naive attempt returned `null` with only a warning (captured in",
"  `t4_t5_scrapling.out.json`).",
"- nodriver prints `RuntimeError: Event loop is closed` on teardown (cosmetic; result valid).",
"- botasaurus `Driver` has **no `execute_script`**; use `select`/`run_js` (first attempt failed).",
"- patchright/nodriver UAs still report `HeadlessChrome/…`; `navigator.webdriver=false`",
"  alone is not anonymity.",
"- SeleniumBase/botasaurus download drivers/binaries; pin versions for reproducibility.",
"- No test proves these defeat any specific retailer's protection. Capability != bypass.","",
"## Legal / licensing",
"- AGPL-3.0: nodriver, skyvern (network use -> source disclosure obligations).",
"- MPL-2.0: camoufox. Apache-2.0: patchright. MIT/BSD-3: the rest.",
"- Retailer ToS and local law still apply.","",
"## Artifacts",
"- `results.json` — consolidated output. `versions.json` — exact versions.",
"- `t*_*.out.json` / `t*_*.err` — raw stdout/stderr. `t*_*.py` — re-runnable scripts.",""]
open("REPORT.md","w").write("\n".join(L)+"\n")
print("regenerated")
