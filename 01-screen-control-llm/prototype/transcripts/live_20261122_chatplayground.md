# Live transcript — 2026-11-22, ChatPlayground sweep

Prompt sent: `Reply with exactly: PROTOTYPE OK`
Transport: Hermes `computer_use` (cua-driver 0.21.0), background delivery, no focus steal.
Window: `chrome.exe` — "Compare · ChatPlayground AI", origin ≈ (1920, 58), 1360×633 client, 150% scaling.

## Step record

| Step | Action | Verdict | Evidence |
|---|---|---|---|
| resolve | `capture mode=ax` cold → 24 elements, furniture only | retry | no page nodes |
| resolve | `capture mode=som` → accessibility awoken | PASS | 95 elements, `Document 'Compare · ChatPlayground AI'` |
| composer | `set_value element=86` | PASS | screenshot: `Reply with exactly: PROTOTYPE OK`, Send active |
| send | `click element=87 'Send to every model'` | PASS | posted click (3127,746); user bubble in all 3 panels; `Stop` present |
| wait_done | poll `capture mode=ax` | PASS | `Text 'ChatGPT-6 Luna finished responding'`, `Text 'Claude (Latest Model) finished responding'` |
| extract | `click element=72 'Copy message'` (assistant row) | PASS | clipboard = `PROTOTYPE OK`, 12 chars |

## Extracted answers

- **ChatGPT-6 Luna** — `PROTOTYPE OK` · TTFT 634 ms · total 851 ms · 14 → 8 tokens · 1 credit
- **Claude (Latest Model)** — `PROTOTYPE OK` · TTFT 338 ms · total 494 ms · 38 → 12 tokens
- **GLM 5.3 Flash** — panel streamed with a Stop control; its completion live region had not appeared at
  the capture used for extraction (the run's done-detection was therefore correctly *partial*, not
  "all panels done").

## Control map observed on this surface (for the next run)

| Control | Label | Notes |
|---|---|---|
| composer | `Edit 'Message every model'` | `set_value` works; typing also works after focus |
| send | `Button 'Send to every model'` | absent until the composer has text |
| stop | `Button 'Stop all models'` | appears while streaming — the negative done signal |
| done (live region) | `Text '<model> finished responding'` | **authoritative** per-panel completion |
| metrics | `TTFT <n> ms`, `Total time <n> ms`, `<in> → <out> tokens`, `<n> credit(s)` | per-panel evidence, not a trigger |
| copy one | `Button 'Copy message'` (assistant row) | clipboard round-trip verified |
| copy all | `Button 'Copy all answers'` | present **only while streaming**; gone after completion |
| per-panel composer | `Edit 'Send to <model> only'` | single-model fan-out |

## Failure observed (and why it is in the design)

An early `coordinate=[700,960]` click — computed in screenshot space, not native — was posted at
`(2621,1019)` and cleared the open conversation. The kernel's rules now come from that:
elements only, and never retry an unverified coordinate click on a stateful surface.
