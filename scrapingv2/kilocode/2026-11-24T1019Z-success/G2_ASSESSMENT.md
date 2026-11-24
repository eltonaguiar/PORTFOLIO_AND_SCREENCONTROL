# G2.com scraping article — factual check (2026-11-24)

Checked the widely-shared "production-ready G2 scraper" write-up against this host.

## Verified
- **G2 blocks plain/TLS-impersonated HTTP:** one polite `curl_cffi impersonate="chrome"`
  GET to `https://www.g2.com/` returned **403** from `server: cloudflare` (1,880 bytes).
  Consistent with the article's premise and with zoocode's independent 403 result.
- `robots.txt` is real and long (**314 lines**), with `Crawl-delay: 1`.

## Overstated / unverified
- **"Robots.txt disallows most scraping" — not supported.** There is **no
  `Disallow: /`**. The rules target query-string variants (`focus_review`, `format=pdf`,
  `locale`, `utm_*`, `gclid`, `fbclid`, `hsa_*`, `__hstc`, `scriptPath`) — see
  `g2_robots_2026-11-24.txt`. The real constraint is G2's **Terms of Service**, not robots.
- **"9/10 difficulty"** is a vendor score from ScrapeOps' analyzer, not an independent measure.
- **"20% → 95%+ success"** is unverified, environment-dependent, and depends on a paid
  rotating-proxy/JS-rendering service. The free tier is small; the cost scales with volume.
- **"Production-ready"** understates the operational load: proxy spend, challenge handling,
  selector drift, and legal review are ongoing, not one-time.

## What is technically sound
Selector fallback chains, dedupe keys, conditional export files, retries/backoff and
rate limiting are good engineering and reusable on sites you are allowed to scrape.

## What I would not do (and did not)
CAPTCHA solving, residential-proxy rotation to defeat blocks, or fingerprint evasion
against a site that prohibits it. That is a ToS/legal risk category, not an engineering
challenge. Compliant paths: **G2's official API/partnership** or a **licensed data vendor**.

## Better pattern that actually worked here (no evasion)
- **Best Buy**: per-SKU availability JSON → `InStock` / `SoldOutOnline` (HTML was 403).
- **Walmart**: embedded `__NEXT_DATA__` → 48 items with name/price/url.
- **Canada Computers**: ordinary 200 page.
See `SUCCESS.md` in this folder for numbers and scripts.
