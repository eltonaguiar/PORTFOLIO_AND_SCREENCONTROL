# SOURCES — every endpoint probed, with the result

All tests run 2026-11-24 between 03:45 and 04:20 EST. Status is the HTTP code actually returned; payload is the
byte size actually received.

## A. Job sources

### Greenhouse (public JSON, no key) — **WORKS**

```
https://boards-api.greenhouse.io/v1/boards/{board}/jobs
```

| board token | HTTP | jobs | verdict |
|---|---:|---:|---|
| `stripe` | 200 | **771** | ✅ |
| `datadog` | 200 | **382** | ✅ |
| `gitlab` | 200 | **251** | ✅ |
| `coinbase` | 200 | **249** | ✅ |
| `airbnb` | 200 | **199** | ✅ |
| `instacart` | 200 | **96** | ✅ |
| `salesforce` | 404 | 0 | ❌ not on Greenhouse |
| `servicenow` | 404 | 0 | ❌ not on Greenhouse |
| `shopify` | 404 | 0 | ❌ not on Greenhouse |
| `doordash` | 404 | 0 | ❌ not on Greenhouse |

A 404 means *that company does not use this ATS* — it says nothing about the company or the endpoint.

### Ashby (public JSON, no key) — **WORKS**

```
https://api.ashbyhq.com/posting-api/job-board/{org}
```

| org | HTTP | jobs |
|---|---:|---:|
| `openai` | 200 | **863** |
| `ramp` | 200 | **180** |
| `supabase` | 200 | **81** |
| `linear` | 200 | **30** |
| `vercel` | 200 | **0** (board exists, empty) |
| `anthropic` | 404 | 0 |

### SmartRecruiters (public JSON, no key) — **WORKS, and this is where ServiceNow actually is**

```
https://api.smartrecruiters.com/v1/companies/{company}/postings?limit=100&offset={n}
```

| company | HTTP | result |
|---|---:|---|
| **ServiceNow** | 200 | **997 postings total; 26 in Canada** |
| Ubisoft | 200 | 0 |
| Visa | 200 | 0 |
| Deloitte | 200 | 0 |

**ServiceNow's own board, Canada breakdown (26):** 19 Toronto, 4 Montreal, 1 Vancouver, 2 bilingual duplicates.
Composition is **Sales, SRE, Security, Compliance, Product** — plus one `Principal Solution Architect- ServiceNow`.
**No ServiceNow developer / admin / platform roles in the GTA.** The titles you want are at integrators and
consultancies, not at the vendor.

### Lever — **NOT LOCATED**

```
https://api.lever.co/v0/postings/{company}?mode=json
```
All eight tokens tried (`shopify`, `netflix`, `plaid`, `brex`, `ramp`, `mistral`, `openai`, `anthropic`) returned
**404**. The endpoint is real; these tokens are wrong. Not evidence the API is dead.

### Workable — **ZERO**

`https://apply.workable.com/api/v1/widget/accounts/{token}?details=false` returned HTTP 200 with **0 jobs** for
`shopify`, `canonical`, `automattic`. Either the tokens are wrong or the widget API changed shape.

### Job Bank Canada (Government of Canada, public) — **WORKS but noisy**

```
https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={q}&locationstring=Toronto%2C+ON&sort=D
```

- HTTP **200**, **277,609 B**, **25 job cards per query**.
- Markup: `<article>` → `<span class="noctitle">` (title), `<li class="business">` (employer),
  `<li class="location">`, `<li class="salary">`, `<li class="date">`.
- **Intermittent:** one request was reset (`WinError 10054`). Retry with backoff; it succeeded on attempt 1 or 2.
- **Precision problem:** keyword search matches the *description*, not the title. See `LESSONS.md` §2.

## B. Console / retail sources

### Canada Computers (static HTML) — **WORKS, best local signal**

```
https://www.canadacomputers.com/en/search?controller=search&s={q}      # SKU discovery
https://www.canadacomputers.com/en/{category}/{sku}/{slug}.html        # per-store stock
```

- HTTP 200, **545 KB**, no JS required.
- **40 stores parsed per SKU**, each as a `data-whid="XX"` block with an address and a `shop-online-box` quantity.
- Toronto Downtown = `312 Yonge Street, Toronto, Ontario, M5B 1R4`.
- Result 2026-11-24: **all 7 console SKUs = 0 at all 40 stores**, including 312 Yonge.
- **Strip the query string** from search-result URLs before fetching — a raw `?keyword=xbox series x` contains
  spaces and raises `URL can't contain control characters`.

### Kijiji (GTA classifieds) — **WORKS via embedded JSON**

```
https://www.kijiji.ca/b-gta-greater-toronto-area/ps5/k0l1700272
```

- HTTP **200**, **421,765 B**.
- `?rss=1` returns **the same HTML, not RSS** — the RSS feed is gone. The page itself is what works.
- Contains `<script id="__NEXT_DATA__">` with an Apollo state graph: keys `StandardListing:<id>` carrying
  `title`, `description`, `imageUrls`, `price.amount`, `location.address`.
- **45 listings parsed, 35 with a numeric price.**
- ⚠️ **`price.amount` is in CENTS.** `60000` means **$600.00**. See `LESSONS.md` §3.
- The string `captcha` appears in the page source but did **not** indicate a challenge — the data was present.

### Workday CXS — **WORKS, but only with POST**

```
POST https://{tenant}.wd{n}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
body: {"appliedFacets":{},"limit":20,"offset":0,"searchText":"{q}"}
headers: Content-Type: application/json
```

A plain **GET returns HTTP 400** — which is why Workday looked dead on the first pass. As a POST:

```
salesforce.wd12.myworkdayjobs.com/.../External_Career_Site/jobs
  "servicenow"            -> HTTP 200, total 13
  "salesforce developer"  -> HTTP 200, total 301   ("Salesforce Technical Architect", 5 locations, Posted Today)
  "apex"                  -> HTTP 200, total 199
```

This is the largest enterprise ATS in the world, and it answers politely once the verb is right.
Response carries `jobPostings[].title`, `.locationsText`, `.postedOn`, `.externalPath`.

**Lesson:** a 400/404 on a JSON endpoint can mean *wrong method*, not *wrong endpoint*. Always try POST.

### RedFlagDeals — **BLOCKED (challenge)**

`/feed/hot-deals/`, `/feed/`, `/rss/hot-deals/` → **404**. `/feeds/hot_deals/` and `/deals/feed/` → **HTTP 202
with a 2,926 B body and 0 `<item>` elements** — a challenge page, not a feed. Effectively blocked.

### Recruitee — **not located**

`https://api.recruitee.com/c/{company}/careers/` → **404** on the token tried. Endpoint shape unverified.

### Reddit — **DOES NOT WORK AS JSON (corrected)**

| request | result |
|---|---|
| `www.reddit.com/r/{sub}/search.json` | **403 Blocked** |
| `old.reddit.com/r/{sub}/search.json` | **200 — but `Content-Type: text/html`, 342,840 B** |
| `api.reddit.com/r/{sub}/search` | **403 Blocked** |

> **Correction.** An earlier version of this file called `old.reddit.com` a working workaround. It is not.
> The 200 body is the Reddit SPA shell: `is JSON? False`, **0** `class="thing"` cards, **0** search-result
> links. It returns a page with no listings in it. Same for `/search` without the `.json` suffix.
>
> The mistake was recording the **status code** as the verdict. A 200 with the wrong content type is a
> failure — see `LESSONS.md` §8, which this file's author then violated.

### Best Buy Canada — **API works, product pages do not**

**Availability API (200):**
```
https://www.bestbuy.ca/ecomm-api/availability/products
  ?accept=application%2Fvnd.bestbuy.standardproduct.v1%2Bjson
  &accept-language=en-CA&skus={sku}&postalCode={A1A1A1}
```
**Search API (200):** `https://www.bestbuy.ca/api/v2/json/search?query={q}&lang=en-CA&pageSize=20`

**Product pages (BLOCKED):** `https://www.bestbuy.ca/en-ca/product/...` → **HTTP 200 with title `🐴 Access Denied`**
(Akamai). A real Chrome does not change this.

**Postal-code sweep — the finding that matters.** Xbox Series S 512GB (`sku 19422130`), nine GTA codes:

| postal | area | shipping | qty | pickup |
|---|---|---|---:|---|
| M5G1L7 | Downtown TO | InStock | 105 | NotAvailable (0) |
| M5V2T6 | King West | InStock | 105 | NotAvailable (0) |
| M6J1R1 | Parkdale | InStock | 105 | NotAvailable (0) |
| M4C1A1 | East York | InStock | 105 | NotAvailable (0) |
| L4K1A1 | Vaughan | InStock | 105 | NotAvailable (0) |
| L5B1A1 | Mississauga | InStock | 105 | NotAvailable (0) |
| L3R0A1 | Markham | InStock | 105 | NotAvailable (0) |
| M1B0A1 | Scarborough | InStock | 105 | NotAvailable (0) |
| L6H0A1 | Oakville | InStock | 105 | NotAvailable (0) |

**Identical everywhere.** The endpoint is a national shipping flag; `pickup.locations` is always empty.
**It cannot prove GTA availability.**

### Amazon.ca — **WORKS in a real browser**

Per-ASIN page read: `#productTitle`, `.a-price .a-offscreen`, `#availability`, `#add-to-cart-button`,
`#mir-layout-DELIVERY_BLOCK`, `#sellerProfileTriggerId`.

| ASIN | shown | reading |
|---|---|---|
| `B0FLL9VRL5` Series S 512GB | "In Stock", ATC present, $649.96, fastest Nov 25 | ✅ **genuinely buyable** |
| `B0BMXVWSD6` Series X 1TB | "Only 2 left", $1,299.50, **sold by `CCJamesInc`**, no visible ATC | ⚠️ marketplace markup |
| `B0BCSYVXGL` PS5 Disc | "Only 1 left", no price, no ATC | ⚠️ unconfirmed |
| `B0FRGMYJMG` / `B0CL7RQRY9` / `B0CL7NKBBL` PS5 | $129.98 / $229.99, empty availability | ⛔ **dead listings** |

## C. Blocked — recorded, not retried

| source | result |
|---|---|
| **Craigslist Toronto RSS** (`?format=rss`) | **403** |
| **`www.reddit.com` JSON** | **403 Blocked** |
| **eBay Browse API** without a token | **403** (needs a free developer key) |
| **Best Buy product pages** | Akamai `🐴 Access Denied` |
| Walmart.ca | `Forbidden` (per prior probe) |
| Staples / EB Games / Memory Express | Cloudflare Turnstile |
| LinkedIn | not attempted — deliberately out of scope |

## D. Keyless-claim audit

Four of these were recommended by external advice as "no key needed". Tested:

| recommendation | claimed | actual |
|---|---|---|
| Craigslist RSS | keyless | **403** |
| Reddit `.json` | keyless | **403** on `www`; 200 on `old` |
| eBay Browse API | free key | 403 without a token — a key is mandatory |
| Kijiji RSS | `?rss=1` works | returns HTML; the **`__NEXT_DATA__` JSON** is the real target |
