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
| `EXTERNAL_ADVICE_AUDIT.md` | **Thirteen AI answers scored against live tests** — which advice survived contact |
| `SEMIFINALS/` | Compiled shortlist: candidates that passed a first probe, with trade-offs |
| `FINALS/` | **Endorsed solutions** — the ones that returned real data, plus runnable scripts |
| `ANTIGRAVITY_KIT_2026-11-24/` | **Anti-bot bake-off** — which technique defeats which block (plain curl vs `curl_cffi` TLS vs Playwright headful vs nodriver vs patchright), measured on six retail targets. See `LESSONS.md` §15 |

## The one-paragraph verdict

The working path is **machine-readable endpoints, not browser evasion.** **Eight** sources returned real data
without a single challenge: **Greenhouse**, **Ashby**, **SmartRecruiters**, **Workday (POST + detail GET)**,
**Personio XML**, **RedFlagDeals Atom**, **Canada Computers static HTML**, and **Kijiji's `__NEXT_DATA__`**.
One more works but needs a classifier to be useful: **Job Bank Canada**. Five popular "keyless" suggestions
from external advice are **blocked**: Craigslist RSS (403), `www.reddit.com` JSON (403), `old.reddit.com`
(200 but HTML shell, no listings), eBay Browse API without a key (403), and every Best Buy product page (Akamai).

> **Two corrections carried in this tree.** `old.reddit.com` was recorded as working because it returned 200 —
> it returns `text/html` with zero listings (`LESSONS.md` §9). And **RedFlagDeals was wrongly eliminated as
> "blocked"**: the correct feed `/feed/forum/9` returns HTTP 200 `application/atom+xml` with 15 entries. I had
> tested wrong paths and then counted `<item>` on an **Atom** feed (`LESSONS.md` §13).

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
