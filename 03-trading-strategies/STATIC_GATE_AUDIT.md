# Static-gate audit — S1–S6 applied to our own harness

Date: 2026-11-22 · Subject: `03-trading-strategies/realtime_challenge/` (the peer harness we publish results from)
Gates: [`FABRICATION_CHECKLIST.md`](FABRICATION_CHECKLIST.md) §0.

Purpose: before quoting any number this harness produces, run on it the same six checks that caught seven defects
in the Claude 4.5 Opus document. A gate that is never run on your own code is decoration.

| # | Gate | Evidence | Verdict |
|---|---|---|---|
| **S1** | Causality: signal index < fill index | `engine.py:114` uses `df["close"].shift(1)` for ATR; entry at `engine.py:141-142`: `entry_bar = i + 1`, `raw_entry = o[entry_bar]`; the run attests `execution_convention="lag1_next_open"` at `engine.py:103` | **PASS** — decisions on the prior close, fills at the next open |
| **S2** | Exit ordering: high/low, stop-first | `engine.py:172-186`: `hit_sl = l[j] <= sl` / `hit_tp = h[j] >= tp` (mirrored for shorts), and the branch order is `if hit_sl: … break` **before** `if hit_tp:` with the comment *"conservative: stop wins the tie"* | **PASS** — no close-only tests, tie goes to the stop |
| **S3** | Annualisation derived, not hard-coded | `stats.py:46` `sharpe(returns, periods_per_year)` → `sqrt(periods_per_year)` at `stats.py:51`; no literal `252` anywhere in the package | **PASS** — caller supplies the period count per timeframe |
| **S4** | Trials counted and reported | `stats.py:122-153` `deflated_sharpe(..., n_trials)`; `cli.py:55` `total_trials = S.TRIAL_COUNT * len(panel)`; passed at `cli.py:86`; emitted as `"trial_count"` / `"cells"` at `cli.py:149` | **PASS** — cells × hypotheses, and the DSR consumes it |
| **S5** | Cron declared in UTC with intent | `.github/workflows/realtime-challenge.yml:27-28` — `7 * * * *` (hourly forward pod) and `20 6 * * *` (daily refresh), labelled by purpose rather than mislabelled as local time | **PASS** |
| **S6** | Workflow can land its artifact | `permissions: contents: write` at line 30-31; commit + push with retry at lines 74-82 and 121-128 | **PASS** (verified in production: `rtc: forward pod pass … [skip ci]` commits exist) |

## Two notes, not defects

1. **`trade.net_ret = gross` (`engine.py:189`)** looks wrong at a glance and is not: friction is applied inside the
   fill prices (`entry * (1 + per_side)`, `exit * (1 - per_side)`), so `gross` is already net of both legs. The
   variable name is misleading; the arithmetic is right. Verified by the harness's own cost-drag test (T2:
   25.4 bps realised vs 26 bps expected).
2. **DSR uses per-trade Sharpe**, not the annualised figure (`stats.py:62-63`), which is the correct input for a
   deflation across trades. The annualised Sharpe in the summary is reported separately and should not be
   deflated twice.

## What this means

The harness that produced the repo's published numbers passes all six static gates, and its own certification
suite (T1–T4) covers the dynamic cases the static checks cannot: look-ahead detectable, cost drag, both-touched
bar resolves to the stop, and 0/60 pure-noise cells clearing DSR 0.95.

By contrast, the reviewed documents fail as follows: Claude 4.5 Opus → S1, S2, S3, S4 (four of six); Pi.ai →
S5, S6; Claude 5.5 Haiku → S4; Qwen Plus → S1–S3 (invented prices); GLM → S1 (thesis contradicts data). The
gates were derived from those failures and are now confirmed to hold where it matters most — our own
measurements.
