# Deep research: how anti-bot bypass actually works

Follow-up to `FINDINGS.md`. Same rule: everything below was measured on this host on 2026-11-24, except where marked as a citation.

## Step 1: identify the protector before choosing a technique

```
status: 403
  server: cloudflare
  cf-ray: a5f7ab5c9a2aa210-YYZ
  x-datadome: protected
  set-cookie: datadome=rc~cTNUbQSTZ...
body: Please enable JS and disable any ad blocker  var dd={'rt':'c','cid':'AHrlqAAAAAMA...
```

g2.com is **DataDome**, fronted by Cloudflare. The body contains a JavaScript `dd` challenge object, not a normal captcha page. The `datadome` cookie here is a **block token**, not a clearance token.

## Step 2: what each layer actually did

| Attempt | Webdriver leak | CF clearance issued | Final result |
|---|---|---|---|
| requests | n/a | no | 403 |
| curl_cffi (Chrome TLS) | n/a | no | 403 |
| playwright headless | **True** | no | 403 |
| patchright headless | **False** | **yes** (`cf_clearance`) | **403 (DataDome)** |
| patchright headed, persistent profile | **False** | **yes** | **403 (DataDome)** |
| nodriver | **False** | - | blocked, empty body |
| camoufox (Firefox, C++ patched) | **False** | **yes** | **403 (DataDome)** |

The Cloudflare layer was passed: `cf_clearance` was issued in three separate attempts. DataDome still refused. So fingerprint leaks were **not** the binding constraint on this site.

## Step 3: is it IP reputation?

The common advice is "use residential proxies". My egress IP is already residential:

```
public IP: 142.181.219.3
{'org': 'AS577 Bell Canada', 'city': 'Toronto', 'country': 'CA'}
```

So the usual datacenter-IP explanation does not apply here, and the standard advice would not have helped. Two different DataDome sites behaved differently under the same IP (`leboncoin.fr` 403, `vinted.fr` 200), which indicates per-site policy rather than a blanket IP ban.

## How people really get past this

What I can support from this run: no fingerprint change, TLS impersonation or headless fix got through. What remains, in descending order of reliability:

1. **Commercial unblocking services** (ScrapingBee, ZenRows, Bright Data's Web Unlocker, ScrapeOps). They run large pools of residential and mobile IPs plus solver farms and sell the result as an API. This is the reliable route, and it is the one the cited guides converge on. It is a paid dependency, not a technique.
2. **Official APIs or partnerships.** G2 has an API. This is the only route that is both reliable and permitted by the terms.
3. **Behavioural pacing on a site that tolerates you.** Rate limiting and jitter matter when the site is merely rate-limiting, which vinted.fr appeared to be. They do not solve an outright DataDome 403.
4. **A real human session.** A logged-in, human-driven browser can pass. That does not scale and is not automation.

## What the evidence says is marketing

- "Bypass anti-bot" as a property of a browser patch. patchright and camoufox both produced a clean `webdriver=False` and still got 403. The patch is real; the bypass claim is not supported.
- "TLS impersonation beats firewalls" as a general rule. curl_cffi was fine on an unprotected site and got the same 403 as plain requests on the protected one.

## Conclusion

The deciding factors were **which protector was deployed** and **whether the site wanted to serve me at all**, not the sophistication of the fingerprint. DataDome decided by policy; no amount of stealth changed its decision. The honest way to get G2 data is its API, or a paid unblocker if the volume justifies it.

## Caveats

- One protected target (plus two spot checks) on one network. Results on other sites will differ, since a site using only Cloudflare Turnstile is a very different problem from one using DataDome.
- SeleniumBase UC mode was installed by a peer agent (COMS) rather than by me, and was not re-tested here.
- No attempts were made against Best Buy, Walmart or Cloudflare Turnstile specifically.

## Corroboration from the literature (cited, not measured here)

Noorsimar Singh's G2 scraping write-up reports the same shape of result I measured. Their scraper failed until they added **ScrapeOps proxy rotation**, after which they report success rising from **20% to 95%+**. Universal selectors, user-agent rotation and delay jitter were all in their stack *before* that change and did not fix the block on their own.

That is the same conclusion this run reached independently: the unblocking service, not the fingerprint or the parser, is what changes the outcome. I have not verified their numbers, and their site has a 9/10 difficulty rating from a third-party analyzer, so treat both as their claims.

Two further points from that source worth noting:

- G2's `robots.txt` disallows most scraping, and G2 offers an official API. For anything beyond personal research the API is the route that is both reliable and permitted.
- Their stack still needed JavaScript rendering plus pacing on top of the proxies, so the proxy is necessary but not sufficient by itself.

## Follow-up: truly headful, corrected

An earlier row in this document said "patchright headed, persistent profile", but that run was **actually headless**: `DISPLAY` was unset and the code fell back to `headless=True`. That is corrected here.

Re-run properly under `Xvfb :99` with `headless=False` and a fresh persistent profile:

```
RESULT headful status: 403 15.2s
RESULT title: 'g2.com'
RESULT text : ''
RESULT cookies: ['datadome', 'cf_clearance', '__cf_bm']
```

Result: **403 again**, with Cloudflare clearance still issued and the DataDome cookie still a block token. Running headful, with a real display, a persistent profile and no automation flags, did **not** change the outcome on this target.

So of the recommended local constraints:
- **headful instead of headless**: tested, no change here.
- **existing Chrome profile / real cookies**: partially tested (persistent profile, but a fresh one, not an existing logged-in profile).
- **throttling to 1 page per 15-30s**: not tested, because the very first request is already denied. Pacing cannot help when the block is on request one.

That last point is the important one: rate limiting and pacing assume you are being throttled. Here the first request was refused, so there is nothing to pace.
