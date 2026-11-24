# FINALS — endorsed, with the evidence they actually ran

These are not proposals. Each script below was executed against the live site and produced the output quoted.
Run them from this directory; they need only the Python standard library (no pip install, no keys, no proxies).

---

## 1. `kijiji_console.py` — GTA console listings

**Proven output (2026-11-24):**

```
query='ps5'  parsed=45  numeric_price=35  console_plausible=16  seller_ads=7 (dropped 9 dealer 'wanted' ads)
median plausible price: $900.00

Ps5 original launch.                          $750.00    Scarborough, ON, M1v1r1
Ps5 selling                                   $850.00    Mississauga, ON L4W
Ps5 disc                                      $880.00    Second Line W, Mississauga, L5W 1A1
PS5 Slim                                      $900.00    Mississauga, ON L5N
PS5 Disc                                      $900.00    Mississauga, ON L5N
Ps5 Slim disc edition+ God of war Ragnarok   $1100.00    Thornhill, ON L3T 4K9
ps5 slim                                     $1200.00    Brampton, ON L6P 2J3
```

**Why it works:** the page ships `<script id="__NEXT_DATA__">` containing an Apollo graph of
`StandardListing:<id>` nodes — clean structured data. No RSS (the `?rss=1` parameter returns HTML), no JS
rendering.

**Three filters it needed, each added because the raw output was wrong:**
1. **`price.amount` is in cents** — `60000` = $600. Without `/100` the median reads **$60,000**.
2. **Accessory filter** — otherwise the "cheapest PS5" is always a $20 stand or a $50 controller.
3. **Dealer "wanted" filter** — 9 of 16 console-plausible titles were *"BUYING PS5"* / *"TOP CASH FOR"* ads.
   Those are buyers; leaving them in inverts the market.

```bash
python kijiji_console.py                 # PS5, GTA
python kijiji_console.py "xbox series x"
```

---

## 2. `ats_jobs.py` — keyless job feeds

**Proven output (2026-11-24):**

```
  greenhouse       stripe           771 jobs
  ashby            openai           863 jobs
collected=1634  selected=0
```

**`selected=0` is the correct result, not a failure.** Stripe and OpenAI are not ServiceNow/Salesforce
consultancies, so no title matches. The board did its job: 1,634 real postings, zero false positives.

Where the roles actually are, from the same test run:

| board | postings | ServiceNow/Salesforce-relevant |
|---|---:|---|
| `smartrecruiters/ServiceNow` | **997** (26 in Canada) | mostly Sales/SRE/Security; 1 `Principal Solution Architect- ServiceNow` |
| `greenhouse/gitlab` | 251 | 1 — `Release Engineer, Salesforce` |
| `greenhouse/stripe` / `datadog` / `airbnb` / `instacart` | 771 / 382 / 199 / 96 | 0 |

The plumbing works. The **supply** of these roles sits at integrators and consultancies — add their board
tokens once you know which ATS each uses (their careers page URL reveals it).

```bash
python ats_jobs.py                                   # default boards + SN/SF filter
python ats_jobs.py --all                             # everything
python ats_jobs.py --boards stripe,openai --canada-only
```

---

## 3. `jobbank_jobs.py` — Canadian job coverage, with the classifier

**Proven output (2026-11-24):**

```
query='servicenow' city='Toronto, ON'  list-page cards=25  page=277609B

CONTEXT-VERIFIED (3)
  business consultant                  Blue Mantis      Toronto (ON)   context-verified in description
  programmer analyst                   BC Assessment    Victoria (BC)  context-verified in description
  information technology (IT) analyst  Aviso Wealth     Toronto (ON)   context-verified in description

UNVERIFIED / REJECTED (22)
  food delivery driver                 Export Development Canada  Montréal (QC)  keyword only in boilerplate
  food delivery driver                 Export Development Canada  Ottawa (ON)    keyword only in boilerplate
```

**This is the whole point.** Job Bank returned 25 "ServiceNow" hits; the classifier cut it to **3 real** and
flagged the two `food delivery driver` postings that matched only on the HR sentence
*"Internal Employees, please consult the ServiceNow article entitled Internal movements"*.

**Rules implemented:** drop mentions within 80 characters of `internal employees` / `consult the` /
`article entitled`, then require **≥2 surviving mentions** or one inside a requirements/skills section.

```bash
python jobbank_jobs.py --query servicenow --limit 5
python jobbank_jobs.py --query salesforce --city "Toronto, ON"
python jobbank_jobs.py --query servicenow --no-details    # fast, but every row is UNVERIFIED
```

Retries with backoff are built in — the host resets connections (`WinError 10054`) under load.

---

## 4. Canada Computers — per-store console stock

Not shipped as a script here (it lives in
`github.com/eltonaguiar/GTA5TORONTOTRACKER/scripts/check_stock.py`), but the recipe is proven and short:

- Search: `canadacomputers.com/en/search?controller=search&s={q}` → gives `/en/{category}/{sku}/{slug}.html`
  (strip the `?keyword=...` query string — it contains spaces and raises *URL can't contain control characters*).
- Product page: HTTP 200, ~545 KB, no JS. **40 stores per SKU**, each a `data-whid="XX"` block with an address
  and a `shop-online-box` quantity.
- Downtown branch = **312 Yonge Street, Toronto, M5B 1R4**.
- Latest verdict: **all 7 console SKUs = 0 at all 40 stores**, including 312 Yonge.

---

## Endorsed with caveats — use, but never as the sole signal

| source | how to use it | the caveat |
|---|---|---|
| **Best Buy availability API** | price/availability **floor for new units** | Postal-code invariant. Nine GTA codes gave identical `InStock qty=105` and `pickup: NotAvailable (0)`. It cannot prove local stock |
| **Amazon per-ASIN browser read** | the only real per-address delivery date | Needs a browser per ASIN; read `#sellerProfileTriggerId` or a reseller markup passes as a restock |

## Corrected — previously endorsed, now eliminated

**`old.reddit.com` was listed here as a working workaround. It is not.** It returns HTTP 200 with
`Content-Type: text/html` — the Reddit SPA shell, containing **0** result cards and **0** listings. The status
code was mistaken for a result. `api.reddit.com` and `www.reddit.com` both return **403**. See
`../LESSONS.md` §9.

## Explicitly not endorsed

- **Proxies / CAPTCHA solvers / stealth plugins.** Not one external recommendation named a working endpoint;
  the free sources above returned data with no challenge at all.
- **LinkedIn scraping.** Deliberately out of scope.
- **Best Buy product pages, Craigslist RSS, `www.reddit.com` JSON, eBay without a key.** All returned 403,
  403, 403 and 403 respectively — see `../SOURCES.md` §C.
