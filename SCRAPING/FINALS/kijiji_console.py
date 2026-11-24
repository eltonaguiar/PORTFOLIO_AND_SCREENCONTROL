#!/usr/bin/env python3
"""Kijiji GTA console listings via the page's embedded __NEXT_DATA__ JSON.

PROVEN: HTTP 200, 421,765 B, 45 listings parsed, 35 with a numeric price (2026-11-24).

Two bugs this script exists to avoid:
  * price.amount is in CENTS  -> 60000 means $600.00. Divide by 100.
  * a bare keyword search returns accessories (stands, controllers, games).
    Filter to console listings and sanity-check against an MSRP band, or the
    "cheapest listing" is always a $20 stand.

Usage:
    python kijiji_console.py                 # PS5 in the GTA
    python kijiji_console.py "xbox series x"
"""
import json
import re
import ssl
import statistics
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36",
      "Accept-Language": "en-CA,en;q=0.9"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# GTA region id on Kijiji. c37l1700272 = City of Toronto; k0l1700272 = GTA-wide.
GTA_URL = "https://www.kijiji.ca/b-gta-greater-toronto-area/{q}/k0l1700272"

# Console-plausible price band, in DOLLARS. A PS5 is not $20 and is not $80.
BAND = {"ps5": (250, 1400), "playstation": (250, 1400),
        "xbox series x": (250, 1200), "xbox series s": (120, 800)}
# Titles that are accessories, not consoles.
NEG = re.compile(r"\b(stand|controller|controller[s]?|game[s]?|disc drive|cover|faceplate|"
                 r"headset|charger|dock|skin|case|portal|remote|memory|ssd|fan)\b", re.I)
# Dealer WANTED ads: these are buyers, not sellers, and they inflate any "cheapest listing" view.
# Measured: 6 of 16 console-plausible titles were "BUYING PS5" / "TOP CASH FOR" dealer ads.
WANTED = re.compile(r"\b(buying|want(ed)?|want to buy|we buy|cash for|top cash|instant cash|"
                    r"sell your|selling your|looking for)\b", re.I)


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                  timeout=35, context=CTX).read().decode("utf-8", "replace")


def listings(html):
    """Walk the __NEXT_DATA__ Apollo graph for StandardListing nodes."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise RuntimeError("no __NEXT_DATA__ - page shape changed")
    data = json.loads(m.group(1))

    found = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.startswith("StandardListing:") and isinstance(v, dict):
                    found.append(v)
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return found


def normalize(raw):
    """-> dict with price in DOLLARS."""
    out, seen = [], set()
    for item in raw:
        i = item.get("id")
        if not i or i in seen:
            continue
        seen.add(i)
        price = item.get("price") or {}
        cents = price.get("amount") if isinstance(price, dict) else None
        loc = item.get("location") or {}
        out.append({
            "id": i,
            "title": (item.get("title") or "").strip(),
            "price_cad": round(cents / 100.0, 2) if isinstance(cents, (int, float)) else None,
            "location": str((loc.get("address") if isinstance(loc, dict) else "") or "")[:60],
            "url": "https://www.kijiji.ca/v-view-details.html?adId=%s" % i,
        })
    return out


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "ps5"
    slug = re.sub(r"\s+", "-", q.lower())
    rows = normalize(listings(fetch(GTA_URL.format(q=slug))))

    lo, hi = BAND.get(q.lower(), (100, 2000))
    plaus = [r for r in rows
             if not NEG.search(r["title"]) and r["price_cad"] and lo <= r["price_cad"] <= hi]
    consoles = [r for r in plaus if not WANTED.search(r["title"])]
    dealers = len(plaus) - len(consoles)

    print("query=%r  parsed=%d  numeric_price=%d  console_plausible=%d  seller_ads=%d (dropped %d dealer 'wanted' ads)"
          % (q, len(rows), sum(1 for r in rows if r["price_cad"]), len(plaus), len(consoles), dealers))
    if consoles:
        med = statistics.median(r["price_cad"] for r in consoles)
        print("median plausible price: $%.2f\n" % med)
        print("%-56s %-10s %s" % ("TITLE", "PRICE", "LOCATION"))
        print("-" * 104)
        for r in sorted(consoles, key=lambda x: x["price_cad"]):
            print("%-56s %-10s %s" % (r["title"][:56], "$%.2f" % r["price_cad"], r["location"]))
    print("\nNOTE: Kijiji is a classifieds board - every price here is a seller's ask,"
          " not a retailer price, and several will be bait. Verify before acting.")


if __name__ == "__main__":
    main()
