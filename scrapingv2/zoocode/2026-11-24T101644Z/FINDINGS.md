# Anti-detect scraping tools: measured evaluation (zoocode)

Run 2026-11-24T10:16Z on a Linux host. Every line below was executed here. Nothing is quoted from a project README.

## Environment

| Tool | Version | Installed |
|---|---|---|
| curl_cffi | 0.16.3 | yes |
| scrapling | 0.4.15 | yes |
| patchright | (no `__version__`) | yes |
| playwright | (no `__version__`) | yes |
| browser_use | (no `__version__`) | yes |
| nodriver | 0.50.8 | installed into an isolated venv (`/tmp/scrapevenv`) because the system Python is PEP 668 managed |
| camoufox, CloakBrowser, SeleniumBase, botasaurus, skyvern | - | **not installed, not tested** |

## Target results

`https://www.gta5-mods.com/` is unprotected. `https://www.g2.com/` is protected.

| Tool | Target | Status | Measured detail |
|---|---|---|---|
| requests (control) | gta5-mods | 200 | 53,360 bytes, 0.5s |
| curl_cffi (`impersonate="chrome"`) | gta5-mods | 200 | 53,859 bytes, **0.2s** |
| requests (control) | g2 | 403 | blocked |
| curl_cffi (`impersonate="chrome"`) | g2 | 403 | **TLS impersonation alone did not bypass** |
| patchright (headless chromium) | g2 | 403 | `navigator.webdriver` = **False** |
| playwright (headless chromium) | g2 | 403 | `navigator.webdriver` = **True** |
| nodriver (headless chromium) | g2 | blocked | `navigator.webdriver` = **False**, but `document.body.innerText` was **empty** after 6s |

## What succeeded

1. **curl_cffi content extraction.** 131 links, correct title, 0.21s, no browser:
   `"GTA5-Mods.com - Your source for the latest GTA 5 car mods, scripts, tools and more."`
2. **patchright's stealth claim.** It reports `navigator.webdriver` as `False` where plain playwright reports `True`. That is a real, measured difference.
3. **nodriver's stealth claim.** Also `webdriver=False`, without Selenium or WebDriver.
4. **Scrapling's adaptive parser.** On a page whose CSS classes are randomised between loads:

```
v1: ['Product Alpha']
v2 adaptive : ['Product Alpha']
v2 plain    : []
```

   The plain selector found nothing on v2; adaptive mode relocated the element. This is the one listed claim that held up under a fair test.

## What did not succeed

- **No anti-bot block was bypassed.** g2.com returned 403 to requests, curl_cffi, patchright and playwright, and served an empty body to nodriver. Eliminating the webdriver leak was *not sufficient*.
- **browser_use could not be exercised.** Its browser launch hit a 30s watchdog timeout. I did not run an agent because that would spend API credits; only the free browser-session part was attempted.
- **camoufox, SeleniumBase, botasaurus and skyvern were untested** because they are not installed.

## Conclusion

For unprotected pages, `curl_cffi` is the best option measured here: fastest, no browser, real TLS fingerprint. For protected pages, nothing tested got through, so the claim that these tools bypass anti-bot defenses is **unsupported by this run**. The strongest measured capability is scrapling's adaptive selector, which is about surviving markup churn, not about passing bot checks.

## Reproduce

```bash
python3 -c 'from curl_cffi import requests as cr; r=cr.get("https://www.gta5-mods.com/", impersonate="chrome"); print(r.status_code, len(r.content))'
python3 /tmp/scr_adaptive.py          # scrapling adaptive vs plain
/tmp/scrapevenv/bin/python /tmp/nd_test.py   # nodriver
```
