# ANTIGRAVITY_KIT_2026-11-24 — anti-bot tool bake-off, ported from the review repo

**Provenance:** copied from `eltonaguiar/antigravity_review_Nov192026`
`41_SCRAPING_KIT_2026-11-24/` at commit **`f8fe20f`** ("Scraping kit: archive arena.ai blueprint + live
verification of 7 anti-bot approaches"). Nothing here was re-run for this copy — every number is the
one recorded at that commit.
**Added to this tree:** 2026-11-24. **Owner of the source of truth:** the review repo; this is the
read copy.

## Why it belongs in `SCRAPING/`

`FINALS/` answers *which job-board endpoints return data* (Greenhouse, Ashby, Workday, Kijiji
`__NEXT_DATA__`, …). This folder answers a different question: **when a target blocks you, which
technique actually defeats the block** — measured against six retail targets with seven methods. The
two are complementary; neither supersedes the other.

## The four rules that survived testing

These are the durable output. Everything else in here is supporting evidence.

1. **Try `curl_cffi` before any browser.** It reproduces Chrome's TLS/JA3 handshake in a plain HTTP
   client. Staples went from `403` to a **complete 396 KB page** with zero browser overhead.
   Playwright on the same target returned only a 9.2 KB shell.
2. **If it blocks you anyway, the data may still be in a first-party JSON endpoint.** Staples'
   Shopify `search/suggest.json` returned 10 products with first-party pricing, all available.
   Best Buy's `ecomm-api/availability/products` returned real stock JSON to **plain HTTP, no tricks**
   (SKU `19422130` → shipping `InStock`, pickup `NotAvailable`) while its HTML product page returned
   `403` from Akamai. The endpoint is not the page.
3. **When a browser is genuinely required, use the installed Chrome headful with a persistent
   profile — never the headless shell.** Walmart: plain `403`, `curl_cffi` `200` but a 7.5 KB
   challenge page, **Playwright `channel="chrome"` headful `200` with 50 products**. The stock
   Playwright headless shell is fingerprinted and fails. This is the single most important detail in
   the whole set.
4. **If the block is on the data endpoint, no browser trick helps.** Memory Express returned `403` on
   its search-results API under **all five** methods — plain `403`, `curl_cffi` `403` challenge,
   Playwright `403`, nodriver ran but its results `403`, patchright `403`. The document loads; the
   data does not. Record it as blocked and stop, rather than buying more evasion.

Also recorded: `patchright` showed **no measurable advantage** over plain Playwright on the one
target where both were tried, and GameStop was simply unreachable (DNS). Camoufox, CloakBrowser,
Skyvern and browser-use were **not tested** — untested, not disproven.

## What is in here

| Path | What it is |
|---|---|
| `REVIEW_AND_VERIFICATION.md` | **Start here.** Claim-by-claim audit with CONFIRMED / WRONG / PARTIAL status, plus the full target × method bake-off and the captured product data |
| `REFERENCE_BLUEPRINT_not_fully_reliable.md` | The architecture blueprint that prompted the audit, kept for context. **Read the warning below before trusting it** |
| `scripts/tls_test.py` | `curl_cffi` TLS-impersonation probe |
| `scripts/pw_scrape.py` | Playwright with `channel="chrome"` + persistent profile (the Walmart winner) |
| `scripts/nd_scrape.py` | nodriver variant |
| `scripts/pr_scrape.py` | patchright variant |
| `scripts/staples_extract.py` | Shopify `search/suggest.json` extraction |
| `results/walmart_ps5_playwright.json` | 50 products captured headful |
| `results/staples_suggest.json` | 10 products via the suggest endpoint |
| `results/curl_cffi_results.json` | TLS-probe outcomes per target |
| `results/patchright_memexpress.json` | The `403` that proves the endpoint-level block |

## Warning on the blueprint

The blueprint is **architecturally sound and factually unreliable**. Its two load-bearing technical
claims (the Best Buy JSON endpoint, and datacenter IPs being what Walmart/Staples/Memory Express
block) both reproduced. But of five files it claimed to have audited, **two do not exist**
(`linkedin_guest_scan.py`, `gx10_runner.py`), and two of its three corpus numbers are wrong: it says
`3,381` "Other" listings where the live file has **3,159** of 4,970 rows, and `5,626` jobs where
`jobs.json` then held **5,632**. Treat its architecture as a design sketch and its numbers as noise.

## Reproducing a single target

```bash
pip install curl_cffi
python scripts/tls_test.py                      # cheapest first: does TLS impersonation clear it?
python scripts/pw_scrape.py --url <target-url>  # only if a browser is genuinely required
```

Run `tls_test.py` first every time. Two of the three successes in this set needed no browser at all.
