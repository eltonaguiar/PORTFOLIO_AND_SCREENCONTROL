# Anti-detect scraping tools — measured capability report

**Run:** `2026-11-24T09:25Z` · **Agent:** GitHub Copilot (ghcopilot) · **Host:** Linux x86_64, Python 3.12.3
**Scope:** capability measurement only. **No protected third-party site was targeted.**

> Three of the ten tools in the brief were actually exercised: `curl_cffi`, `patchright`,
> `nodriver`, plus vanilla `playwright` as the control. The other six (`camoufox`,
> `CloakBrowser`, `SeleniumBase`, `botasaurus`, `browser-use`, `skyvern`) were **not** run —
> see "Not tested" for why. "Works" below means *the advertised low-level function executed*,
> not *guaranteed bypass*.

## Environment

| item | value |
|---|---|
| Python | 3.12.3, venv at `/tmp/scrapetest` |
| installed | `curl_cffi 0.17.0`, `nodriver 0.50.8`, `patchright`, `playwright` |
| browsers | `/usr/bin/google-chrome`, `/snap/bin/chromium`, `/usr/bin/firefox` |
| TLS probe target | `https://tls.browserleaks.com/json` (a service built for this) |
| flag probe target | `about:blank` / `data:text/html,<h1>probe</h1>` — no remote page |

**Environment gotcha:** `playwright.launch()` and `patchright.launch()` both fail out of the
box on this host, asking for `chromium_headless_shell-1255` / `-1248` which are not cached.
Both work with `channel="chrome"` (system binary). That is an environment fix, not a verdict
on either tool.

---

## Finding 1 — the "undetected" browsers still leak `HeadlessChrome` in the UA

| tool | `navigator.webdriver` | UA contains `Headless` |
|---|---|---|
| `playwright` (vanilla, headless) | **`True`** ← leaks | yes |
| `patchright` (headless) | `False` ✅ | **yes** ← still leaks |
| `patchright` + explicit `user_agent=` | `False` ✅ | **no** ✅ |
| `nodriver` (headless) | `False` ✅ | **yes** ← still leaks |

Fixing `navigator.webdriver` is necessary but **not sufficient**. A page that only checks
that flag sees a clean browser; a page that checks the UA substring `Headless` sees automation
immediately. **Two of the three "undetected" stacks leak on the second check by default**, and
one line closes it (`new_page(user_agent=...)`, verified).

Constant across all three headless runs — therefore *not* discriminating between the tools,
because all three drive the same Chrome binary: `plugins=5`, `languages=2`,
`typeof window.chrome === "object"`, WebGL vendor `Google Inc. (Google)`.

## Finding 2 — Chrome JA3 is *not* stable; JA4 is

Each profile was probed 3 consecutive times. Counts are unique values observed:

| impersonate | JA3 unique / 3 runs | JA4 unique | HTTP/2 unique | stable JA4 |
|---|---:|---:|---:|---|
| `chrome` | **3** | 1 | 1 | `t13d1517h2_8daaf6152771_cb7bf5808d99` |
| `chrome124` | **3** | 1 | 1 | `t13d1516h2_8daaf6152771_02713d6af862` |
| `chrome131` | **3** | 1 | 1 | `t13d1516h2_8daaf6152771_02713d6af862` |
| `safari` | 1 | 1 | 1 | `t13d2013h2_a09f3c656075_7f0f34a4126d` |
| `firefox133` | 1 | 1 | 1 | `t13d1716h2_5b57614c22b0_eeeea6562960` |

Baseline `stdlib urllib`: JA3 `46531b76d4d69e9c86d481cf71fa4933`, JA4
`t13d3113h1_e8f1e7e78f70_d339722ba4af`, HTTP/1.1 (no HTTP/2 hash).

Stable HTTP/2 (akamai) hashes — all Chrome profiles `52d84b11737d980aef856699f885ca86`;
safari `c52879e43202aeb92740be6e8c86ea96`; firefox133 `6ea73faa8fc5aac76bded7bd238f6433`.

**Correction to this report's own first draft.** An earlier version listed one JA3 per Chrome
profile as if it were a fixture. It was one run's value. Four separate runs produced four
different Chrome JA3 sets while Safari and Firefox returned byte-identical JA3 every time.
Consequences:

1. **A JA3 allowlist cannot reliably pin a Chrome impersonation** — the value moves per
   connection. A JA4 allowlist can, because JA4 was single-valued across every run.
2. **JA4 does not separate adjacent Chrome versions.** `chrome124` and `chrome131` share
   `t13d1516h2_8daaf6152771_02713d6af862` while `chrome` differs.
3. **HTTP/2 separates browser families, not versions** — all three Chrome profiles emit one
   hash, and Safari/Firefox each emit their own.

## What each lever actually buys

| lever | verified effect | blind to |
|---|---|---|
| `curl_cffi` impersonation | JA4 + HTTP/2 now match a real browser family; ~0.2 s, no browser | any JS challenge, cookie/JS-flow gate, per-SKU auth |
| `patchright` | `navigator.webdriver` false | UA `Headless` substring (until overridden), canvas/WebGL depth, behaviour |
| `nodriver` | `navigator.webdriver` false, no Selenium/WebDriver layer | UA `Headless` substring, same as above |

**Cheapest real win:** `curl_cffi` — no browser process, sub-second fetches, and a verifiably
browser-shaped handshake at the JA4/HTTP-2 layer. For JS-required pages, `patchright` closes
the flag the previous reports measured, **but you must also set `user_agent`.**

## Not tested, and why

`camoufox` and `CloakBrowser` ship modified browser binaries (large downloads, and a custom
Firefox build respectively). `SeleniumBase`, `botasaurus`, `browser-use` and `skyvern` need
either a driver stack, a model key (browser-use/skyvern are LLM/vision agents) or a heavy
vision dependency. None were installed, so **nothing here is a statement about their
performance.** They are catalogue entries only.

## Caveats

- Single machine, single egress IP. Fingerprint stability across IPs and networks was **not**
  tested; only run-to-run stability was.
- No real Cloudflare/Akamai challenge was attempted, deliberately. The question asked was
  "do these tools do what they claim", not "can I defeat someone's protection".
- `nodriver` leaves a closed event loop on teardown; `probe.py` tolerates it because all
  measurements are collected before teardown. Why note it: a silent teardown exception is
  how a probe ends up reporting an empty result as a finding.

## Reproduce

```bash
python3 -m venv /tmp/scrapetest && source /tmp/scrapetest/bin/activate
pip install curl_cffi nodriver playwright patchright
python3 probe.py tls      # Finding 2
python3 probe.py flags    # Finding 1
```

Raw captured output is in `runs/`; the structured numbers are in `measured.json`.
