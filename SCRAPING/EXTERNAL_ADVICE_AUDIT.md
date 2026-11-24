# EXTERNAL ADVICE AUDIT — thirteen answers, scored against what actually happened

**Date:** 2026-11-24. Six answers arrived via `chatplayground`, six via `askanymodel.xyz`, one via `1min.ai`,
one via free-tier surfaces. Their testable claims were run against live sites. This file records which advice
survived contact and which did not.

The purpose is not to grade the models. It is that **the failure patterns repeat**: the same handful of
"keyless" sources are recommended by almost everyone, and almost all of them are blocked. A future reader
should not have to re-run this to find out.

---

## Claims that survived

| claim | who said it | test result |
|---|---|---|
| **Greenhouse board API is public** | Claude (Latest), GLM 5.3, Claude 5.1, Claude 5.2, Gemini 4 Neon, ChatGPT-6 Luna | ✅ **stripe 771, datadog 382, gitlab 251, coinbase 249, airbnb 199, instacart 96** |
| **Ashby posting-API is public** | Claude 5.2, Claude 5.1 | ✅ **openai 863, ramp 180, supabase 81, linear 30** |
| **SmartRecruiters exposes a public board** | **GLM 5.3 Flash**, Claude 5.2 | ✅ **ServiceNow — 997 postings, 26 in Canada.** Only these two named it; it is where ServiceNow actually lives |
| **Workday has a JSON endpoint** | **Claude 5.2 Fable** | ✅ but **only as a POST** — see below |
| **Don't scrape LinkedIn; use alerts / ATS / aggregators** | every answer | ✅ and it is also what the user asked for |
| **GitHub Actions cron → normalise → dedupe → commit JSON → Pages** | ChatGPT-6 Luna, Claude (Latest), GLM 5.3, Claude 5.1, Claude 5.2, Gemini 4 Neon | ✅ already how both repos work |
| **LLM for extraction/classification, not for fetching** | Claude 5.2, Gemini 4 Neon, ChatGPT-6 Luna | ✅ and the Job Bank test shows exactly why: classification is the bottleneck |
| **Embedding centroid / few-shot for category patterns** | Qwen3.6, GLM 5.3, Claude 5.2, Gemini 4 Neon | ✅ sound, and it is the right answer to the user's "find jobs by common pattern" ask |
| **Keep a `sources_status.json`** (last success, item count) | **Claude 5.1 Fable** | ✅ best engineering suggestion in the whole set — a dead source looks identical to an empty one otherwise |
| **Open a GitHub issue when an adapter returns 0** | **Claude 5.2 Fable** | ✅ adopted as a recommendation |
| **`git diff --quiet || git commit`** to avoid no-op commits | Claude 5.1 Fable | ✅ |
| **Deal score vs median; flag <60% of median as likely bait** | Claude 5.1 Fable | ✅ right method — and it caught that my own median was 100× wrong |

## Claims that failed

| claim | who said it | test result |
|---|---|---|
| **Kijiji RSS works** (`?rss=1`) | GLM 5.3, Claude 5.1 | ❌ **returns the same 421 KB of HTML, not RSS.** `/rss-srp-...` → **403**. The *page* works; the feed does not |
| **Craigslist RSS works** (`&format=rss`) | GLM 5.3, Claude 5.1, Claude (Latest) | ❌ **HTTP 403** |
| **Reddit `.json` / RSS works** | ChatGPT-6 Luna, Claude (Latest), GLM 5.3, Claude 5.1, Claude 5.2, Gemini 4 Neon, Kimi | ❌ `www.reddit.com` **403**; `api.reddit.com` **403**; `old.reddit.com` **200 but `text/html`** — SPA shell, 0 listings |
| **RedFlagDeals RSS works** | **Claude 5.2 Fable**, **Gemini 4 Neon** | ❌ three paths **404**; two return **HTTP 202 with a 2,926 B body and 0 `<item>`s** — a challenge page |
| **RedFlagDeals Atom feed** | **Qwen4 Max** | ✅ `/feed/forum/9` → 200, `application/atom+xml`, **15 `<entry>`**. My earlier ❌ was wrong: I tried wrong paths and counted `<item>` on an Atom feed |
| **Workday detail GET** (`externalPath`) | **Qwen4 Max** | ✅ 200, 22,515 B, keys `jobPostingInfo`/`hiringOrganization`. Two-step recipe confirmed |
| **Personio XML feed** | **Qwen4 Max** | ✅ 200, `text/xml`, 3 `<position>` parsed |
| **eBay Browse API is free/keyless** | Claude (Latest), GLM 5.3, Claude 5.2, Gemini 4 Neon | ⚠️ **403 without a token.** Free *developer account*, but a key is mandatory — "free" was read as "no setup" |
| **Best Buy's API gives local availability** | Claude 5.1, Claude 5.2, GLM 5.3, Kimi, Gemini 4 Neon | ❌ **postal-code invariant.** Nine GTA codes → identical `InStock qty=105`, `pickup: NotAvailable (0)`. National shipping flag only |
| **Lever is a quick win** | Claude (Latest), GLM 5.3, Claude 5.2, Gemini 4 Neon | ⚠️ endpoint real, **all 8 tokens I could name returned 404** — not a failure of the API, a failure to locate boards |
| **Proxies + CAPTCHA solvers + stealth are required** | **Qwen3.6 Flash**, **Kimi K2.7 Code**, **GPT-4.1 mini** | ❌ none needed. Six sources returned data with **zero** challenges. ~$80–280/mo to defeat a wall we do not have to cross |

---

## The two findings only testing produced

**1. Workday needs POST.** Claude 5.2 named the endpoint; nobody said the verb. A GET returns **HTTP 400**, which
reads as "dead endpoint". As a POST: `servicenow` 13, `salesforce developer` **301**, `apex` 199. This is the
largest enterprise ATS in the world and it was being written off because of a method mismatch.

**2. Best Buy's API is postal-invariant.** Five answers recommended it for GTA availability. It cannot do that.
The sweep is in `SOURCES.md` §B.

---

## What the pattern says

The sources that **worked** are the ones nobody presented as a scraping trick: four ATS JSON APIs, a classifieds
page with structured JSON embedded in it, and a retailer that ships its stock table in static HTML.

The sources that **failed** are almost all in one family: **"RSS is easy."** Craigslist RSS, Kijiji RSS,
RedFlagDeals RSS, Reddit RSS/JSON — every one blocked, challenged, or silently serving HTML. RSS is largely
dead in 2026 unless the operator still genuinely emits it, and a status code will not tell you which.

**The rule to carry forward:** a 200 with the wrong content type is a failure, and a 400 may mean the wrong
verb rather than a wrong URL. Both cost me a wrong entry in this very directory before they were caught.

---

## Where the advice was better than my own work

Worth recording honestly:

- **Claude 5.1 Fable** proposed a deal score against a rolling median. I had no sanity check at all, which is
  why a 100× cents/dollars error went unnoticed in my first Kijiji parse.
- **Claude 5.1 Fable** proposed `sources_status.json`. Without it a blocked source and an empty one are
  indistinguishable — the exact failure that made a cron job report "0 jobs" as success for hours.
- **Claude 5.2 Fable** caught that GitHub Actions runners use datacenter IPs, which is the real reason
  server-side scraping of these sites degrades over time.
- **GLM 5.3 Flash** was the only answer to name **SmartRecruiters** in its ATS list — the one that actually
  carried ServiceNow's 997 postings.
