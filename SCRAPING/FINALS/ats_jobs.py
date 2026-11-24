#!/usr/bin/env python3
"""Keyless ATS job collector: Greenhouse + Ashby + SmartRecruiters.

PROVEN 2026-11-24: greenhouse/stripe 771, ashby/openai 863, smartrecruiters/ServiceNow 997 postings
(26 in Canada). All HTTP 200, no key, no challenge.

Design notes that matter:
  * A 404 means "this company is not on this ATS" - it says nothing about the company.
    Record which ATS each employer uses; never generalise a 404.
  * Company career pages name their ATS. SmartRecruiters is where ServiceNow itself lives;
    Greenhouse/Ashby are where most tech employers live.
  * Filter on the TITLE, because these boards return clean role names (unlike Job Bank).

Usage:
    python ats_jobs.py                       # default board set, ServiceNow/Salesforce filter
    python ats_jobs.py --all                 # no keyword filter
    python ats_jobs.py --boards stripe,openai
"""
import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request

UA = {"User-Agent": "pasc-scraper/1.0 (+https://github.com/eltonaguiar/PORTFOLIO_AND_SCREENCONTROL)",
      "Accept": "application/json"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# verified-live boards, with the observed job counts on 2026-11-24
GREENHOUSE = ["stripe", "datadog", "gitlab", "coinbase", "airbnb", "instacart"]
ASHBY = ["openai", "ramp", "supabase", "linear"]
SMARTRECRUITERS = ["ServiceNow"]

KEYWORDS = ("servicenow", "service now", "salesforce", "apex", "lwc", "sfdc")


def get(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                             timeout=30, context=CTX).read().decode("utf-8", "replace"))


def from_greenhouse(board):
    d = get("https://boards-api.greenhouse.io/v1/boards/%s/jobs" % board)
    for j in d.get("jobs") or []:
        yield {"source": "greenhouse/%s" % board,
               "title": j.get("title") or "",
               "company": board,
               "location": (j.get("location") or {}).get("name") or "",
               "url": j.get("absolute_url") or ""}


def from_ashby(org):
    d = get("https://api.ashbyhq.com/posting-api/job-board/%s" % org)
    for j in d.get("jobs") or []:
        yield {"source": "ashby/%s" % org,
               "title": j.get("title") or "",
               "company": org,
               "location": str(j.get("location") or ""),
               "url": j.get("jobUrl") or j.get("applyUrl") or ""}


def from_smartrecruiters(company, pages=12):
    for page in range(pages):
        d = get("https://api.smartrecruiters.com/v1/companies/%s/postings?limit=100&offset=%d"
                % (company, page * 100))
        batch = d.get("content") or []
        for j in batch:
            loc = j.get("location") or {}
            yield {"source": "smartrecruiters/%s" % company,
                   "title": j.get("name") or "",
                   "company": company,
                   "location": ", ".join(x for x in (loc.get("city"), loc.get("country")) if x),
                   "country": (loc.get("country") or "").lower(),
                   "url": "https://jobs.smartrecruiters.com/%s/%s" % (company, j.get("id"))}
        if len(batch) < 100:
            return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="skip the keyword filter")
    ap.add_argument("--boards", help="comma list of board tokens to use instead of defaults")
    ap.add_argument("--canada-only", action="store_true", help="filter to country=ca")
    args = ap.parse_args()

    rows, errors = [], []
    todo = [("greenhouse", b, from_greenhouse) for b in GREENHOUSE]
    todo += [("ashby", b, from_ashby) for b in ASHBY]
    todo += [("smartrecruiters", b, from_smartrecruiters) for b in SMARTRECRUITERS]
    if args.boards:
        wanted = {b.strip() for b in args.boards.split(",")}
        todo = [t for t in todo if t[1] in wanted]

    for kind, token, fn in todo:
        try:
            got = list(fn(token))
            rows += got
            print("  %-16s %-14s %5d jobs" % (kind, token, len(got)))
        except urllib.error.HTTPError as e:
            errors.append("%s/%s HTTP %s" % (kind, token, e.code))
            print("  %-16s %-14s HTTP %s (not on this ATS)" % (kind, token, e.code))
        except Exception as e:
            errors.append("%s/%s %s" % (kind, token, str(e)[:60]))
            print("  %-16s %-14s FAIL %s" % (kind, token, str(e)[:50]))

    sel = rows
    if not args.all:
        sel = [r for r in sel if any(k in r["title"].lower() for k in KEYWORDS)]
    if args.canada_only:
        sel = [r for r in sel if r.get("country") == "ca"]

    print("\ncollected=%d  selected=%d" % (len(rows), len(sel)))
    print("\n%-62s %-22s %s" % ("TITLE", "COMPANY", "LOCATION"))
    print("-" * 108)
    for r in sel[:40]:
        print("%-62s %-22s %s" % (r["title"][:62], r["company"][:22], r["location"][:22]))

    if errors:
        print("\nFAILURES (recorded, not hidden): %s" % "; ".join(errors))
    print("\nNote: a 404 above means that company does not use that ATS - it is a routing fact,")
    print("not a judgement about the company or the endpoint.")


if __name__ == "__main__":
    main()
