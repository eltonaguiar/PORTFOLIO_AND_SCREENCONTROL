# Auto-expired rows are their own resolution class — schema spec (B1)

**Status:** local spec delivered (this is B1's definition-of-done: "written spec in `03-*/` even if the upstream
fix lands elsewhere"). The resolver **code** lives in `findtorontoevents.ca` and is fleet-owned; applying the
change there is a separate upstream task, blocked on that repo. Nothing in this document has been applied to any
live ledger — it is a contract for the fix.

---

## 1. The defect

The auto-resolver stamps a pick whose window closes **without touching take-profit or stop-loss** in a way that
scores it as **neither a win nor a loss** — in practice it collapses to `0` (or is silently dropped from the class
average). That makes "the price did not reach a trigger inside the window" indistinguishable from "the price ended
exactly where it started", which is almost never true.

Two independent scans of the same defect, from different populations:

| source | observation |
|---|---|
| audit3 live ledger (`02-portfolio-multi-asset/CAPITAL_ALLOCATION.md` §5.4) | **9,277 auto-expired rows score as neither win nor loss**, "so a wide-TP strategy escapes judgement forever." |
| harvest tracker (`42_HARVEST_UPGRADE_2026-11-24/tracker/DEFECT_RESOLVER_CLASS_CONFOUND`, as recorded in `01-screen-control-llm/hyper_keeper.py`) | `TIME_EXPIRED` **29,505 rows, 28,430 of them zero (96.4 %)**; `SL_HIT` **0 of 18,534** zero; `TP_HIT` **2 of 12,448** zero. A further **2,906 EXPIRED rows** do not join to the older table. |

### Why this is a scoring artifact, not a natural terminal state

If a `0` return were a genuine market outcome (expiry price exactly equals entry), zeros would be spread across
**every** class. Instead they are ~exclusively in `TIME_EXPIRED` (96.4 % there, ~0 % in `SL_HIT`, 0.02 % in
`TP_HIT`). The zero-concentration is created by the **expiry branch of the resolver**, not by the market. A pick
that timed out is a distinct outcome and must be recorded as one.

---

## 2. Failure mode the change fixes

1. **Zero-inflation of the binary class.** Expired rows are counted in the population but contribute `0`, dragging
   mean-return and hit-rate toward zero for every strategy that produces timeouts.
2. **Wide-TP strategies escape judgement.** A rare-hit, wide-take-profit strategy produces many timeouts and few
   TP/SL touches. Scored as "neither", it never accumulates enough win/loss rows to be judged — it hides in the
   neutral bucket forever. A tight-TP strategy on the same data is judged only on its hits. Cross-class comparison
   becomes invalid.
3. **Denominator ambiguity.** "Neither win nor loss" rows inflate the population while contributing nothing, so
   profit factor and hit-rate computed over different strategies are not comparable — the denominator is not
   stated per class.
4. **Sign error on the edge.** Every resolved row still pays the round-turn cost. A timeout scored `0` gross is
   really **≈ −cost** (≈ −26 bp at this repo's default 26 bp round turn). Reporting it as `0` flips a small loss
   into a flat outcome and overstates expectancy.
5. **Silent data loss.** The 2,906 `EXPIRED` rows that fail to join are dropped entirely, so the class average is
   computed on a subsample with no record of what was excluded.

---

## 3. Schema change (proposed)

### 3.1 Resolver output — an explicit `resolution_class`

Add a field independent of the existing binary `resolution`:

| `resolution_class` | meaning | `resolution` | `realized_bp` |
|---|---|---|---|
| `OPEN` | position still live | `null` | `null` |
| `TP_HIT` | take-profit touched inside the window | `1` | signed bp to the TP fill |
| `SL_HIT` | stop touched inside the window | `0` | signed bp to the SL fill |
| `TIME_EXPIRED` | window closed, neither touched | `null` (kept out of win/loss) | **mark-to-market at expiry** (never a default `0.0`) |
| `VOID` | data-integrity exclusion (ghost row, WON-vs-PnL contradiction, unjoinable, no resolvable price) | `null` | `null` |

The key rule: **`TIME_EXPIRED` is not a loss and not a zero.** It keeps `resolution = null` so it does not
pollute the binary win/loss class, but it **does** carry a `realized_bp` — the signed return from `entry_price` to
the last tradeable price at the window close. A timeout with no sourceable price becomes `VOID`, not `TIME_EXPIRED
= 0`.

### 3.2 Field additions (JSON, for the resolver row and for `picks_schema.json`)

```json
{
  "resolution_class": { "enum": ["OPEN", "TP_HIT", "SL_HIT", "TIME_EXPIRED", "VOID"] },
  "expiry_price":      { "type": ["number", "null"], "description": "Last tradeable price at window close; the mark for a TIME_EXPIRED row." },
  "expiry_utc":        { "type": ["string", "null"], "format": "date-time" },
  "realized_bp":       { "type": ["number", "null"], "description": "Signed P&L in bp. For TIME_EXPIRED = mark at expiry vs entry; MUST NOT default to 0.0." }
}
```

Invariants the resolver must enforce:

- `resolution_class == "TIME_EXPIRED"` ⇒ `resolution == null` **and** (`realized_bp` is non-null **or** the row is
  re-classed `VOID`). A `TIME_EXPIRED` row with `realized_bp == 0.0` and `expiry_price` far from `entry_price` is
  forbidden.
- `resolution_class in {"TP_HIT","SL_HIT"}` ⇒ `resolution ∈ {1,0}` respectively.
- `VOID` rows are counted and reported separately; they never enter a win-rate denominator.

### 3.3 Class-average semantics

- **Win-rate denominator** = `TP_HIT + SL_HIT` only (the binary class). State it explicitly per table.
- **Mean-return / expectancy** = all resolved rows (`TP_HIT + SL_HIT + TIME_EXPIRED`) using `realized_bp`
  (timeouts use their mark, not `0`), with round-turn cost charged to every row.
- **Report the timeout share** explicitly: `timeout_share = TIME_EXPIRED / (TP_HIT + SL_HIT + TIME_EXPIRED)`, so a
  wide-TP strategy is visible rather than neutralised.
- **VOID share** reported alongside, so the dropped-row count (currently 2,906) is never silent.

---

## 4. Mapping to this repo

- **`03-trading-strategies/picks_schema.json` (E1)** currently models `resolution` as `1 | 0 | null` with
  `status ∈ {open, closed, killed, superseded}` and no expiry class. It should gain `resolution_class`,
  `expiry_price`, `expiry_utc` per §3.2 so local paper books reconcile with the upstream ledger. The schema is
  **append-only** (`additionalProperties: false`, "rows are inserted once and never edited"): historical rows are
  re-classified at **read time** by resolver branch, never edited in place (E7).
- **`04-investment-strategy/paper_book.py` (E6)** already does the right thing for local books: a `time_based`
  pick past `max_hold_days` is booked as a **killed row at the snapshot price** — i.e. it stores a *mark*, not a
  zero. Verified end to end: `time_based 200 max_hold 1 expired → killed at 90 → −5,500 bp`
  (`03-trading-strategies/PROGRESS.md`, E6). **This is the pattern to port upstream:** timeout = marked-to-market
  return with the cost charged, not `0`.
- No file under `03-trading-strategies/results/` or `ledger/` is touched by this spec; those are sibling-owned.

---

## 5. Verification / acceptance (for the upstream fix, wherever it lands)

1. **Per-class zero rate after deploy:** `TIME_EXPIRED` zero-rate falls from ≈ 96.4 % to the same order as
   `TP_HIT`/`SL_HIT` (< 1 %), because timeouts now carry a mark.
2. **Mark coverage:** `realized_bp` non-null rate on `TIME_EXPIRED` ≥ 99 %; the remainder are `VOID`, counted
   separately (must not exceed the prior 2,906 unjoined rows without an explanation).
3. **Known wide-TP strategy moves:** its expectancy shifts from ≈ 0 (neutral bucket) to its true net-of-cost
   value once timeouts are marked. A wide-TP strategy that was "flat forever" must now show a sign.
4. **Denominators documented:** every leaderboard states `TP_HIT`, `SL_HIT`, `TIME_EXPIRED`, `VOID` counts, and
   the win-rate denominator is `TP_HIT + SL_HIT` for all compared strategies.
5. **No unresolved growth:** the `OPEN` count is unchanged by the migration (re-classification touches resolved
   rows only).
6. **Cost floor honoured:** a table summing `realized_bp` over resolved rows shows a negative floor ≈ −round-turn
   cost per timeout; if it sums to exactly `0` for a batch of timeouts, the default-zero bug is still present.

---

## 6. What remains blocked upstream

The resolver code is in `findtorontoevents.ca` (fleet-owned; a request was raised on COMS). This repo cannot edit
it. This document satisfies B1's **local** DoD — a written spec of the schema change and the failure mode it fixes
— without pretending the upstream fix is done. Applying §3 to the upstream resolver is the separate, fleet-owned
task.
