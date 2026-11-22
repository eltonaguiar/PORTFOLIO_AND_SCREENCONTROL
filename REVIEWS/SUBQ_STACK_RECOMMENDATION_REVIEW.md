# Review — Subq stack recommendation (Windows agent + backtesting), 2026-11-22

Input: a supplied note from "Subq" (~3.8k tokens) recommending a complete Windows agent /
screen-control / backtesting stack for this repository's two topics.

Audited the same day: every repository claim checked through the GitHub API
(stars / last push / licence / archived), and the note's one quantitative performance claim
**tested against this repo's own measured trades**.

**Verdict: the agent/desktop half is largely right and usefully specific; the backtesting
half repeats two stale-engine recommendations it should have caught, and its one number —
"combining strategies improved risk-adjusted returns by 30-50%" — does not reproduce on this
book. Measured here: combining made it *worse*, because diversification cannot manufacture
an edge that four of the six components do not have.**

---

## 1. Repository claims, checked

| note's claim | verdict | GitHub API, 2026-11-22 |
|---|---|---|
| `vercel-labs/agent-desktop`, Apache-2.0, CLI + C library, accessibility tree → JSON refs | ✅ **accurate** | 26,040★, Apache-2.0, last push 2026-11-21 |
| `BrowserMCP/mcp` — connects agents to the user's real browser with existing logins | ✅ **accurate** | 7,398★, Apache-2.0, last push 2026-11-12 |
| Windows-MCP — "the most adopted Windows desktop MCP server at **~6,750 stars**", MIT, UIA tree, 0.2–0.9 s | ⚠️ **real but the star count is wrong** | `CursorTouch/Windows-MCP` — **11,999★**, MIT, pushed 2026-11-22. It *is* the most adopted; it is ~78% bigger than stated |
| `thisnick/agent-rdp` — IronRDP CLI, PowerShell agent over a dynamic virtual channel | ✅ accurate, but presented as a **stack pick** | 28★, Apache-2.0, last push 2026-02-26. A 28-star experimental repo is a probe, not a member of a decided stack |
| **Backtrader** for "realistic validation" | ❌ **stale, and the note does not say so** | `mementum/backtrader` — GPL-3.0, 23,776★, **last push 2024-08-19**. Two years and three months without a commit. It runs; nobody fixes bugs. Recommending it as *the* validation layer is the same defect this note criticises elsewhere |
| **QSTrader** for the portfolio layer | ❌ **stale, undisclosed** | `mhallsmoore/qstrader` — MIT, 3,491★, **last push 2024-06-30**. Two years and five months |
| **OptimalPortfolios** for construction | ⚠️ real and maintained, but **99★** | `ArturSepp/OptimalPortfolios` — MIT, 99★, last push 2026-11-19. Research code, not a supported library. Fine to read, thin to depend on |
| **bt** for the allocation layer | ✅ **accurate** | `pmorissette/bt` — MIT, 3,045★, last push 2026-11-20 |
| **vectorbt** for sweeps | ✅ **accurate** and agrees with `LIBRARY_SURVEY.md` | 9,911★, last push 2026-11-11 |
| **Workroom** plugin, byte-identical Office files | 🟡 **unverifiable from here** | no GitHub repository found under `lobehub/workroom` or by search; it is a Hermes-plugin-side artifact. Its published evidence may well be real — this audit cannot confirm it, so it is marked unverified rather than repeated |
| Data tiers (Twelve Data 800/day, Alpha Vantage 25/day, Tiingo 1,000/day, Finnhub 60/min) | 🟡 **unverified** | these are account-tier numbers; they cannot be checked without a key. Recorded as the note's claim, not as this repo's finding |

## 2. Where the note is right, and this repo already agrees

- **"OHLCV deliberately discards intrabar ordering, spread and depth, so a stop and a target
  hit in the same bar cannot be sequenced correctly."** Correct, and it is certification
  test **T3** here: a bar touching both resolves to the **stop**, always, because resolving
  it as a win is inventing one.
- **"A multi-asset run tests rules independently per symbol; a portfolio run has one cash
  account where holdings compete for the money bar by bar. You want both."** Correct, and it
  is a **real gap in this harness**, now owned: `realtime_challenge` sizes each symbol
  independently and has no shared cash constraint. Mitigated partly by the forward pod's
  `max_open = 4` cap, but a per-bar shared-cash simulation is still missing (roadmap P5,
  R157–R160).
- **"Parameter stability across neighbouring settings matters more than the single best
  Sharpe; read sweeps as heatmaps, not winners."** Agrees with the pre-registration rule
  here, and with the roadmap's "prefer plateaus to peaks".
- **Tree-first, vision-fallback** matches `01-screen-control-llm/`'s reliability ladder and
  the implementation's accessibility-tree transport.

## 3. The number that does not reproduce

The note states: *"Combining strategies into one portfolio improved risk-adjusted returns by
30–50% versus single-strategy approaches in the cited research."*

That is testable here, on trades this harness measured, so it was tested —
`realtime_challenge/proof/portfolio_combination.py`, artifact
`results/portfolio_combination.json`. Six hypotheses on 1d bars, 7 majors, 3.3 years,
26 bps round turn, daily mark-to-market (**a flat day earns 0.0%, not "no observation"**),
combined as equal capital across strategies.

| book | total return | **Sharpe** | max DD | ann vol | days in market |
|---|---:|---:|---:|---:|---:|
| buy & hold, equal weight | **+51.57%** | **0.519** | −70.6% | 65.1% | 99.9% |
| H-R4 vol_compression (best single) | +5.12% | **0.243** | −8.8% | 7.4% | 16.9% |
| H-R2 donchian_breakout | +4.74% | 0.169 | −31.6% | 17.9% | 64.3% |
| **COMBINED equal weight** | **−2.27%** | **−0.123** | −8.0% | 4.7% | 82.0% |
| H-R1 trend_pullback | −2.32% | −0.157 | −7.8% | 4.0% | 14.2% |
| H-R6 rsi2_pullback | −13.32% | −0.307 | −21.7% | 11.9% | 26.1% |
| H-R3 bollinger_meanrev | −14.24% | −0.365 | −20.4% | 11.1% | 25.1% |
| H-R5 weekend_effect | 0.00% | n/a | 0.0% | 0.0% | 0.0% |

**Combined Sharpe −0.123 versus best single +0.243: a −150.6% change, not +30–50%.**

The mechanism is visible, and it is the interesting part:

- **average pairwise correlation 0.105** — the strategies really are nearly independent
- **diversification ratio 1.841** — the mix is genuinely much less volatile than its parts
  (annualised vol falls to 4.7% against 7.4–17.9% for the singles)
- **but only 2 of 6 strategies have a positive Sharpe**

So the note's mechanism is real and the note's conclusion is false *for this book*.
Diversification reduces variance; it does not create expected return. Combining four negative-
expectancy strategies with two positive ones produces a diversified near-zero, which is
exactly what the table shows (−2.27% over 3.3 years, Sharpe −0.123).

That is not an argument against portfolio construction. It is the ordering requirement the
note skips: **you must establish positive per-strategy expectancy before combining, or you
are just averaging losses more efficiently.** The claim as stated ("combining improves
risk-adjusted returns 30–50%") is only true conditional on components that already have an
edge — and in this repository, establishing that edge is precisely the open problem.

Note also that H-R5 contributes nothing here: on daily bars the weekend rule never fires
(`no cell with n≥10`), so the combined book is effectively five strategies.

## 4. What was adopted into this repository

| item | where it landed |
|---|---|
| The multi-asset vs portfolio distinction, and the admission that this harness has no shared-cash simulation | `PROGRESS.md`, roadmap P5 (R157–R160) |
| The "read sweeps as heatmaps, prefer plateaus" rule | already in `ROADMAP_200` via the pre-registration rule |
| The `portfolio_combination.py` test as a **permanent** portfolio-layer check, not a one-off rebuttal | `realtime_challenge/proof/`, results committed |
| Stale-library stance (backtrader, qstrader) | `LIBRARY_SURVEY.md` already lists backtrader under "avoid"; qstrader is added there with its 2024-06-30 push date |

## 5. What this audit could not verify

- The Workroom plugin's byte-identical-Office evidence (no public repository found).
- Every data-provider free-tier number (account-tier, needs a key).
- The feasibility of `agent-desktop` / `Windows-MCP` latency claims (0.2–0.9 s) — plausible,
  not measured here; `01-screen-control-llm/MEASUREMENTS.md` has this machine's real numbers
  and should be preferred over any vendor figure.

Per the repo's own rule: **observed / derived / assumed**. The table in §1 is observed
(GitHub API, date stamped). §3 is derived from committed artifacts. The note's data tiers are
assumed until someone measures them.
