#!/usr/bin/env python3
"""Reproduce the measurements in REPORT.md.

Usage:
    python3 probe.py tls     # TLS/JA3/JA4/HTTP2 per curl_cffi impersonation
    python3 probe.py flags   # navigator.webdriver + user-agent per headless tool

Setup:
    python3 -m venv /tmp/scrapetest && source /tmp/scrapetest/bin/activate
    pip install curl_cffi nodriver playwright patchright

Notes
    - playwright/patchright are launched with channel="chrome" because the default
      launch asks for headless-shell builds that may not be cached on this host.
    - Nothing here targets a protected third-party site. TLS fingerprints come from
      tls.browserleaks.com (built for this) and browser flags are read from data: URLs.
"""
import json
import sys

TLS_URL = "https://tls.browserleaks.com/json"
PROFILES = ["chrome", "chrome124", "chrome131", "safari", "safari17_0", "firefox133"]

FLAG_JS = """() => ({
  webdriver: navigator.webdriver,
  ua: navigator.userAgent,
  plugins: navigator.plugins.length,
  langs: (navigator.languages||[]).length,
  chrome_obj: typeof window.chrome,
  webgl_vendor: (() => { try {
      const c=document.createElement('canvas').getContext('webgl');
      const d=c.getExtension('WEBGL_debug_renderer_info');
      return c.getParameter(d.UNMASKED_VENDOR_WEBGL);
    } catch(e){ return 'ERR'; } })()
})"""


def probe_tls():
    import urllib.request
    from curl_cffi import requests as cr

    rows = []
    try:
        r = urllib.request.urlopen(TLS_URL, timeout=20)
        d = json.loads(r.read())
        rows.append({"client": "stdlib urllib (baseline)",
                     "ja3": d.get("ja3_hash"), "ja4": d.get("ja4"), "http2": None})
    except Exception as e:
        rows.append({"client": "stdlib urllib (baseline)", "error": str(e)})

    for imp in PROFILES:
        try:
            d = cr.get(TLS_URL, impersonate=imp, timeout=25).json()
            rows.append({"client": f"curl_cffi impersonate={imp}",
                         "ja3": d.get("ja3_hash"), "ja4": d.get("ja4"),
                         "http2": d.get("akamai_hash")})
        except Exception as e:
            rows.append({"client": f"curl_cffi impersonate={imp}", "error": str(e)})

    w = max(len(r["client"]) for r in rows)
    print(f"  {'client':{w}}  {'JA3':34}  {'JA4':46}  HTTP2")
    for r in rows:
        print(f"  {r['client']:{w}}  {str(r.get('ja3')):34}  {str(r.get('ja4')):46}  {r.get('http2')}")


def probe_flags():
    out = []

    def run_pw(name, module, ua=None):
        mod = __import__(f"{module}.sync_api", fromlist=["sync_playwright"])
        with mod.sync_playwright() as p:
            b = p.chromium.launch(headless=True, channel="chrome")
            pg = b.new_page(**({"user_agent": ua} if ua else {}))
            pg.goto("data:text/html,<h1>probe</h1>")
            d = pg.evaluate(FLAG_JS)
            d["tool"] = name
            d["ua_leaks_headless"] = "Headless" in d["ua"]
            out.append(d)
            b.close()

    run_pw("playwright", "playwright")
    run_pw("patchright", "patchright")
    run_pw("patchright+explicit_user_agent", "patchright",
           ua=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36"))

    import asyncio
    import nodriver as uc

    async def nd():
        b = await uc.start(headless=True, browser_args=["--no-sandbox", "--disable-gpu"])
        pg = await b.get("data:text/html,<h1>probe</h1>")
        await pg.sleep(1.5)
        res = {"tool": "nodriver"}
        for expr, key in (("navigator.webdriver", "webdriver"),
                          ("navigator.userAgent", "ua"),
                          ("navigator.plugins.length", "plugins"),
                          ("typeof window.chrome", "chrome_obj")):
            try:
                res[key] = await pg.evaluate(expr)
            except Exception as e:
                res[key] = f"ERR {type(e).__name__}"
        res["ua_leaks_headless"] = "Headless" in str(res.get("ua"))
        out.append(res)
        try:
            b.stop()
        except Exception:
            pass

    # nodriver leaves a closed event loop behind on teardown; the measurements are
    # already collected by this point, so a teardown-only RuntimeError is noise.
    try:
        asyncio.run(nd())
    except RuntimeError as e:
        if "Event loop is closed" not in str(e):
            raise

    print(f"  {'tool':32}  {'webdriver':9}  {'UA leaks Headless':17}  UA")
    for r in out:
        print(f"  {r['tool']:32}  {str(r.get('webdriver')):9}  "
              f"{str(r.get('ua_leaks_headless')):17}  {r.get('ua')}")

    print("\n  KEY: patchright and nodriver both clear navigator.webdriver, but only an")
    print("  explicit user_agent removes the 'HeadlessChrome' substring.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "flags"
    {"tls": probe_tls, "flags": probe_flags}.get(mode, probe_flags)()
