# What actually worked (2026-11-24T1019Z)

Single polite requests (no auth, no CAPTCHA solving, no proxy rotation). One
attempt per site; 3–4 s spacing. "Success" = real product data returned.

## Successes

### 1. Best Buy — per-SKU availability API (BEST RESULT)
`GET https://www.bestbuy.ca/ecomm-api/availability/products?accept=application/vnd.bestbuy.standardproduct.v1+json&accept-language=en-CA&skus=<SKU>`
with `curl_cffi impersonate="chrome"`:

| SKU | Result |
|---|---|
| 19422130 (Xbox Series S 512GB) | **InStock** (shipping), pickup NotAvailable |
| 19446111 (PS5 Slim 1TB) | **SoldOutOnline**, pickup NotAvailable |

- Plain `requests`: **ReadTimeout** (30 s) — TLS impersonation is the difference.
- The **HTML product page returned 403 "Access Denied"** for the same URL family.
- This is the site's own JSON endpoint, not a bypass: no challenge was solved.

### 2. Walmart — embedded Next.js data
`GET https://www.walmart.ca/en/search?q=playstation+5` with curl_cffi:
- 200, 613 KB, `__NEXT_DATA__` present.
- `itemStacks[0].items` = **48 items** with `name`, `price`, `priceInfo`, `canonicalUrl`.
- Sample: "Refurbished 2K NBA 24 Kobe Bryant Edition (Play Station 5)" — $21.61.
- The repo previously listed Walmart as "Forbidden"; it is readable via the embedded
  JSON, but note many rows are games/accessories, not consoles.

### 3. Canada Computers
- 200, 546 KB, correct product title (already worked in the tracker).

## Failures (honest)
| Target | Result |
|---|---|
| Best Buy **HTML** product page | **403 Access Denied** (Akamai) — TLS impersonation did not help |
| Staples search | 200 but Cloudflare challenge shell: no product JSON, `server: cloudflare` |
| Memory Express | 200 but `just a moment` challenge shell |
| G2 (per zoocode) | 403 to requests, curl_cffi, patchright, playwright; empty body to nodriver |

## The modified approach that produced success
1. **Prefer the site's own JSON**: availability APIs / `__NEXT_DATA__` payloads.
   The HTML is often gated; the JSON behind it frequently is not.
2. **Use TLS/HTTP2 impersonation** (`curl_cffi impersonate="chrome"`) for those JSON
   endpoints — it changed a timeout into a 200.
3. **If a browser is required**, set an explicit `user_agent` (patchright leaks
   `HeadlessChrome` otherwise) and expect HTML-level Akamai/Cloudflare to still block.
4. **Do not** escalate to CAPTCHA solving or residential-proxy evasion; that is a
   different risk/ToS category and was not attempted.

## G2 specifically
The suggested stack (residential proxies + CAPTCHA/JS unlocking) is out of scope here:
it is anti-bot circumvention and ToS-risky. Legitimate alternatives: G2's official
API/partnership, or a licensed data provider. If the goal is G2 reviews at scale,
buy access rather than evade the block.

## Artifacts
`retail_probe.json`, `bestbuy_api.json`, `walmart_extract.json`, and the five
re-runnable scripts in this folder.
