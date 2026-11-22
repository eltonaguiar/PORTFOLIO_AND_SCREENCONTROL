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
| `01-screen-control-llm/` — Screen control via LLM/AI — how an agent sees and drives a machine | 20 (8 md) | 0 | see `git log -1 -- 01-screen-control-llm` |
| `02-portfolio-multi-asset/` — Reference: tracking, engine choice, evidence rules | 6 (6 md) | 0 | see `git log -1 -- 02-portfolio-multi-asset` |
| `03-trading-strategies/` — The challenge: specs, rounds, results, ledgers | 62 (11 md) | 38 | see `git log -1 -- 03-trading-strategies` |
| `REVIEWS/` — Audits of model answers and challenge documents | 18 (18 md) | 0 | see `git log -1 -- REVIEWS` |

### Documents

| Path | Lines | Bytes |
|---|---:|---:|
| [`01-screen-control-llm/FACTCHECK.md`](01-screen-control-llm/FACTCHECK.md) | 82 | 8645 |
| [`01-screen-control-llm/IMPLEMENTATION.md`](01-screen-control-llm/IMPLEMENTATION.md) | 126 | 6506 |
| [`01-screen-control-llm/MEASUREMENTS.md`](01-screen-control-llm/MEASUREMENTS.md) | 119 | 5940 |
| [`01-screen-control-llm/PC_AGENT_CONTROL_RESEARCH.md`](01-screen-control-llm/PC_AGENT_CONTROL_RESEARCH.md) | 389 | 40245 |
| [`01-screen-control-llm/PROGRESS.md`](01-screen-control-llm/PROGRESS.md) | 69 | 5411 |
| [`01-screen-control-llm/README.md`](01-screen-control-llm/README.md) | 108 | 7860 |
| [`01-screen-control-llm/SAFETY.md`](01-screen-control-llm/SAFETY.md) | 43 | 3029 |
| [`01-screen-control-llm/TOOL_INTERFACE.md`](01-screen-control-llm/TOOL_INTERFACE.md) | 140 | 7296 |
| [`02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md`](02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md) | 130 | 6795 |
| [`02-portfolio-multi-asset/FRAMEWORK_MATRIX.md`](02-portfolio-multi-asset/FRAMEWORK_MATRIX.md) | 80 | 6855 |
| [`02-portfolio-multi-asset/NAUTILUS_ARCHITECTURE.md`](02-portfolio-multi-asset/NAUTILUS_ARCHITECTURE.md) | 291 | 16353 |
| [`02-portfolio-multi-asset/PAPER_TRADING_AND_MONITORING.md`](02-portfolio-multi-asset/PAPER_TRADING_AND_MONITORING.md) | 100 | 6132 |
| [`02-portfolio-multi-asset/PORTFOLIO_TRACKING.md`](02-portfolio-multi-asset/PORTFOLIO_TRACKING.md) | 115 | 6910 |
| [`02-portfolio-multi-asset/README.md`](02-portfolio-multi-asset/README.md) | 66 | 5409 |
| [`03-trading-strategies/FABRICATION_CHECKLIST.md`](03-trading-strategies/FABRICATION_CHECKLIST.md) | 104 | 5479 |
| [`03-trading-strategies/GPT5NANO_REVIEW.md`](03-trading-strategies/GPT5NANO_REVIEW.md) | 52 | 4684 |
| [`03-trading-strategies/HARNESS_CERTIFICATION.md`](03-trading-strategies/HARNESS_CERTIFICATION.md) | 56 | 3919 |
| [`03-trading-strategies/IMPLEMENTATION.md`](03-trading-strategies/IMPLEMENTATION.md) | 77 | 3902 |
| [`03-trading-strategies/LIBRARY_SURVEY.md`](03-trading-strategies/LIBRARY_SURVEY.md) | 70 | 5884 |
| [`03-trading-strategies/PEERCROSSCHECK_deepseek-flash.md`](03-trading-strategies/PEERCROSSCHECK_deepseek-flash.md) | 282 | 17431 |
| [`03-trading-strategies/PROGRESS.md`](03-trading-strategies/PROGRESS.md) | 127 | 15472 |
| [`03-trading-strategies/README.md`](03-trading-strategies/README.md) | 128 | 7494 |
| [`03-trading-strategies/ROADMAP_200_deepseek-flash.md`](03-trading-strategies/ROADMAP_200_deepseek-flash.md) | 288 | 16894 |
| [`03-trading-strategies/STRATEGY_SPEC.md`](03-trading-strategies/STRATEGY_SPEC.md) | 124 | 5513 |
| [`03-trading-strategies/TIMEFRAME_MATRIX.md`](03-trading-strategies/TIMEFRAME_MATRIX.md) | 138 | 7775 |
| [`REVIEWS/AGENT_MARKET_AUTOMATION_PLAYBOOK_REVIEW.md`](REVIEWS/AGENT_MARKET_AUTOMATION_PLAYBOOK_REVIEW.md) | 53 | 6177 |
| [`REVIEWS/CHALLENGE_PROTOTYPES_GLM_GEMINI_REVIEW.md`](REVIEWS/CHALLENGE_PROTOTYPES_GLM_GEMINI_REVIEW.md) | 171 | 12575 |
| [`REVIEWS/CLAUDE_HAIKU_CHALLENGE_REVIEW.md`](REVIEWS/CLAUDE_HAIKU_CHALLENGE_REVIEW.md) | 96 | 6975 |
| [`REVIEWS/CLAUDE_OPUS_CHALLENGE_REVIEW.md`](REVIEWS/CLAUDE_OPUS_CHALLENGE_REVIEW.md) | 87 | 7249 |
| [`REVIEWS/GPT41MINI_CHALLENGE_BLUEPRINT_REVIEW.md`](REVIEWS/GPT41MINI_CHALLENGE_BLUEPRINT_REVIEW.md) | 68 | 6540 |
| [`REVIEWS/inputs/AGENT_MARKET_AUTOMATION_PLAYBOOK.md`](REVIEWS/inputs/AGENT_MARKET_AUTOMATION_PLAYBOOK.md) | 97 | 11968 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Claude-4.5-Opus.md`](REVIEWS/inputs/REALTIMECHALLENGE_Claude-4.5-Opus.md) | 3186 | 114814 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Claude-5.5-Haiku.md`](REVIEWS/inputs/REALTIMECHALLENGE_Claude-5.5-Haiku.md) | 379 | 23658 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Gemini-3.1-Pro.md`](REVIEWS/inputs/REALTIMECHALLENGE_Gemini-3.1-Pro.md) | 254 | 22199 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_GLM-5.3-Flash.md`](REVIEWS/inputs/REALTIMECHALLENGE_GLM-5.3-Flash.md) | 111 | 10274 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Pi.md`](REVIEWS/inputs/REALTIMECHALLENGE_Pi.md) | 148 | 4525 |
| [`REVIEWS/inputs/REALTIMECHALLENGE_Qwen-Plus.md`](REVIEWS/inputs/REALTIMECHALLENGE_Qwen-Plus.md) | 131 | 7711 |
| [`REVIEWS/PERPLEXITY_NOTE_REVIEW.md`](REVIEWS/PERPLEXITY_NOTE_REVIEW.md) | 158 | 12937 |
| [`REVIEWS/PI_CHALLENGE_REVIEW.md`](REVIEWS/PI_CHALLENGE_REVIEW.md) | 61 | 4338 |
| [`REVIEWS/QWEN_PLUS_CHALLENGE_REVIEW.md`](REVIEWS/QWEN_PLUS_CHALLENGE_REVIEW.md) | 84 | 5640 |
| [`REVIEWS/README.md`](REVIEWS/README.md) | 57 | 5821 |
| [`REVIEWS/SUBQ_FURTHER_NOTE_REVIEW.md`](REVIEWS/SUBQ_FURTHER_NOTE_REVIEW.md) | 52 | 7095 |
| [`REVIEWS/SUBQ_STACK_RECOMMENDATION_REVIEW.md`](REVIEWS/SUBQ_STACK_RECOMMENDATION_REVIEW.md) | 116 | 8590 |

### Top level

| Path | Lines | Bytes |
|---|---:|---:|
| [`README.md`](README.md) | 145 | 12400 |

_Generated by `scripts/update_index.py`; do not edit this block by hand._
<!-- INDEX:END -->
