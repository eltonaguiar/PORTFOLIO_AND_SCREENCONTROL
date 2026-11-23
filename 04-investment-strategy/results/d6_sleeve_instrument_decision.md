# D6 — sleeve vs instrument decision (prediction-market calibration harness)

Item: D6 `H` — Decide and document: is this an investment sleeve (≤2%) or purely an instrument? Revisit after 50 resolved claims.
Owner: H (Hermes, Session B, cron queue axis)
Gate: G5 (evidence hygiene / provenance per INVESTMENT_DECISION_FRAMEWORK.md); G4 capital only becomes relevant at the revisit trigger
Worktree: C:/Users/zerou/pasc (github.com/eltonaguiar/PORTFOLIO_AND_SCREENCONTROL)
Run: 2026-11-23 cron, 19:05 UTC (14:05 EST)
Git hash: 5bbdee3 (HEAD; origin/main fast-forwarded f9cd013 -> 5bbdee3 this run)

## Decision

The prediction-market calibration harness (D section: "Prediction markets as a calibration harness") is **PURELY AN INSTRUMENT** — a calibration / foresight-measurement tool — and is **NOT** an investment sleeve (≤2% of capital).

This decision is recorded now and must be **revisited after 50 resolved claims** exist in the D2 ledger, per the TODO's own clause.

## Ground truth attached to this decision

- D2 ledger (`04-investment-strategy/results/d2_prediction_calibration.json`): `records: 0`. No predictions logged; the append-only JSONL ledger exists but is empty.
- D3 scoring (`04-investment-strategy/results/d3_score_latest.json`): `INSUFFICIENT_DATA` (exit 3), 0 resolved records, needs ≥5; ΔBrier vs market uncomputable, no number produced — not UNVERIFIED, not fabricated.
- D4 panel claims (AI-owned): not generated; no claims exist to resolve or score.
- D1 venue (Polymarket) selected and documented, but **no capital deployed and no positions opened** on any prediction market.
- Portfolio templates F1–F5 are not done; no sleeve exists in any template to allocate into.

## Rationale

With zero resolved claims there is no measured edge and nothing to size a sleeve against. Treating the harness as a ≤2% investment sleeve now would allocate capital to an uncalibrated, unproven mechanism — a fabricated positive by another name. The standing state of this repo is "nothing PROVEN or CANDIDATE; nothing to allocate to yet." The harness stays instrument-only: it measures whether we (and the panel) can forecast, it does not invest.

## Revisit trigger

50 resolved claims in the D2 ledger. Once that threshold is met and D3 can score ΔBrier vs market with a bootstrap 95% CI, re-decide sleeve (≤2%, sized to measured foresight) vs instrument-only on the measurement, not on this assumption.

## Artifacts referenced

- `04-investment-strategy/prediction_calibration.py` — D2 harness
- `04-investment-strategy/results/d2_prediction_calibration.json` — 0 records
- `04-investment-strategy/results/d3_score_latest.json` — INSUFFICIENT_DATA, 0 resolved
- `04-investment-strategy/results/d1_venue_selection.md` — Polymarket venue, no positions

No new number is produced by this item (documentation decision only); no COMS post is made per rule 6 (COMS only on a new or corrected measured number).
