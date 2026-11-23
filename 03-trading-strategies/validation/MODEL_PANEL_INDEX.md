# Model panel index — every answer collected, audited, and ranked

One table for the whole exercise. Each row points at the section of `validation/MODEL_ANSWER_DELTAS.md` (or
`PROVEN_STRATEGIES_TABLE_AUDIT.md`) where its audit lives. **Nothing here is a threshold source** — the gate is
`validation/strategy_validation_protocol.md` v1.0 §3.11, always.

## The answers

| # | Model | Platform | Cost | Verdict | Audit ref |
|---|---|---|---|---|---|
| **1G** | **Claude 5.2 Fable** | 1min.ai | 1.18M credits | **best of thirteen.** DSR example reproduces to 4 dp (0.9174); 12 gates; random-signal 99th-pct test; corrected our power question with the `H₀` boundary row | §2i |
| **1E** | Alibaba-family | 1min.ai | 1.77M | **joint best.** DSR example exact (0.947); variance-corrected power table (**9.3 y** not 6.2); canary test; per-trade power | §2e |
| **1F** | Claude 5.5 Haiku | 1min.ai | 21,800 | most complete; 17 falsifiers; DSR example exact; **two arithmetic defects** (crude power table, Bonferroni column +24% at low SR) | §2f |
| **1D** | 1min.ai answer 4 | 1min.ai | — | strong; 6 adoptable items; **MinBTL self-contradiction** (45 trials / 5 y vs its own 2·ln N rule) | §2c |
| **Luna** | ChatGPT-6 Luna | chatplayground | 1 credit | clean and closest to v1.0; thin on operations | §1 |
| **Claude** | Claude (latest) | chatplayground | 2 credits | close; PBO relaxed to 0.25 | §1 |
| **GLM** | GLM 5.3 Flash | chatplayground | 1 credit | close; PBO 0.25, alpha-t tiered low | §1 |
| **R3-GLM** | GLM 5.3 | AskAnyModel | 4 credits | real citations; "32%" McLean–Pontiff error; best qualitative failure modes | §2h |
| **R3-GPT6** | GPT-6 Astra | AskAnyModel | 14 credits | real citations; **the TSMOM ⊂ trend overlap point** that changes our N_eff; MOP sample year wrong | §2h |
| **R3-Qwen** | Qwen3.8 Max | AskAnyModel | 4 credits | real citations; most specific crash dates; "Tsyvinski" for Verdelhan | §2h |
| **GLM-table** | 1min.ai table | 1min.ai | — | 2 of 7 citations misattributed | `PROVEN_STRATEGIES_TABLE_AUDIT` §1 |
| **Grok-table** | Grok 4.20 | AskAnyModel | 5 credits | **6 of 6 citations real** → adopted as `READING_LIST_VERIFIED.md` | `PROVEN_STRATEGIES_TABLE_AUDIT` §6 |
| **1A** | Gemini 4 Neon | 1min.ai | — | sound; alpha-t softened to 2.0; no break-even gate | §2 |
| **1B** | GPT-4 mini | 1min.ai | — | **poor**: DSR 0.80, 3-year OOS vs its own 27.8-y claim, "Bailey, Ledoit" | §2 |
| **1C** | Mistral | 1min.ai | — | **unusable**: DSR gated at 1.5, PBO inverted, "Bergomi" for CSCV, invented "Independent R²" | §2, §2b |
| **Routed batch** | "6 models" | AskAnyModel | 3 credits | **worthless**: four panes were one model (GPT-OSS 20B via Pollinations), 3 of 7 gates invented | §2g |

## What the thirteen answers agree on

1. **DSR ≥ 0.95** with an honest trial count — the only gate every credible answer shares.
2. **Pre-registration + a trial ledger**, with N_eff from the correlation structure, not the config count.
3. **Only monthly/quarterly rebalancing survives retail cost** — matched independently by our own ladder (+24.21 bp at 1D vs −0.57 bp at 15m).
4. **A short paper test cannot confirm a modest Sharpe.** Four different phrasings, same arithmetic.
5. **"Proven" means auditable and falsifiable, never guaranteed.**

## What they disagree on — and the range is the finding

| Gate | Range proposed | v1.0 | Notes |
|---|---|---|---|
| DSR pass mark | **0.80 to 1.5** | 0.95 | two answers set 1.5, which is impossible for a probability |
| PBO | **0.10 to 0.50** | ≤ 0.10 | one answer treats 0.50 (coin flip) as a pass |
| Break-even cost multiple | **2.0× / 2.5× / 3.0× / 4.0×** | ≥ 4× | only v1.0 is strict enough to matter |
| Capacity | **1× to 10×** intended AUM | ≥ 5× | |
| Alpha t | **1.5 to 3.5** | 3.0 / 3.5 / 4.0 by N_eff | |
| Tail ratio scale | **0.6 / 0.8 / 1.0 / 1.5 / 2.0 / 3.0** | ≥ 1.0 + skew + concentration | six different scales for one statistic |

**Six different threshold sets, no two answers identical on any gate.** That variance is why the protocol and the
ledger exist, and why no model answer is a threshold source.

## Recurring defects worth watching for in any new harvest

| Defect | Seen in | How to catch it |
|---|---|---|
| **DSR treated as a ratio, gated ≥ 1.5** | 1C, routed batch | DSR is a probability in [0,1]. If a gate exceeds 1, the answer is broken |
| **PBO inverted** (≥ 90% or < 0.5 as a pass) | 1C, routed batch | PBO is the probability of overfitting. Higher is worse |
| **Crude power table** (`6.185/SR²`) | 1A, 1B, 1D, 1F, Luna, Claude, GLM | recompute with `(1+SR²/2)`: SR 1.0 → **9.3 y**, not 6.2 |
| **Citation near-miss** (real surname, wrong field) | Mistral→Bergomi, GPT-4mini→Ledoit, Qwen→Tsyvinski, 1min.ai table→Gray&Vogel | **verify the title, not the author** |
| **Invented metric names** | routed batch (DIR, CAS, CTR, "Forward-Whisker") | search the name; if only DSR returns, it's invented |
| **Self-contradiction** (formula stated, table violates it) | 1D MinBTL, 1F Bonferroni, 1G κ | re-derive one table row |
| **Convergence on a wrong number** | all three round-3 panes: McLean–Pontiff "32%" (paper: 26% OOS / 58% post-publication) | agreement ≠ truth; check the primary source |
| **Pane labels ≠ model** | AskAnyModel (Gemma label, GPT-OSS answer) | **diff the panes** before calling it a panel |

## The one test that sorts a panel in five minutes

> **Ask for one worked numerical example and re-derive it.**
>
> Two of thirteen answers survived that: **1E** (SR₀ = 0.0523 → DSR 0.947) and **1G** (SR₀ = 0.0399 → DSR 0.9174).
> Both are Anthropic models on the same platform. The rest produced formulas they could not execute. That single
> question is a cheaper and more reliable discriminator than any benchmark, threshold table, or prose quality.

## Cost per useful answer

| Platform | Credits | Useful answers per credit |
|---|---|---|
| Local router `:4000` | free | — (the hourly cycle lives here) |
| chatplayground | 1–2 | high — three clean answers for 4 credits |
| AskAnyModel | 3–14 per model | mixed — the 25-credit round 3 was worth it, the 3-credit routed batch was not |
| 1min.ai | 22K–1.18M | **1G at 1.18M was worth it; 1F at 22K was the better trade** |

**Best value of the night: 1F (Claude 5.5 Haiku) at 21,800 credits** — 95% of 1G's content for 2% of its price.
