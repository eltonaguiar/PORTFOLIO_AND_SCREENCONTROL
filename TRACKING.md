# TRACKING — what is where, and what is still in the wrong place

Two rules govern this repository:

1. **Screen control and trading never share a folder.** `01-screen-control-llm/` is how an agent perceives and
   drives a machine; `03-trading-strategies/` is what we test in markets; `02-portfolio-multi-asset/` is the
   reference shelf they both cite.
2. **The index below is generated, not maintained.** `scripts/update_index.py` rewrites it from the working tree,
   so it cannot drift from reality.

## Status

| Item | State |
|---|---|
| Folder split (`01` screen / `02` reference / `03` strategies / `REVIEWS` audits) | ✅ in place |
| Peer challenge artifacts in `03-trading-strategies/` | ✅ moved in `fdc93d7` (harness, results, ledger, roadmap, peer cross-check) |
| Strategy contract (declaration, gates G1–G8, manifest, trial accounting) | ✅ [`03-trading-strategies/STRATEGY_SPEC.md`](03-trading-strategies/STRATEGY_SPEC.md) |
| Tool interface for screen control (14 tools, approval classes, ledger schema) | ✅ [`01-screen-control-llm/TOOL_INTERFACE.md`](01-screen-control-llm/TOOL_INTERFACE.md) |
| Evidence rules (provenance, gates, manifests, multiple testing) | ✅ [`02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md`](02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md) |
| Eight source documents audited | ✅ [`REVIEWS/`](REVIEWS/) |
| Per-topic next actions | listed at the bottom of each folder README |

## Keeping it current

```bash
git pull --rebase
python scripts/update_index.py      # rewrite the block below
python scripts/update_index.py --check   # exit 1 if stale (use in CI)
```

A scheduled job (Hermes cron) runs the same pair and commits only when the index actually changed, so the table
reflects new peer artifacts without a human in the loop.

## Index

<!-- INDEX:START -->
| Folder | Files | Artifacts (results/ledger/state) | Last commit |
|---|---:|---:|---|
| `01-screen-control-llm/` — Screen control via LLM/AI — how an agent sees and drives a machine | 71 (25 md) | 0 | see `git log -1 -- 01-screen-control-llm` |
| `02-portfolio-multi-asset/` — Reference: tracking, engine choice, evidence rules | 9 (8 md) | 0 | see `git log -1 -- 02-portfolio-multi-asset` |
| `03-trading-strategies/` — The challenge: specs, rounds, results, ledgers | 193 (34 md) | 139 | see `git log -1 -- 03-trading-strategies` |
| `REVIEWS/` — Audits of model answers and challenge documents | 26 (25 md) | 0 | see `git log -1 -- REVIEWS` |

### Documents

| Path | Lines | Bytes |
|---|---:|---:|
| [`01-screen-control-llm/DRIVING_BROWSER_AND_VSCODE.md`](01-screen-control-llm/DRIVING_BROWSER_AND_VSCODE.md) | 107 | 7525 |
| [`01-screen-control-llm/FACTCHECK.md`](01-screen-control-llm/FACTCHECK.md) | 82 | 8645 |
| [`01-screen-control-llm/harvest/1min_methodology.md`](01-screen-control-llm/harvest/1min_methodology.md) | 85 | 10558 |
| [`01-screen-control-llm/harvest/arena_methodology.md`](01-screen-control-llm/harvest/arena_methodology.md) | 1040 | 38556 |
| [`01-screen-control-llm/harvest/askanymodel_methodology.md`](01-screen-control-llm/harvest/askanymodel_methodology.md) | 305 | 26812 |
| [`01-screen-control-llm/harvest/CAPTURE_CONTRACT.md`](01-screen-control-llm/harvest/CAPTURE_CONTRACT.md) | 96 | 5617 |
| [`01-screen-control-llm/harvest/chatplayground_methodology.md`](01-screen-control-llm/harvest/chatplayground_methodology.md) | 416 | 33727 |
| [`01-screen-control-llm/harvest/duckai_methodology.md`](01-screen-control-llm/harvest/duckai_methodology.md) | 88 | 10376 |
| [`01-screen-control-llm/harvest/FREE_ENDPOINTS.md`](01-screen-control-llm/harvest/FREE_ENDPOINTS.md) | 121 | 6733 |
| [`01-screen-control-llm/harvest/SUMMARY_multi_ai_methodology.md`](01-screen-control-llm/harvest/SUMMARY_multi_ai_methodology.md) | 151 | 9997 |
| [`01-screen-control-llm/IMPLEMENTATION.md`](01-screen-control-llm/IMPLEMENTATION.md) | 126 | 6506 |
| [`01-screen-control-llm/INTERVENTION.md`](01-screen-control-llm/INTERVENTION.md) | 94 | 6321 |
| [`01-screen-control-llm/MEASUREMENTS.md`](01-screen-control-llm/MEASUREMENTS.md) | 143 | 7047 |
| [`01-screen-control-llm/PC_AGENT_CONTROL_RESEARCH.md`](01-screen-control-llm/PC_AGENT_CONTROL_RESEARCH.md) | 389 | 40245 |
| [`01-screen-control-llm/PROGRESS.md`](01-screen-control-llm/PROGRESS.md) | 69 | 5411 |
| [`01-screen-control-llm/prototype/runs/20261122_cdp_breakthrough.md`](01-screen-control-llm/prototype/runs/20261122_cdp_breakthrough.md) | 74 | 4480 |
| [`01-screen-control-llm/prototype/runs/20261122_chatplayground.md`](01-screen-control-llm/prototype/runs/20261122_chatplayground.md) | 92 | 6098 |
| [`01-screen-control-llm/prototype/runs/20261122_multi_site_blockers.md`](01-screen-control-llm/prototype/runs/20261122_multi_site_blockers.md) | 56 | 4080 |
| [`01-screen-control-llm/prototype/transcripts/chatplayground_methodology.md`](01-screen-control-llm/prototype/transcripts/chatplayground_methodology.md) | 42 | 2297 |
| [`01-screen-control-llm/prototype/transcripts/chatplayground_pasteall_20261122.md`](01-screen-control-llm/prototype/transcripts/chatplayground_pasteall_20261122.md) | 13 | 153 |
| [`01-screen-control-llm/prototype/transcripts/live_20261122_chatplayground.md`](01-screen-control-llm/prototype/transcripts/live_20261122_chatplayground.md) | 43 | 2730 |
| [`01-screen-control-llm/README.md`](01-screen-control-llm/README.md) | 152 | 12716 |
| [`01-screen-control-llm/SAFETY.md`](01-screen-control-llm/SAFETY.md) | 43 | 3029 |
| [`01-screen-control-llm/TOOL_INTERFACE.md`](01-screen-control-llm/TOOL_INTERFACE.md) | 140 | 7296 |
| [`01-screen-control-llm/VSCODE_PANEL_CDP_CONTROL.md`](01-screen-control-llm/VSCODE_PANEL_CDP_CONTROL.md) | 281 | 12825 |
| [`02-portfolio-multi-asset/CAPITAL_ALLOCATION.md`](02-portfolio-multi-asset/CAPITAL_ALLOCATION.md) | 123 | 8695 |
| [`02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md`](02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md) | 134 | 7082 |
| [`02-portfolio-multi-asset/FRAMEWORK_MATRIX.md`](02-portfolio-multi-asset/FRAMEWORK_MATRIX.md) | 80 | 6855 |
| [`02-portfolio-multi-asset/INVESTMENT_HUB_REVIEW.md`](02-portfolio-multi-asset/INVESTMENT_HUB_REVIEW.md) | 101 | 7465 |
| [`02-portfolio-multi-asset/NAUTILUS_ARCHITECTURE.md`](02-portfolio-multi-asset/NAUTILUS_ARCHITECTURE.md) | 291 | 16353 |
| [`02-portfolio-multi-asset/PAPER_TRADING_AND_MONITORING.md`](02-portfolio-multi-asset/PAPER_TRADING_AND_MONITORING.md) | 100 | 6132 |
| [`02-portfolio-multi-asset/PORTFOLIO_TRACKING.md`](02-portfolio-multi-asset/PORTFOLIO_TRACKING.md) | 115 | 6910 |
| [`02-portfolio-multi-asset/README.md`](02-portfolio-multi-asset/README.md) | 67 | 5671 |
| [`03-trading-strategies/AI_IDEA_CYCLES.md`](03-trading-strategies/AI_IDEA_CYCLES.md) | 79 | 5658 |
| [`03-trading-strategies/ASSET_CLASS_IDEA_HARVEST.md`](03-trading-strategies/ASSET_CLASS_IDEA_HARVEST.md) | 59 | 4359 |
| [`03-trading-strategies/BRACKET_P7.md`](03-trading-strategies/BRACKET_P7.md) | 180 | 9527 |
| [`03-trading-strategies/CARRY_RTT_T4.md`](03-trading-strategies/CARRY_RTT_T4.md) | 125 | 6582 |
| [`03-trading-strategies/CARRY_SERIES.md`](03-trading-strategies/CARRY_SERIES.md) | 68 | 3752 |
| [`03-trading-strategies/ETF_ROTATION_H-E1.md`](03-trading-strategies/ETF_ROTATION_H-E1.md) | 144 | 7413 |
| [`03-trading-strategies/FABRICATION_CHECKLIST.md`](03-trading-strategies/FABRICATION_CHECKLIST.md) | 106 | 5862 |
| [`03-trading-strategies/FOLD_SENSITIVITY_T3.md`](03-trading-strategies/FOLD_SENSITIVITY_T3.md) | 92 | 4206 |
| [`03-trading-strategies/FX_CENSUS_P8.md`](03-trading-strategies/FX_CENSUS_P8.md) | 98 | 5130 |
| [`03-trading-strategies/GPT5NANO_REVIEW.md`](03-trading-strategies/GPT5NANO_REVIEW.md) | 52 | 4684 |
| [`03-trading-strategies/HARNESS_CERTIFICATION.md`](03-trading-strategies/HARNESS_CERTIFICATION.md) | 56 | 3919 |
| [`03-trading-strategies/HORIZON_LADDER_A9.md`](03-trading-strategies/HORIZON_LADDER_A9.md) | 112 | 5408 |
| [`03-trading-strategies/IMPLEMENTATION.md`](03-trading-strategies/IMPLEMENTATION.md) | 77 | 3902 |
| [`03-trading-strategies/LIBRARY_SURVEY.md`](03-trading-strategies/LIBRARY_SURVEY.md) | 70 | 5884 |
| [`03-trading-strategies/PEER_REVIEW_T2.md`](03-trading-strategies/PEER_REVIEW_T2.md) | 119 | 7568 |
| [`03-trading-strategies/PEERCROSSCHECK_deepseek-flash.md`](03-trading-strategies/PEERCROSSCHECK_deepseek-flash.md) | 282 | 17431 |
| [`03-trading-strategies/PROGRESS.md`](03-trading-strategies/PROGRESS.md) | 568 | 86797 |
| [`03-trading-strategies/PROVEN_EDGE_METHODOLOGY.md`](03-trading-strategies/PROVEN_EDGE_METHODOLOGY.md) | 124 | 9362 |
| [`03-trading-strategies/PROVEN_STRATEGIES_TABLE_AUDIT.md`](03-trading-strategies/PROVEN_STRATEGIES_TABLE_AUDIT.md) | 135 | 11438 |
| [`03-trading-strategies/READING_LIST_VERIFIED.md`](03-trading-strategies/READING_LIST_VERIFIED.md) | 72 | 5978 |
| [`03-trading-strategies/README.md`](03-trading-strategies/README.md) | 129 | 7718 |
| [`03-trading-strategies/ROADMAP_200_deepseek-flash.md`](03-trading-strategies/ROADMAP_200_deepseek-flash.md) | 327 | 19700 |
| [`03-trading-strategies/STATIC_GATE_AUDIT.md`](03-trading-strategies/STATIC_GATE_AUDIT.md) | 37 | 3470 |
| [`03-trading-strategies/STRATEGY_SPEC.md`](03-trading-strategies/STRATEGY_SPEC.md) | 133 | 6196 |
| [`03-trading-strategies/TIMEFRAME_MATRIX.md`](03-trading-strategies/TIMEFRAME_MATRIX.md) | 202 | 10945 |
| [`03-trading-strategies/validation/MODEL_ANSWER_DELTAS.md`](03-trading-strategies/validation/MODEL_ANSWER_DELTAS.md) | 559 | 39541 |
| [`03-trading-strategies/validation/MODEL_PANEL_INDEX.md`](03-trading-strategies/validation/MODEL_PANEL_INDEX.md) | 80 | 6440 |
| [`03-trading-strategies/validation/REVIEW_AND_ADOPTION.md`](03-trading-strategies/validation/REVIEW_AND_ADOPTION.md) | 98 | 7168 |
| [`03-trading-strategies/validation/strategy_validation_protocol.md`](03-trading-strategies/validation/strategy_validation_protocol.md) | 662 | 49890 |
| [`03-trading-strategies/VALIDATION_METHODOLOGY_PANEL.md`](03-trading-strategies/VALIDATION_METHODOLOGY_PANEL.md) | 152 | 10964 |
| [`03-trading-strategies/VALUE_VS_PEAD_EVIDENCE.md`](03-trading-strategies/VALUE_VS_PEAD_EVIDENCE.md) | 189 | 16693 |
| [`03-trading-strategies/VERDICT_200.md`](03-trading-strategies/VERDICT_200.md) | 67 | 9128 |
| [`03-trading-strategies/VOL_SCALING_H-VS1.md`](03-trading-strategies/VOL_SCALING_H-VS1.md) | 94 | 4754 |
| [`03-trading-strategies/WALKFORWARD_P6.md`](03-trading-strategies/WALKFORWARD_P6.md) | 115 | 6127 |
| [`REVIEWS/AGENT_MARKET_AUTOMATION_PLAYBOOK_REVIEW.md`](REVIEWS/AGENT_MARKET_AUTOMATION_PLAYBOOK_REVIEW.md) | 53 | 6177 |
| [`REVIEWS/ASKANYMODEL_MULTICHAT_STRATEGY_TABLE_REVIEW.md`](REVIEWS/ASKANYMODEL_MULTICHAT_STRATEGY_TABLE_REVIEW.md) | 34 | 6919 |
| [`REVIEWS/CHALLENGE_PROTOTYPES_GLM_GEMINI_REVIEW.md`](REVIEWS/CHALLENGE_PROTOTYPES_GLM_GEMINI_REVIEW.md) | 171 | 12575 |
| [`REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md`](REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md) | 156 | 8628 |
| [`REVIEWS/CLAUDE_HAIKU_CHALLENGE_REVIEW.md`](REVIEWS/CLAUDE_HAIKU_CHALLENGE_REVIEW.md) | 96 | 6975 |
| [`REVIEWS/CLAUDE_OPUS_CHALLENGE_REVIEW.md`](REVIEWS/CLAUDE_OPUS_CHALLENGE_REVIEW.md) | 87 | 7249 |
| [`REVIEWS/COPILOT_GPT5_STACK_AND_ETF_HYPOTHESIS_REVIEW.md`](REVIEWS/COPILOT_GPT5_STACK_AND_ETF_HYPOTHESIS_REVIEW.md) | 84 | 6454 |
| [`REVIEWS/GEMINI_TRADE_0001_AUDIT.md`](REVIEWS/GEMINI_TRADE_0001_AUDIT.md) | 204 | 10859 |
| [`REVIEWS/GPT41MINI_CHALLENGE_BLUEPRINT_REVIEW.md`](REVIEWS/GPT41MINI_CHALLENGE_BLUEPRINT_REVIEW.md) | 68 | 6540 |
| [`REVIEWS/inputs/AGENT_MARKET_AUTOMATION_PLAYBOOK.md`](REVIEWS/inputs/AGENT_MARKET_AUTOMATION_PLAYBOOK.md) | 97 | 11968 |
| [`REVIEWS/inputs/ALLOCATION_FOUR_MODEL_ANSWERS.md`](REVIEWS/inputs/ALLOCATION_FOUR_MODEL_ANSWERS.md) | 483 | 41739 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Claude-4.5-Opus.md`](REVIEWS/inputs/REALTIMECHALLENGE_Claude-4.5-Opus.md) | 3186 | 114814 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Claude-5.5-Haiku.md`](REVIEWS/inputs/REALTIMECHALLENGE_Claude-5.5-Haiku.md) | 379 | 23658 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Gemini-3.1-Pro.md`](REVIEWS/inputs/REALTIMECHALLENGE_Gemini-3.1-Pro.md) | 254 | 22199 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_GLM-5.3-Flash.md`](REVIEWS/inputs/REALTIMECHALLENGE_GLM-5.3-Flash.md) | 111 | 10274 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Meta-MuseSpark.md`](REVIEWS/inputs/REALTIMECHALLENGE_Meta-MuseSpark.md) | 260 | 16326 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Pi.md`](REVIEWS/inputs/REALTIMECHALLENGE_Pi.md) | 148 | 4525 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Qwen-Plus.md`](REVIEWS/inputs/REALTIMECHALLENGE_Qwen-Plus.md) | 131 | 7711 |
| [`REVIEWS/META_MUSESPARK_CHALLENGE_REVIEW.md`](REVIEWS/META_MUSESPARK_CHALLENGE_REVIEW.md) | 73 | 6028 |
| [`REVIEWS/PERPLEXITY_NOTE_REVIEW.md`](REVIEWS/PERPLEXITY_NOTE_REVIEW.md) | 158 | 12937 |
| [`REVIEWS/PI_CHALLENGE_REVIEW.md`](REVIEWS/PI_CHALLENGE_REVIEW.md) | 61 | 4338 |
| [`REVIEWS/QWEN_PLUS_CHALLENGE_REVIEW.md`](REVIEWS/QWEN_PLUS_CHALLENGE_REVIEW.md) | 84 | 5640 |
| [`REVIEWS/README.md`](REVIEWS/README.md) | 126 | 11515 |
| [`REVIEWS/SUBQ_FURTHER_NOTE_REVIEW.md`](REVIEWS/SUBQ_FURTHER_NOTE_REVIEW.md) | 52 | 7095 |
| [`REVIEWS/SUBQ_STACK_RECOMMENDATION_REVIEW.md`](REVIEWS/SUBQ_STACK_RECOMMENDATION_REVIEW.md) | 116 | 8590 |

### Top level

| Path | Lines | Bytes |
|---|---:|---:|
| [`NEXT_STEPS.md`](NEXT_STEPS.md) | 155 | 12563 |
| [`PROGRESS_LOG.md`](PROGRESS_LOG.md) | 40 | 8907 |
| [`README.md`](README.md) | 196 | 16360 |
| [`WORKSTREAMS.md`](WORKSTREAMS.md) | 97 | 6492 |

_Generated by `scripts/update_index.py`; do not edit this block by hand._
<!-- INDEX:END -->
