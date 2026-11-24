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

## The one-paragraph verdict

The working path is **machine-readable endpoints, not browser evasion.** Six sources returned real data without
a single challenge: **Greenhouse**, **Ashby**, **SmartRecruiters**, **Workday (via POST)**, **Canada Computers
static HTML**, and **Kijiji's `__NEXT_DATA__`**. One more works but needs a classifier to be useful:
**Job Bank Canada**. Six popular "keyless" suggestions from external advice are **blocked**: Craigslist RSS
(403), `www.reddit.com` JSON (403), `old.reddit.com` (200 but HTML shell, no listings), RedFlagDeals RSS
(202 challenge), eBay Browse API without a key (403), and every Best Buy product page (Akamai).

> **Correction carried in this tree:** an earlier version of `SOURCES.md` listed `old.reddit.com` as a working
> workaround. It returns **200 with `Content-Type: text/html`** and zero listings. The status code was mistaken
> for the result. `LESSONS.md` §9 and `SOURCES.md` §B are both corrected.

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
