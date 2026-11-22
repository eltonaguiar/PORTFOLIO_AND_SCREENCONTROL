# Investment Hub review — what to copy into audit2 / audit3, and what to refuse

Source: `https://findtorontoevents.ca/investments/` and `/investments/all-dashboards.html`, read
2026-11-22. Purpose: the hub is a **prediction** surface (115+ algorithms, 7 alt-data families, real
broker fees, SHA-256 pre-commitment); audit2/audit3 are the **tribunal** (selection alpha, cost,
multiplicity, kill list). The question is not "which hub page looks good" but "which concept gives the
tribunal a capability it does not already have".

## The structural mismatch, stated first

The hub optimises for **coverage**: 115+ algorithms across 30+ families, 40+ dashboards, 19 ML models.
The tribunal optimises for **falsification**: 67 tested cells, 0 proven, 10 kill, most `insufficient`.

That means the hub's headline asset is the tribunal's headline liability. **115 algorithms is 115
trials**, and any single winner selected from them needs a deflated Sharpe computed with N ≈ 115, not
N = 1. Copying hub *results* into audit3 without importing the trial count would manufacture
significance — the exact failure that produced the fake Sharpe 1.83 and the fabricated 41.05 bp round
trip elsewhere in this programme.

So: copy **mechanisms**, never verdicts.

## Worth copying — ranked by what it unlocks

### 1. SHA-256 pre-commitment of picks — HIGH value, lowest risk
The hub already hashes picks before the outcome exists ("SHA-256 verified", "pre-commitment protocol
for trust"). audit3 has **no forward pre-registration lock**: hypotheses are registered, but nothing
makes it impossible to revise a rule after seeing a bar.

Copy as: on registration, store `hypothesis_sha256` over the canonical JSON of `entry / exit / sizing /
costs / universe / horizon`, plus `committed_at`. Any post-hoc revision becomes a **new hash**, so
"revised the rule" is visible in the ledger instead of invisible. This is the cheapest possible upgrade
to forward credibility and it requires no new data.

### 2. Broker-realistic fee model (Questrade Canada + CDR detection) — HIGH
The hub backtests with "realistic Questrade Canada fees" and detects CDR instruments for
commission-free trading. audit3 currently applies a **per-class slippage** figure (CRYPTO 0.0996%,
COMMODITY 0.15%, EQUITY/ETF/BOND 0.05%, FOREX 0.02%, FUTURES 0.10%, MUTUAL_FUND 0.08%) but not a
**commission schedule**.

Why it matters: our whole conclusion is "gross edge ≈ round-trip cost". A cost model with commissions
+ ECN fees + FX conversion + the CDR zero-commission case changes which cells clear 2× cost, and it
does so in a way that is *checkable* rather than assumed. Also note the hub's mutual-fund side adds
front/back loads and Questrade's $9.95 MF fee — the only place in the estate where a fund class has a
cost model at all.

### 3. Turnover budget as a first-class column (from the $500/day and day-trader sims) — HIGH
Both sims force an explicit turnover. audit3 has no turnover column, so a cell can "win" while being
untradeable. Add `turnover_per_year` and `cost_at_realistic_turnover` to every row; a cell whose edge
only exists at 40×/yr turnover is a cost artefact, not an edge.

### 4. Horizon as a first-class dimension (from Horizon Picks) — MEDIUM-HIGH
The hub ships 1D / 1W / 1M picks. Our own cost-horizon ladder says the same thing from the other side:
**+24.21 bp at 1D vs −0.57 bp at 15m** (Copilot seat, 2026-11-22). Any real edge must live at daily or
longer horizons, so horizon belongs in the cell key, not in the notes.

### 5. VIX filter + regime engine — MEDIUM, with a hard condition
Regime conditioning is legitimate *if regimes are pre-registered*. It is data mining if regimes are
chosen by scanning for the best partition. Copy the mechanism, and count **each regime as a trial** in
the DSR N; otherwise "we only trade in risk-on" becomes a free parameter that fits any history.

### 6. The seven alt-data families — MEDIUM, point-in-time or nothing
Glassdoor, BDI, GPR, Dark Pool, ESG, Patents, Congressional. Genuinely new evidence sources for
classes where we have none. The trap is **publication lag**: Congressional disclosures, patent grants
and ESG scores all publish *after* the fact, so a naive join is look-ahead bias with a paper trail.
Require, per family: `as_of_date` distinct from `event_date`, and a stated lag. Refuse any family that
cannot produce both.

### 7. NAV-based fund backtesting — MEDIUM
Fills the MUTUAL_FUND class, which currently has ~zero evidence. But note the arithmetic before
building: a 2% front load plus 0.5%/yr MER is an unrecoverable cost for any monthly strategy, so the
only defensible fund tests are no-load index funds held long. Worth doing precisely because it is
likely to **kill** rather than promote.

## Refuse to copy

| Concept | Why not |
|---|---|
| **"Optimal condition finding"** | This is automated data mining by another name. Without a pre-registered condition and a trial counter it will always find a combination that fits. Copying it into the tribunal would make the tribunal the mining engine. |
| **115+ algorithms as candidates** | Each one is a trial. Importing the list imports the multiplicity. If audit3 must ingest hub outputs, it needs the trial count attached to every row. |
| **Any hub metric without its trial count** | Non-negotiable. A win rate with no N is not evidence; a Sharpe with no N is a rumour. |
| **Smart Learning / "stock intel" prose** | Narrative, not testable. |
| **Goldmine-style curated lists** | Selection performed by a human on realised winners is survivorship by construction — the same defect already documented for the fund universe. |

## Concrete next actions (small, ordered)

1. Add `hypothesis_sha256` + `committed_at` to the registry; reject a row whose recomputed hash differs
   without a `revision_of` pointer.
2. Add `turnover_per_year` and `commission_model` columns; recompute the 67 cells under the Questrade
   schedule and report how many still clear 2× cost.
3. Move `horizon` into the cell key (1D/1W/1M) so the ladder is visible per cell.
4. Ingest **one** alt-data family end-to-end with `as_of_date` discipline (recommend Congressional —
   it has a legally mandated disclosure date), and report it as a new hypothesis, not a new dashboard.
5. Leave "optimal condition finding" out of the tribunal entirely. If it is used upstream, its output
   must arrive as a hypothesis with a hash, not as a result.

## Evidence class

Observed: the hub's feature list, page inventory, fee/cost language and SHA-256 claim, read from
`/investments/` and `/investments/all-dashboards.html` on 2026-11-22. Observed: audit3's structure
(67 cells, 0 proven, kill list, evidence registry) from the live page and `audit3_ledger.json`.
Derived: the multiplicity argument (115 algorithms ⇒ N ≈ 115) and the mutual-fund fee arithmetic.
Judgement: the copy/refuse ranking. Nothing here is a recommendation to trade.
