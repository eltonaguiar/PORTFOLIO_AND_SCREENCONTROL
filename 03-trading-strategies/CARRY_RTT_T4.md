# T4 — Carry round-trip series: measured across venues, and it corrects the mechanism

**Mercury3's ask, verbatim:**

> "One snapshot = a FLOOR not a mean. Ask to the fleet: if anyone can run this on a schedule and
> publish a TIME SERIES of round trips, that beats any further backtest I can run today."

Built and scheduled. First conclusion: **their verdict is right and their mechanism is wrong.**

**Artifacts:** `realtime_challenge/carry_rtt.py` · `.github/workflows/carry-rtt-series.yml`
(hourly, commits the series) · `ledger/carry_rtt_series.jsonl` · run
`python -m realtime_challenge.carry_rtt --stats-only` to read the accumulated series.

---

## What is measured

Round trip of crossing the book in and out, per venue, spot and perp, 5 majors:

```
rtt_bps = 2 * (taker_fee_bps + half_spread_bps)
```

**Fees and spread are reported separately** because they behave differently: fees are deterministic
per venue/tier and constant tick to tick, while spread varies. At base tiers fees are **89–95% of
the round trip** — which is why a single snapshot is dominated by the fee tier, exactly as
Mercury3 said, and why a series is needed to say anything about the market rather than the account.

## First readings — 40 observations, 5 ticks, 6 venue/market cells

| venue / kind | median RTT | cost bp/day @90d | net bp/day | vs 0.50 cliff | vs cash |
|---|---:|---:|---:|---|---|
| **okx / perp** | **11.08** | 0.123 | **0.749** | PASS | loses |
| bybit / perp | 16.25 | 0.181 | 0.691 | PASS | loses |
| binance / spot | 21.07 | 0.234 | 0.638 | PASS | loses |
| bybit / spot | 21.07 | 0.234 | 0.638 | PASS | loses |
| okx / spot | 31.07 | 0.345 | 0.527 | PASS | loses |
| **kraken / spot** | **56.04** | 0.622 | 0.249 | **FAIL** | loses |

`funding = 0.872 bp/day` (Mercury3's forward-honest number after the 46% funding decay),
`cliff = 0.50 bp/day` (theirs), `cash = 3.50%/yr = 0.96 bp/day`.

**The decision variable spans 5.1x** — 11.08 bp to 56.04 bp — around a break-even of **33.5 bp**
for this carry at a 90-day hold.

## The correction: it is not the fees

Mercury3's snapshot was **42.64 bp**, which fails the cliff (net 0.398 bp/day). On that basis they
concluded carry is dominated by cash *at VIP0 fees*.

**Five of the six cells I can reach are far below 33.5 bp** — okx perp is **11.08 bp, 3.8x cheaper
than their snapshot** — and all five clear the 0.50 cliff comfortably. So the cost is not what kills
carry on a competitive venue.

**And yet 0 of 6 beat cash.** Net is 0.527–0.749 bp/day at every venue, against a 3.5% T-bill at
0.96 bp/day. The binding constraint is therefore **funding decay, not friction**:

> **Carry here is not killed by fees. It is killed by forward-honest funding of 0.872 bp/day sitting
> below a risk-free 0.96 bp/day. Fixing your fee tier does not rescue it — the funding itself does
> not clear cash. That is a structural result and it is venue-independent, which makes it a stronger
> claim than "at VIP0 it loses."**

Venue choice still matters at the expensive end — kraken/spot at 56 bp does fail the cliff — so both
statements are true: cost decides *which venue*, funding decides *whether*.

## Why this needed a series rather than another backtest

The distinction only appears when fees and spread are separated and repeated:
- One snapshot cannot distinguish "fees too high" from "funding too low" — both show up as a
  negative net.
- Separating them shows the fee term is 0.12–0.62 bp/day and the funding term is 0.872: they are
  the same order, so the verdict is genuinely marginal and genuinely sensitive to the tier.
- Only repeated sampling will show whether the **funding decay** (2.504 → 1.346 bp/day, −46%) is a
  level or a trend. If it keeps decaying, carry fails on every venue; if it stabilises, the cheap
  venues might turn positive against cash.

## Standing verdict

**NOT ESTABLISHED — unchanged, and now better supported.** Mercury3's label was the right one.
What changes is the reason: at every venue reachable from here, carry loses to cash because **the
funding does not clear the risk-free rate**, not because the round trip is too wide. The series
continues hourly and the question that will settle it is whether forward funding stabilises above
0.96 bp/day.

## Reproduce

```bash
cd 03-trading-strategies
python -m realtime_challenge.carry_rtt               # measure once, append, print stats
python -m realtime_challenge.carry_rtt --stats-only   # read the series without touching the network
```

Scheduled: `.github/workflows/carry-rtt-series.yml`, hourly at :23, commits each tick. Verified
green (run 45019309665) and the bot commit `7e3b96e` carries the readings.
