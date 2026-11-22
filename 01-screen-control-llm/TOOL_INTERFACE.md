# Tool interface — the contract both layers share

This is the interface spec that the screen-control kernel (§4.6 / Phase 1 of
[`PC_AGENT_CONTROL_RESEARCH.md`](PC_AGENT_CONTROL_RESEARCH.md)) and the supervisor (§5) both implement. It exists
so that *any* host — Hermes, Claude Code, Cursor, a custom Python agent — can drive the same capabilities with
the same names and the same semantics, and so that "did it work?" has one answer shape no matter which layer
answered.

Adapted from the twelve-tool sketch in the Perplexity note (see
[`../REVIEWS/PERPLEXITY_NOTE_REVIEW.md`](../REVIEWS/PERPLEXITY_NOTE_REVIEW.md)) and extended with the effect
verdicts measured on this machine.

## Envelope — every tool returns this

```json
{
  "ok": true,                       // the call was accepted and attempted
  "effect": "confirmed",            // confirmed | unverifiable | suspected_noop | refused
  "verified": true,                 // a read-back proved the intended change
  "evidence": {"kind": "crop_hash|element_value|text|diff|exit_code", "ref": "..."},
  "escalation": null,               // {"recommended": "px|foreground", "reason": "..."}
  "error": null                     // {"code": "...", "message": "...", "retryable": false}
}
```

Rule: **`ok` is not success.** Only `verified: true` closes an action. A tool that cannot verify must say
`effect: "unverifiable"` and the caller must re-read before retrying.

## 1 — Perceive

| Tool | Args | Returns | Notes |
|---|---|---|---|
| `list_windows` | `{}` | `[{id, app, pid, title, bounds, on_screen}]` | cheap, no capture |
| `read_window` | `{window_id, mode: "ax"\|"text"\|"image"\|"som", region?}` | `{elements?: [{ref, role, name, bounds, patterns}], text?, image_path?, dpi, scale}` | **always try `ax` first**; `som` adds marks for vision |
| `screenshot` | `{window_id?, region?, scale?}` | `{image_path, width, height, origin, px_per_point}` | origin + scale are mandatory — they are what makes coordinates land |

## 2 — Act (all take `verify: true` by default)

| Tool | Args | Verification |
|---|---|---|
| `click` | `{ref}` or `{window_id, x, y}`, `button`, `modifiers`, `delivery: "background"\|"foreground"` | element state change or crop hash change |
| `type` | `{text}` (into focused control) or `{ref, text}` | read the control's value back |
| `key` | `{combo}` | depends — window title, focused element, or crop |
| `scroll` | `{ref?, dy, dx}` | scroll position or crop delta |
| `set_value` | `{ref, value}` | `ValuePattern` read-back (preferred over click+type for selects/sliders) |

`ref` is the opaque element handle from the last `read_window`. Refs die on the next read — a stale ref must be
refused explicitly, not clicked anyway.

## 3 — Browser (only when a DOM exists)

| Tool | Args | Returns |
|---|---|---|
| `browser_navigate` | `{url, tab_id?}` | `{tab_id, title, url, status}` |
| `browser_extract` | `{tab_id?, selector? \| "a11y", format: "text"\|"html"\|"json"}` | `{content, node_count, truncated}` |

Prefer these over `read_window` for pages: the DOM is structure, and structure beats pixels.

## 4 — Compute and persist

| Tool | Args | Returns | Notes |
|---|---|---|---|
| `run_python` | `{code, timeout_s, workdir}` | `{stdout, stderr, exit_code, artifacts[]}` | **full** output, never a truncated tail — truncation is the #1 cause of agent loops |
| `save_artifact` | `{name, kind: "csv\|json\|md\|png\|parquet", path}` | `{path, bytes, sha256}` | every reported number must trace to one of these |

## 5 — Market and research

| Tool | Args | Returns |
|---|---|---|
| `query_market_data` | `{symbols[], venue, start, end, freq, price_type}` | `{series_id, rows, snapshot_hash, source, retrieved_at, status: "historical\|delayed\|realtime", missing_bars}` |
| `run_backtest` | `{strategy_ref, data_snapshot, params, costs, oos: true}` | `{run_id, metrics{cagr,vol,mdd,sharpe,trades}, oos, manifest_path}` |

Both must refuse to run if the [`../02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md`](../02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md)
gates fail. A backtest without a `snapshot_hash` and a `code_ref` is not a result.

## 6 — Gate

| Tool | Args | Returns |
|---|---|---|
| `request_approval` | `{action, why, blast_radius, expires_in_s}` | `{approved: bool, approver, scope, expires_at}` |

Approval classes — enforced by the tool layer, not by the model's judgement:

| Class | Examples | Rule |
|---|---|---|
| **0 — free** | reads, screenshots, list, query data | no approval |
| **1 — reversible** | type in an editor, scroll, click a nav element | no approval, but must verify |
| **2 — side-effecting** | `git push`, file delete, send an email, place a **paper** order, browser form submit | approval once per task, scoped |
| **3 — irreversible** | force-push, money movement, live order, credential change, account deletion, publishing | approval per action, short expiry, human identity recorded |

## Task ledger (the supervisor's state file)

One JSON file per task, written atomically, re-read every cycle. This is what survives compaction and restarts.

```json
{
  "task_id": "btc-momentum-validation-2026-11-22",
  "goal": "Determine whether the BTC momentum rule survives costs on 2024-2026 data",
  "created_utc": "2026-11-22T14:02:00Z",
  "deadline_utc": "2026-11-22T18:00:00Z",
  "approval_class": 1,
  "definition_of_done": {
    "checks": [
      {"cmd": "pytest -q tests/test_momentum.py", "expect_exit": 0},
      {"artifact": "reports/momentum_2026-11-22.md", "must_contain": ["snapshot_hash", "oos"]}
    ]
  },
  "state": "in_progress",
  "cycle": 7,
  "last_observation": {"at_utc": "...", "summary": "31 bars missing in 2025-08", "evidence": ["data/btc_1d.csv#sha256:..."]},
  "next_action": {"tool": "query_market_data", "args": {"symbols": ["BTC/USDT"]}},
  "attempts": [{"sig": "9f2c1a", "tool": "run_python", "result": "AssertionError", "count": 2}],
  "evidence": [{"kind": "file", "ref": "reports/run_0042.json", "sha256": "..."}],
  "blocked_reason": null,
  "budget": {"cycles_left": 33, "minutes_left": 214, "diffs_kb_left": 900}
}
```

## Loop contract

```
while state == "in_progress":
    ledger = read(task_id)                     # disk, not context
    if STOP file exists or budget exhausted: state = "cancelled"; break
    obs = perceive(next_action.target)          # ax → text → image
    result = act(next_action)                   # with verify
    append_evidence(result)
    state, next_action = decide(ledger, obs, result)   # classify: progress | loop | blocked | done
    write_atomic(ledger)                        # before any external side effect
```

`decide` is the whole supervisor from §5: loop signature comparison, stop classification, and the brief
injection. It never re-sends "continue" — it either supplies a new fact or stops.

## Why this interface and not twenty bespoke tools

- **One shape for verification** means the supervisor can trust any backend, including ones added later.
- **Capability naming is stable across OSes** (macOS AX, Windows UIA, Linux AT-SPI all answer `read_window`), which
  is what makes a single agent script portable.
- **Approval classes live in the tool layer**, so a prompt injection in a web page cannot escalate them.
