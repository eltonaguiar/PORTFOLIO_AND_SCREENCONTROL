# LESSONS — the failure modes that produce confident wrong answers

Each lesson is a bug this programme actually hit, with the evidence. These are more valuable than the source list:
the source list tells you where to look, these tell you when the data is lying.

---

## 1. A 404 is a routing fact, not a verdict

`greenhouse/salesforce` → 404, `greenhouse/servicenow` → 404. That does **not** mean Salesforce or ServiceNow
don't hire, and it does not mean Greenhouse is broken. It means those companies use a different ATS —
ServiceNow turned out to be on **SmartRecruiters** (997 postings).

**Rule:** record which ATS a company uses, per company. Never generalise a 404 to a platform judgement.

---

## 2. Keyword search matches the description, not the title — so "25 jobs" is mostly noise

Job Bank returned **25 listings** for `servicenow` in Toronto. Fetching the actual postings:

| title | ServiceNow mentions | verdict |
|---|---:|---|
| `business consultant` (Blue Mantis) | 7 | ✅ *"experienced ServiceNow Business Process Consultant"* |
| `programmer analyst` (BC Assessment) | 7 | ✅ *"take ownership of … ServiceNow platform"* |
| `information technology (IT) analyst` (Aviso Wealth) | 1 | ✅ secondary — *"GRC tools (e.g., Archer, ServiceNow GRC, Resolver)"* |
| `food delivery driver` (EDC, Montréal) | 1 | ❌ **false positive** |
| `food delivery driver` (EDC, Ottawa) | 1 | ❌ **false positive** |

**Precision: 3 of 5.** Both false positives are the same sentence:

> *"Internal Employees, please consult the ServiceNow article entitled Internal movements"*

That is an HR intranet reference, not a skill requirement.

**Rules that work:**

- Drop any hit within ~80 characters of `internal employees`, `consult the`, or `article entitled`.
- Then require **≥2 surviving mentions**, *or* a single mention inside a requirements/skills section.
- **Fetch the detail page.** The list page alone cannot distinguish a ServiceNow consultant from a food
  delivery driver.
- **Filter location after classification**, not before: `programmer analyst` was Victoria, BC — a "Toronto"
  query returned it because Job Bank broadens nationally.

Separate data-quality note: Export Development Canada, a federal export agency, listing *food delivery driver*
twice is a Job Bank posting-quality problem, not a scraping problem.

---

## 3. Kijiji prices are in CENTS

`StandardListing.price.amount` returned `60000` for a **$600** console. My first parse compared raw values and
reported a **median price of $60,000**.

**Rule:** divide by 100, and sanity-check the result against a known MSRP band before publishing anything.
A 100× error is not subtle once you look — but it parses cleanly and reads as plausible if you don't.

---

## 4. Best Buy's availability API cannot answer "in stock near me"

Nine GTA postal codes, byte-identical response: `InStock qty=105`, `pickup: NotAvailable`, `locations: 0`.

**Rule:** for Best Buy, the availability API is a **national online-shipping** signal. It is a legitimate lead,
but it is **not** evidence of Toronto stock, and `pickup` is never populated. Do not attach a city to it.

The converse trap from earlier in this project: `pickup: NotAvailable / locations: []` also does **not** mean
"sold out in store" — it means the field is not implemented. Unpopulated is not zero.

---

## 5. Stale ASINs become dead listings that still render a title and a price

Three PS5 ASINs returned **$129.98** and **$229.99** with an empty availability block and no add-to-cart.
Those are not bargains — they are retired listings.

**Rules:**
- Keep an **MSRP band per SKU** (roughly `0.6×` to `1.3×`) and drop anything outside it.
- A price with **no availability block and no add-to-cart** is a dead page, not an opportunity.
- Re-discover SKUs each run; never reuse a remembered one.

---

## 6. `soldBy` is the tie-breaker between a restock and a reseller

Xbox Series X 1TB, Amazon.ca: **"Only 2 left in stock" at $1,299.50, sold by `CCJamesInc`.** MSRP is far below
that, and there was no visible add-to-cart.

**Rule:** read `#sellerProfileTriggerId`. A third-party seller at a premium is not a restock. Report first-party
only as "verified retail".

---

## 7. A zero must never be reported the same way as a block

"0 listings found" and "403 Forbidden" are different facts. Collapsing them into one number is how a dead
source looks healthy for weeks.

**Rule:** keep a `sources_status.json` with `last_success`, `http_status`, and `item_count` per source, and
surface it. A source that has returned 0 for N runs is *stale*, not empty.

---

## 8. Verify the payload, not the parameter

`?rss=1` on a Kijiji search returned **421 KB of HTML, not RSS**. Had I trusted the parameter name I would have
been parsing XML tags that were never there.

**Rule:** check the content — does it contain `<item>` / `"__NEXT_DATA__"` / valid JSON — before choosing a
parser. `/rss-srp-...` returned a hard **403**; the plain search page returned 200.

---

## 9. A 200 is not a success — check the content type

This section previously claimed a host trick as the fix. It was wrong, and the correction is the better lesson.

| request | result |
|---|---|
| `www.reddit.com/r/…/search.json` | **403 Blocked** |
| `old.reddit.com/r/…/search.json` | **200 — but `Content-Type: text/html`, 342,840 B** |
| `api.reddit.com/r/…/search` | **403 Blocked** |

The old domain did return 200. It returned the **SPA shell**: `is JSON? False`, **0** `class="thing"` cards,
**0** search-result links. No listings in it. Calling that "working" because the status code was 200 is the
same class of error as calling an empty `content` field "the model got it wrong" — the status is not the result.

**Rule:** after any fetch, assert on **shape**, not status — `content-type`, does it parse as the format you
asked for, and does it contain N>0 expected records. `LESSONS.md` §8 says verify the payload; this section is
what happens when you don't.

**What actually solved it:** the useful ATS discovery in the same round was **Workday needing POST**, found by
reacting to a 400 as "wrong verb?" rather than "dead endpoint".

---

## 10. Query strings with spaces break native URL fetchers

Canada Computers search links come back as `/en/xbox/184244/slug.html?keyword=xbox series x`. Passing that
straight to `urllib` raises **`URL can't contain control characters`**.

**Rule:** strip the query string (`.split("?")[0]`) or percent-encode it. Free discovery, cheap fix.

---

## 11. Retry government endpoints; they reset connections

`jobbank.gc.ca` returned `WinError 10054` ("connection forcibly closed") on one attempt and a clean 277 KB on
the next. That is rate-limiting, not a block.

**Rule:** retry with backoff (3–5 attempts, 3–15 s) and send `Connection: close`. Do not record a single reset
as "source dead".

---

## 12. A public page can contain the word "captcha" without being challenged

The Kijiji search page contains `captcha` in its source **and** returned 45 real listings. Grepping for the
word and aborting would be a false negative.

**Rule:** judge by whether the data is present in the payload, not by the presence of defensive keywords.

---

## 13. Atom is not RSS, and a `<item>` count will lie to you

I eliminated RedFlagDeals as "blocked" after counting `<item>` and finding **0**. The feed was live the whole
time:

```
https://forums.redflagdeals.com/feed/forum/9
HTTP 200 · Content-Type: application/atom+xml · 24,200 B · 15 <entry> elements
```

Two stacked errors: I had tested **wrong paths** (`/feeds/hot_deals/`, `/deals/feed/` → 202 challenge), then
when I finally hit the right one I grepped for **RSS `<item>`** on an **Atom** feed, which uses `<entry>`.

**Rule:** before declaring a feed dead, check all four of:

1. `Content-Type` — `application/rss+xml`, `application/atom+xml`, `text/xml`.
2. Element name — **`<item>` (RSS) or `<entry>` (Atom)**. Never assume.
3. Element count > 0.
4. The URLs you tried are the canonical ones. A forum's feed is usually `/feed/forum/{id}`, not `/feed/hot-deals/`.

That is three separate verdicts in this directory I got wrong from checking the wrong thing: `old.reddit.com`
(status, not content type), Kijiji `?rss=1` (parameter, not payload), and now RedFlagDeals (element, not feed).
**In every case the fix was to assert on parsed shape, not on a proxy for it.**

---

## 14. A detailed answer can be more correct than a careful-sounding one

The two endpoints I had wrongly eliminated — RedFlagDeals' forum feed and the Workday detail GET — were both
named correctly by **Qwen4 Max**, the longest and most code-heavy of thirteen answers. Meanwhile the answers
that *sounded* most disciplined ("skip the arms race, use the obvious feeds") were the ones recommending
Craigslist RSS, which is a hard 403.

**Rule:** judge advice by whether its specific claims survive a probe, not by whether its tone matches your
priors. Length and specificity are not quality signals on their own — but a named URL is falsifiable, and a
principle is not.

---

## 15. Anti-bot technique is target-specific, and the cheapest method usually wins

Measured across six retail targets with seven methods
(`ANTIGRAVITY_KIT_2026-11-24/REVIEW_AND_VERIFICATION.md`). There is no "best scraper", only a best first
attempt:

| Target | plain curl | `curl_cffi` (TLS) | Playwright headful | apex winning method |
|---|---|---|---|---|
| Best Buy ecomm-api | **200** | 200 | — | plain HTTP is enough |
| Amazon.ca search | **200, 1.98 MB** | 200 but 2.2 KB bot shell | — | plain curl |
| Staples search | 403 | **200, full 396 KB page** | 200, shell only 9.2 KB | `curl_cffi` |
| Walmart search | 403 | 200 but 7.5 KB challenge | **200, 50 products** | Playwright headful |
| Memory Express | 403 | 403 challenge | 403 | **none — blocked** |
| GameStop | 000 | DNSError | timeout | host unreachable |

**Three rules, each from a row above.**

1. **Probe with `curl_cffi` before launching a browser.** TLS/JA3 impersonation in a plain HTTP client took
   Staples from `403` to a complete page; Playwright on the same target got a 9.2 KB shell. Two of the three
   wins here needed no browser at all.
2. **If a browser is genuinely needed, it must be the installed Chrome headful with a persistent profile —
   never the Playwright headless shell.** The headless shell is fingerprinted; `channel="chrome"` headful
   returned 50 real products from Walmart where the shell returned a challenge.
3. **Know when the block is on the data endpoint rather than the document.** Memory Express served its page
   to nodriver (real title, ~2.5 KB body) while its search-results API returned `403` to all five methods.
   No amount of evasion fixes that. Record it blocked and spend the effort elsewhere.

**Corollary:** `patchright` gave no measurable advantage over plain Playwright where both were tried, and
"untested" is not "disproven" — Camoufox, CloakBrowser, Skyvern and browser-use remain untried.

