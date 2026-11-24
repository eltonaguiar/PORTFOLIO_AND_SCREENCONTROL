# Cross-check vs `scrapingv2/ghcopilot` (2026-11-24T0925Z) — 10:16Z

Independent re-run of the two claims from the ghcopilot evaluation, on this host.

## Claim 1 — "undetected" browsers still send `HeadlessChrome` — **CONFIRMED**
| Tool | Default UA contains `Headless` | `navigator.webdriver` |
|---|---|---|
| patchright 1.63.0 | **yes** — `HeadlessChrome/153.0.8010.12` | false |
| patchright + explicit `user_agent` | **no** — `Chrome/157.0.0.0` | false |
| nodriver 0.50.99 | **yes** — `HeadlessChrome/157.0.0.0` | false |

Raw: `ua.out.json`. Closing `navigator.webdriver` is necessary, not sufficient.

## Claim 2 — Chrome JA3 is not stable across runs — **CONFIRMED**
Each profile probed 3× against `tls.browserleaks.com/json` (`stability.out.json`):

| Profile | unique JA3 / 3 runs | unique JA4 / 3 runs |
|---|---|---|
| chrome | **3** | 1 |
| chrome110 | **3** | 1 |
| chrome120 | **3** | **2** |
| chrome124 | **3** | 1 |
| safari17_0 | 1 | 1 |
| firefox133 | 1 | 1 |
| edge101 | 1 | 1 |

So: **JA3 is run-varying for Chrome**, stable for Safari/Firefox/Edge — matching ghcopilot.

## Refinement ghcopilot missed
They reported JA4 as "single-valued across every run". Here **chrome120 produced two
JA4 values in three runs**:
- `t13d1516h2_8daaf6152771_02713d6af862`
- `t13d1517h2_8daaf6152771_b1ff8ab2d16f`

So a JA4 allowlist is *more* stable than JA3 but **not guaranteed single-valued** —
pin the exact JA4 set observed, or expect occasional misses on ALPN/extension drift.
Also reproduced their version-collapse observation: chrome120/chrome124 share
`t13d1516h2_8daaf6152771_02713d6af862` (adjacent versions not separable by JA4).

## Impact on our `2026-11-24T1014Z` report
That report's JA3 table is a **single-run sample**, not a stable fixture. Treat the
JA3 column as illustrative only; use JA4 + HTTP/2 family for matching, and expect
Chrome JA3 drift. No other conclusion in that report changes.

## Artifacts
`stability.out.json`, `ua.out.json`, `t19_stability.py`, `t20_ua.py` (re-runnable).
