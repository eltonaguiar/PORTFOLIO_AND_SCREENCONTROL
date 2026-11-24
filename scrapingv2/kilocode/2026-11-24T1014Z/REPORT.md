# Web-scraping tools — kilocode evaluation (2026-11-24T10:14Z)

Runtime tests on Linux, Python 3.12.3, system Chrome 157. No attempts against
Best Buy / Walmart / Cloudflare / Akamai pages. **Works = performs its advertised
low-level function**, not a guarantee of bypassing any site's protections.

## Verdict summary

| Tool | Version | Runtime result | Status |
|---|---|---|---|
| curl_cffi | 0.16.3 | 8 browser profiles with distinct JA3; httpbin JSON status 200 | **WORKS** |
| scrapling | 0.4.15 | basic parse='In Stock'; adaptive after class change='<span class="qq17">In Stock</span>' | **WORKS** |
| patchright | 1.63.0 | render='ok' (bundled); navigator.webdriver=False; plugins=0 | **WORKS** |
| nodriver | 0.50.99 | render='ok'; navigator.webdriver=False; plugins=5 | **WORKS** |
| seleniumbase | 4.58.4 | UC mode headless render='ok'; chromedriver 157 downloaded | **WORKS** |
| botasaurus | 4.0.97 | headless render='ok' | **WORKS** |
| camoufox | 0.5.9 | package imports; patched Firefox not downloaded (large) | INSTALLED ONLY |
| cloakbrowser | 0.7.3 on PyPI | available; modified Chromium binary not fetched | AVAILABLE ONLY |
| browser-use | 0.12.7 | installed; needs an LLM API key, not run | NOT RUN |
| skyvern | 1.0.58 on PyPI | available; vision stack needs model/API setup, not run | NOT RUN |

## TLS evidence (curl_cffi)

| Profile | JA3 | JA4 |
|---|---|---|
| chrome | `c5cd3e5ef679c9842aec4c708db3bcd3` | `t13d1516h2_8daaf6152771_806a8c22fdea` |
| chrome110 | `637e72e70b4e35493c834625a848c54e` | `t13d1516h2_8daaf6152771_e5627efa2ab1` |
| chrome120 | `5ca7558f4d5aac6dc0700a1e92410b7c` | `t13d1516h2_8daaf6152771_02713d6af862` |
| chrome124 | `bdcacdf5f60b157c59e8be1483d57ea4` | `t13d1516h2_8daaf6152771_02713d6af862` |
| safari17_0 | `773906b0efdefa24a7f2b8eb6985bf37` | `t13d2014h2_a09f3c656075_14788d8d241b` |
| safari17_2_ios | `773906b0efdefa24a7f2b8eb6985bf37` | `t13d2014h2_a09f3c656075_14788d8d241b` |
| firefox133 | `2d692a4485ca2f5f2b10ecb2d2909ad3` | `t13d1716h2_5b57614c22b0_eeeea6562960` |
| edge101 | `cd08e31494f9531f560d64c695473da9` | `t13d1516h2_8daaf6152771_e5627efa2ab1` |

Plain `requests` (earlier run): JA3 `0149f47eabf9a20d0893e2a44e5a6323`, JA4
`t13d3112h1_…` (HTTP/1.1). Impersonation is a real, measurable change.

## Honest failures / limits
- Scrapling adaptive mode is **silently ignored** unless `Adaptor(..., adaptive=True)`;
  the naive attempt returned `null` with only a warning (captured in
  `t4_t5_scrapling.out.json`).
- nodriver prints `RuntimeError: Event loop is closed` on teardown (cosmetic; result valid).
- botasaurus `Driver` has **no `execute_script`**; use `select`/`run_js` (first attempt failed).
- patchright/nodriver UAs still report `HeadlessChrome/…`; `navigator.webdriver=false`
  alone is not anonymity.
- SeleniumBase/botasaurus download drivers/binaries; pin versions for reproducibility.
- No test proves these defeat any specific retailer's protection. Capability != bypass.

## Legal / licensing
- AGPL-3.0: nodriver, skyvern (network use -> source disclosure obligations).
- MPL-2.0: camoufox. Apache-2.0: patchright. MIT/BSD-3: the rest.
- Retailer ToS and local law still apply.

## Artifacts
- `results.json` — consolidated output. `versions.json` — exact versions.
- `t*_*.out.json` / `t*_*.err` — raw stdout/stderr. `t*_*.py` — re-runnable scripts.

