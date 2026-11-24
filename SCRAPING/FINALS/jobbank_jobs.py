#!/usr/bin/env python3
"""Job Bank Canada collector WITH the context classifier that makes it usable.

PROVEN 2026-11-24: HTTP 200, 277,609 B, 25 cards per query. Intermittent
(`WinError 10054`) - retries recover it.

THE POINT OF THIS SCRIPT. Job Bank matches keywords in the DESCRIPTION, so a raw
hit count is mostly noise. Measured on 5 postings that matched "servicenow":

    business consultant (Blue Mantis)        7 mentions  -> REAL
    programmer analyst (BC Assessment)       7 mentions  -> REAL
    IT analyst (Aviso Wealth)                1 mention   -> real but secondary
    food delivery driver (EDC)               1 mention   -> FALSE POSITIVE
    food delivery driver (EDC)              1 mention   -> FALSE POSITIVE

Both false positives were the same HR boilerplate:
    "Internal Employees, please consult the ServiceNow article entitled Internal movements"

So the classifier drops mentions that sit inside HR/intranet phrasing, and then
requires >=2 surviving mentions OR one inside a requirements/skills section.

Usage:
    python jobbank_jobs.py --query servicenow --city "Toronto, ON"
    python jobbank_jobs.py --query salesforce --city "Toronto, ON" --no-details
"""
import argparse
import html as htmlmod
import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-CA,en;q=0.9",
      "Connection": "close"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# Mentions near these phrases are HR/intranet boilerplate, not skill requirements.
NOISE = re.compile(r"(internal employees?|consult the|article entitled|benefits? portal|"
                   r"employee handbook|intranet|hr portal|self-serve)", re.I)
SKILLS_HDR = re.compile(r"(requirements|qualifications|skills|must have|you will|"
                        r"responsibilities|experience)", re.I)


def fetch(url, tries=4):
    last = None
    for attempt in range(1, tries + 1):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                          timeout=45, context=CTX).read().decode("utf-8", "replace")
        except Exception as e:                      # WinError 10054 = rate limit, retry
            last = e
            time.sleep(min(3 * attempt, 15))
    raise last


def clean(fragment):
    fragment = re.sub(r"<script.*?</script>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", htmlmod.unescape(fragment)).strip()


def parse_list(page):
    out = []
    for art in re.split(r"<article ", page)[1:]:
        m = re.search(r'href="(/jobsearch/jobposting/([0-9]+)[^"]*)"', art)
        t = re.search(r'<span class="noctitle">(.*?)</span>', art, re.S)
        if not m or not t:
            continue
        title = clean(t.group(1))
        if not title:
            continue

        def li(cls):
            mm = re.search(r'<li class="%s">(.*?)</li>' % cls, art, re.S)
            return clean(mm.group(1)) if mm else ""

        out.append({"id": m.group(2), "title": title, "employer": li("business"),
                    "location": re.sub(r"^Location\s*", "", li("location")),
                    "salary": re.sub(r"^Salary\s*", "", li("salary")), "posted": li("date"),
                    "url": "https://www.jobbank.gc.ca/jobsearch/jobposting/" + m.group(2)})
    return out


def classify(title, body, keywords):
    """Return (is_match, signal, surviving_mentions)."""
    if any(k in title.lower() for k in keywords):
        return True, "keyword in TITLE", None
    if not body:
        return False, "no detail fetched (unverified)", None

    surviving = 0
    in_skills = False
    for kw in keywords:
        for m in re.finditer(re.escape(kw), body, re.I):
            window = body[max(0, m.start() - 80):m.start() + 80]
            if NOISE.search(window):
                continue                       # HR boilerplate, not a skill
            surviving += 1
            if SKILLS_HDR.search(body[max(0, m.start() - 600):m.start()]):
                in_skills = True
    if surviving >= 2 or (surviving >= 1 and in_skills):
        return True, "context-verified in description", surviving
    return False, "keyword only in boilerplate / too thin", surviving


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="servicenow")
    ap.add_argument("--city", default="Toronto, ON")
    ap.add_argument("--no-details", action="store_true",
                    help="skip detail fetches (fast, but every row is UNVERIFIED)")
    ap.add_argument("--limit", type=int, default=10, help="detail pages to fetch")
    args = ap.parse_args()

    keywords = [args.query.lower()]
    if args.query.lower() == "servicenow":
        keywords.append("service now")

    url = ("https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=%s&locationstring=%s&sort=D"
           % (urllib.parse.quote(args.query), urllib.parse.quote(args.city)))
    page = fetch(url)
    rows = parse_list(page)
    print("query=%r city=%r  list-page cards=%d  page=%dB\n" % (args.query, args.city, len(rows), len(page)))

    verified, unverified = [], []
    for i, r in enumerate(rows):
        if args.no_details or i >= args.limit:
            r["signal"] = "not fetched"
            unverified.append(r)
            continue
        try:
            detail = clean(fetch(r["url"]))
            ok, signal, n = classify(r["title"], detail, keywords)
            r["signal"] = signal
            r["mentions"] = n
            (verified if ok else unverified).append(r)
            time.sleep(2)                      # be polite; the host rate-limits
        except Exception as e:
            r["signal"] = "detail fetch failed: %s" % str(e)[:40]
            unverified.append(r)

    def show(label, items):
        print("%s (%d)" % (label, len(items)))
        if not items:
            print("  -")
            return
        print("  %-44s %-24s %-16s %s" % ("TITLE", "EMPLOYER", "LOCATION", "SIGNAL"))
        for r in items:
            print("  %-44s %-24s %-16s %s" % (r["title"][:44], r["employer"][:24],
                                              r["location"][:16], r.get("signal", "")[:34]))
        print()

    show("CONTEXT-VERIFIED", verified)
    show("UNVERIFIED / REJECTED", unverified)
    print("Precision note: without the detail-page pass every row is a keyword match only.")
    print("On a measured sample, 2 of 5 raw matches were HR boilerplate.")


if __name__ == "__main__":
    main()
