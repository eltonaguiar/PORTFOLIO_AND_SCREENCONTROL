# SCRAPING — what actually works, proven by test

**Date:** 2026-11-24 · **Scope:** autonomous web harvesting for (a) Xbox/PS5 console availability in the GTA, and
(b) ServiceNow / Salesforce job listings for Canada.

Every claim in this tree is backed by a request this programme actually made. Sources that returned 403 or an
Akamai wall are recorded as failures, not quietly dropped — the failures are the reason the winners exist.

## Structure

| Path | What lives here |
|---|---|
| `SOURCES.md` | **Every source probed**, with HTTP status, payload size, and verdict |
| `LESSONS.md` | **Failure modes** — the bugs that produce confident wrong answers |
| `SEMIFINALS/` | Compiled shortlist: candidates that passed a first probe, with trade-offs |
| `FINALS/` | **Endorsed solutions** — the ones that returned real data, plus runnable scripts |

## The one-paragraph verdict

The working path is **machine-readable endpoints, not browser evasion.** Five sources returned real data without
a single challenge: **Greenhouse**, **Ashby**, **SmartRecruiters**, **Canada Computers static HTML**, and
**Kijiji's `__NEXT_DATA__`**. Two more work only with a workaround: **old.reddit.com** (where `www.reddit.com`
is blocked) and **Job Bank Canada** (works, but needs a classifier to be useful). Four popular
"keyless" suggestions from external advice are **blocked**: Craigslist RSS (403), `www.reddit.com` JSON (403),
eBay Browse API without a key (403), and every Best Buy product page (Akamai).

## Three findings that change the design

1. **Best Buy's availability API is postal-code invariant.** Nine GTA postal codes returned byte-identical
   `InStock qty=105` and `pickup: NotAvailable (0 locations)`. It **cannot** answer "in stock near Toronto" —
   it is a national online-shipping flag. Any local-stock claim resting on it is unsupported.
2. **Job Bank keyword search is mostly false positives.** Five postings matched "servicenow"; only three
   genuinely were. The two false positives were the same HR boilerplate: *"consult the ServiceNow article
   entitled Internal movements"*.
3. **Kijiji prices are in cents.** `price.amount` returns `60000` for $600. Comparing raw values against a
   dollar threshold produces a 100× error that looks plausible.

## What this tree deliberately refuses

- **No proxy, CAPTCHA-solver, or stealth-plugin recommendation.** Those appear in most external advice and none
  of it names a working endpoint. The free sources above returned data without a challenge; paying ~$80–280/mo
  to defeat a wall we do not need to cross is not engineering.
- **No LinkedIn scraping.** Its own alert emails and the ATS boards behind its listings carry the same
  postings at zero ban risk.
- **No silent zeros.** A source that returns 0 items must be recorded as *blocked* or *stale*, never as
  "no listings" — `SOURCES.md` keeps that distinction explicit.
