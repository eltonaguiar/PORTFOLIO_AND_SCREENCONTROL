# SEMIFINALS — the compiled shortlist

Every candidate here **passed a first probe**: it returned HTTP 200 and parseable data, or it returned a clean
explicit block that makes it a contingent option rather than a dead end. Scored on the five things that decide
whether a source belongs in a cron job.

## Scorecard

Scale 1–5. **Reliability** = did it answer on every attempt. **Autonomy** = can it run unattended with no human
and no paid infra. **Precision** = does a match mean what it says. **Effort** = 5 is cheapest to integrate.
**Cost** = 5 is free.

| # | Source | Rel. | Auto. | Prec. | Eff. | Cost | Total | Role |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | **Greenhouse JSON** | 5 | 5 | 5 | 5 | 5 | **25** | Job feed, tech employers |
| 2 | **Ashby JSON** | 5 | 5 | 5 | 5 | 5 | **25** | Job feed, tech employers |
| 3 | **SmartRecruiters JSON** | 5 | 5 | 5 | 5 | 5 | **25** | Job feed — **this is where ServiceNow lives** |
| 4 | **Canada Computers HTML** | 4 | 5 | 5 | 4 | 5 | **23** | Console stock, per-store, GTA |
| 5 | **Kijiji `__NEXT_DATA__`** | 4 | 5 | 3 | 3 | 5 | **20** | Used/local console listings |
| 6 | **Workday CXS (POST)** | 5 | 5 | 5 | 3 | 5 | **23** | Job feed — largest enterprise ATS; **GET 400, POST works** |
| 7 | **Job Bank Canada** | 3 | 4 | **2** | 3 | 5 | **17** | Canadian job coverage — needs a classifier |
| 8 | **Best Buy availability API** | 5 | 5 | **2** | 5 | 5 | **22** ⚠ | National shipping flag only — see below |
| 9 | **Amazon.ca (browser)** | 4 | 3 | 5 | 2 | 5 | **19** | Real per-product delivery dates |
| 10 | **eBay Browse API** | — | 5 | 5 | 4 | 4 | contingent | Needs a free developer key |
| 11 | **Lever** | — | 5 | 5 | 4 | 5 | contingent | Endpoint real; board tokens unknown |
| — | **old.reddit.com** | — | — | — | — | — | **eliminated** | **200 but `text/html`** — SPA shell, 0 listings (corrected) |
| — | **RedFlagDeals RSS** | — | — | — | — | — | **eliminated** | 202 challenge, 2,926 B, 0 items |
| — | **Best Buy product pages** | — | — | — | — | — | **eliminated** | Akamai `🐴 Access Denied` |

## Why #8 scores high and still loses

Best Buy's availability API is reliable, free and trivial to call — and **useless for the question being asked**.
Nine GTA postal codes returned byte-identical `InStock qty=105`, `pickup: NotAvailable (0 locations)`.
A high total score on the wrong dimension is how a pipeline ends up asserting Toronto stock it cannot see.

It stays in the shortlist as a **price/availability floor for new units**, not as a local-stock signal.

## Why #7 (Job Bank) is in and #12 is out

Job Bank answers every time and covers Canadian employers nobody else indexes — but its keyword search matches
description text, so 2 of 5 "ServiceNow" hits were `Internal Employees, please consult the ServiceNow article`.
It is a real source with a real precision defect, which is fixable with a classifier.

Best Buy product pages are not fixable by any code change we are willing to make: a real Chrome gets Akamai's
access-denied page. Eliminated.

## Pairing, not ranking

No single source answers both questions, so the shortlist is a **portfolio**:

- **Console availability** → Canada Computers (per-store truth) + Amazon browser (delivery date) + Best Buy API
  (price floor). Kijiji and old.reddit for the used market.
- **Jobs** → Greenhouse + Ashby + SmartRecruiters (keyless, precise) + Job Bank (Canadian breadth) **with a
  title/context classifier** to fix precision.

## Promoted to FINALS

- Console: **Canada Computers**, **Kijiji `__NEXT_DATA__`**, **Amazon browser read**
- Jobs: **Greenhouse**, **Ashby**, **SmartRecruiters**
- Conditional: **Job Bank** — promoted **only with** the classifier described in `LESSONS.md` §2
- Recorded as lead-only: **Best Buy API** (national, not local), **old.reddit.com** (companion signal)
