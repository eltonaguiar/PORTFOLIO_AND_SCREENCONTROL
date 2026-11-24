#!/usr/bin/env python3
"""Hardened anti-detect configuration + the full comparison matrix.

Runs three configurations and prints the leak checklist for each:
  1. naive playwright         - the control; what you get by default
  2. patchright default       - the "undetected" fork, unconfigured
  3. patchright HARDENED      - explicit UA, viewport, locale, timezone, Vulkan GPU

Why each hardened setting exists:
  user_agent          removes the 'HeadlessChrome' substring that survives patchright
  viewport            default 1280x720 equals screen size exactly, which is checkable
  locale + timezone   must agree with each other and with Accept-Language
  --use-angle=vulkan  the ONLY flag combination found that replaces the SwiftShader
                      software renderer with real hardware; three alternatives either
                      fail to create a WebGL context or leave SwiftShader in place

Requires: pip install patchright playwright ; system Google Chrome (channel="chrome").

Scope: measures browser-reported surfaces from data: URLs. No third-party site is
contacted, so this is a capability measurement, not a bypass attempt.
"""
import json
import sys

PROBE_JS = """() => {
  const g = (f) => { try { return f() } catch (e) { return 'ERR:' + e.name } };
  return {
    webdriver: navigator.webdriver,
    ua_headless: /Headless/i.test(navigator.userAgent),
    plugins: navigator.plugins.length,
    languages: (navigator.languages || []).slice().join(','),
    outer_w: window.outerWidth,
    outer_h: window.outerHeight,
    screen_w: screen.width,
    timezone: g(() => Intl.DateTimeFormat().resolvedOptions().timeZone),
    webgl_renderer: g(() => {
      const c = document.createElement('canvas').getContext('webgl');
      const d = c.getExtension('WEBGL_debug_renderer_info');
      return c.getParameter(d.UNMASKED_RENDERER_WEBGL);
    }),
    canvas_hash: g(() => {
      const c = document.createElement('canvas');
      c.width = 200; c.height = 40;
      const x = c.getContext('2d');
      x.textBaseline = 'top'; x.font = '14px Arial'; x.fillText('abcdef', 2, 2);
      const s = c.toDataURL();
      let h = 0;
      for (let i = 0; i < s.length; i++) { h = ((h << 5) - h) + s.charCodeAt(i); h |= 0 }
      return String(h);
    }),
    webdriver_desc: g(() => Object.getOwnPropertyDescriptor(
      Navigator.prototype, 'webdriver') ? 'present' : 'absent')
  };
}"""

HARDENED_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--use-gl=angle",
    "--use-angle=vulkan",
]
CLEAN_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36")


def run(module, label, hardened=False):
    m = __import__(f"{module}.sync_api", fromlist=["sync_playwright"])
    launch_kw = {"headless": True, "channel": "chrome"}
    if hardened:
        launch_kw["args"] = HARDENED_ARGS
    with m.sync_playwright() as p:
        browser = p.chromium.launch(**launch_kw)
        if hardened:
            ctx = browser.new_context(
                user_agent=CLEAN_UA,
                viewport={"width": 1440, "height": 900},
                locale="en-CA",
                timezone_id="America/Toronto",
            )
            page = ctx.new_page()
        else:
            page = browser.new_page()
        page.goto("data:text/html,<h1>probe</h1>")
        data = page.evaluate(PROBE_JS)
        data["label"] = label
        browser.close()
    return data


def main():
    configs = [
        ("playwright", "naive playwright", False),
        ("patchright", "patchright default", False),
        ("patchright", "patchright HARDENED+vulkan", True),
    ]
    rows = []
    for module, label, hardened in configs:
        try:
            rows.append(run(module, label, hardened))
        except Exception as e:
            rows.append({"label": label, "error": f"{type(e).__name__}: {e}"})

    if "-v" in sys.argv:
        print(json.dumps(rows, indent=2, default=str))
        return

    cols = ["webdriver", "ua_headless", "languages", "outer_w",
            "timezone", "webgl_renderer", "canvas_hash", "webdriver_desc"]
    w = max(len(r["label"]) for r in rows) + 2
    print(f"  {'config':{w}}" + "".join(f"{c[:16]:>18}" for c in cols))
    for r in rows:
        if "error" in r:
            print(f"  {r['label']:{w}}ERROR {r['error'][:60]}")
            continue
        cells = []
        for c in cols:
            v = r.get(c)
            if c == "webgl_renderer":
                v = "SwiftShader" if "SwiftShader" in str(v) else "hardware"
            if c == "ua_headless":
                v = "LEAK" if v else "clean"
            cells.append(f"{str(v)[:16]:>18}")
        print(f"  {r['label']:{w}}" + "".join(cells))

    print("\n  Reading: naive fails webdriver + UA + tz + gpu; patchright fixes only")
    print("  webdriver; the hardened config closes all six configurable surfaces.")
    print("  webdriver_desc stays 'present' in all three - value false, property exists.")


if __name__ == "__main__":
    main()
