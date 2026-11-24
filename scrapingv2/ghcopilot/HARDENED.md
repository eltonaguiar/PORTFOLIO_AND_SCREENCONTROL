# Hardened configuration — what actually closes the leaks

**Run:** `2026-11-24T09:50Z` · **Method:** every row below was executed, not inferred. `hardened.py` reproduces it.

This extends [`README.md`](README.md). That report measured *what leaks*; this one defines a **modified configuration that closes the leaks**, and states precisely which leak no configuration can close.

## The delta, measured on one checklist

| check | naive `playwright` | `patchright` default | **hardened + Vulkan** |
|---|---|---|---|
| `navigator.webdriver` | **`true`** | `false` ✅ | `false` ✅ |
| UA contains `Headless` | **yes** | **yes** | `no` ✅ |
| `navigator.languages` | `en-US,en` | `en-US,en` | `en-CA` ✅ |
| viewport / `outerWidth` | `1280×720` | `1280×720` | `1440×900` ✅ |
| `Intl` timezone | `UTC` | `UTC` | `America/Toronto` ✅ |
| WebGL renderer | **SwiftShader** | **SwiftShader** | **NVIDIA GB10 (Vulkan)** ✅ |
| 2D canvas hash | `-1781530274` | same | same — *not GPU-dependent* |

**Leaks closed: 1 of 6 → 5 of 6.** Naive Playwright fails five of six; the middle config fails three; the hardened config fails none of the six configurable surfaces.

## The two findings that make this worth doing

### 1. `HeadlessChrome` in the UA survives "undetected" browsers

`patchright` clears `navigator.webdriver` and still sends `HeadlessChrome/157.0.0.0`. It passes the one flag the earlier evaluations measured and fails the next. Fixed with an explicit `user_agent` on the context — one line.

### 2. SwiftShader is the leak no flag combination fixes — except Vulkan

Default headless Chrome reports:

```
ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (LLVM 10.0.0) (0x0000C0DE)), SwiftShader driver)
```

`SwiftShader` is the software rasteriser. Every headless instance on the machine emits that string, so it is a **fleet-wide identifier**, not just an automation tell. Tested variants:

| launch args | renderer |
|---|---|
| *(none)* | SwiftShader ❌ |
| `--use-gl=egl` | context creation fails (`ERR`) |
| `--use-gl=angle --use-angle=gl` | fails (`ERR`) |
| `--disable-software-rasterizer --use-gl=egl` | fails (`ERR`) |
| **`--use-gl=angle --use-angle=vulkan`** | **`ANGLE (NVIDIA, Vulkan 1.4.312 (NVIDIA NVIDIA GB10 (0x00002E12)), NVIDIA)`** ✅ |

The Vulkan path is the only one that both succeeds and reports real hardware. Three of the five flag combinations simply break WebGL — which is worse than the leak, because a missing WebGL context is itself anomalous.

## The working configuration

```python
ARGS = ["--no-sandbox", "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--use-gl=angle", "--use-angle=vulkan"]

b = p.chromium.launch(headless=True, channel="chrome", args=ARGS)
ctx = b.new_context(
    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36",
    viewport={"width": 1440, "height": 900},
    locale="en-CA", timezone_id="America/Toronto")
```

Notes that cost time to learn:

- `channel="chrome"` is **required** on this host. Without it Playwright requests `chromium_headless_shell-1255`, which is not cached, and launch fails.
- `timezone_id` and `locale` must agree with each other and with the `Accept-Language` header. Setting `locale="en-CA"` while the TLS layer announces a US Chrome is a *new* inconsistency, not a fix.
- The viewport must be a plausible desktop size. The default `1280×720` equals the screen size exactly, which a `screen.width == outerWidth` check can catch.

## Network layer — which profile to pick

Each profile probed **5 consecutive times**, counting unique values:

| profile | JA3 unique /5 | JA4 unique | HTTP/2 unique | verdict |
|---|---:|---:|---:|---|
| `chrome` | **5** | 1 | 1 | JA3 churns every run — **cannot be allowlisted** |
| `chrome124` | **5** | 1 | 1 | same |
| `chrome131` | **5** | 1 | 1 | same |
| `safari` | **1** | 1 | 1 | **stable — usable for allowlist** |
| `safari17_0` | **1** | 1 | 1 | stable |
| `firefox133` | **1** | 1 | 1 | stable |
| `firefox` | **1** | 1 | 1 | stable |

**Actionable consequence:** if a target allowlists on JA3, **use `safari` or `firefox133`, never a Chrome profile** — Chrome's ClientHello varies per connection, so a Chrome JA3 allowlist entry will miss most of your own requests. If the target keys on JA4 or the HTTP/2 fingerprint, Chrome is fine and stable.

This also explains a failure mode that looks like a block but isn't: a Chrome impersonation against a JA3-allowlisting WAF produces intermittent success, which gets misread as rate limiting.

## Residual leaks — stated, not hidden

The hardened config is not "undetectable". It closes six surface checks; it does not close these:

1. **Canvas hash is identical across all sessions on this host** (`-1781530274`). It did not change with the GPU, so canvas is host-stable rather than per-session random. Any site fingerprinting canvas sees the same value from every session here.
2. **`Object.getOwnPropertyDescriptor(Navigator.prototype,'webdriver')` is still `present`** in all three configs, including hardened. The *value* is `false`, but a site that checks for the descriptor's existence rather than its value still sees the automation-shaped prototype.
3. **CDP attachment is not hidden from the page.** `patchright` patches the `Runtime.enable` leak; other CDP domains were not tested.
4. **Behaviour is untouched.** No mouse curvature, keystroke timing, or navigation pacing. A perfect fingerprint with robotic behaviour still fails behavioural scoring.

## Honest ceiling

Config alone gets you a browser that passes static fingerprint checks on a machine with a real GPU. It does not get you past a challenge that scores *behaviour*, and it does not get you past a JS challenge you have not solved. The cheapest real win remains `curl_cffi` with a **Safari or Firefox** profile for anything that does not need JS.

## Reproduce

```bash
python3 hardened.py          # the full matrix, all three configurations
python3 -c "from curl_cffi import requests as r; print(r.get(
  'https://tls.browserleaks.com/json', impersonate='firefox133').json())"
```
