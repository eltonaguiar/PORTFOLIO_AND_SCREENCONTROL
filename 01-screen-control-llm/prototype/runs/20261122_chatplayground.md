# Prototype run 2026-11-22 — ChatPlayground sweep on the user's own Chrome

**What this was.** The first end-to-end run of the control kernel against a surface we do not own: a
logged-in SPA in the user's real Chrome, on monitor 2, at 150% scaling. Task file:
[`../tasks/chatplayground.json`](../tasks/chatplayground.json). Transport: the Hermes `computer_use`
tool (cua-driver), background delivery. No credentials typed, no password manager touched.

**Verdict: the loop works — perceive → target → act → verify → detect completion — on element
indices. It does not work on raw coordinates, which is the finding that matters.**

## Observations, in order

| # | Action | Result | Evidence |
|---|---|---|---|
| 1 | `capture app=chrome.exe mode=ax` (cold) | **24 elements**, all browser furniture, 0 page nodes | tabs, address bar, extension buttons only |
| 2 | `capture app=chrome.exe mode=ax` (after one `som` capture) | **95 elements**, page fully exposed | `Document 'Compare · ChatPlayground AI'`, `Hyperlink 'Playground'`, model list |
| 3 | `click coordinate=[700,960]` | window-relative point became `(2621,1019)` after the driver added the window origin `(1912,50)`; **below the 720 px client area**, the open conversation was cleared | panel content went from 3 answers to "Ready when you are" |
| 4 | `set_value element=86 'Message every model'` | composer filled | screenshot shows `Reply with exactly: PROTOTYPE OK`, Send becomes active |
| 5 | `click coordinate=[3108,739]` | driver posted the click at **`(5029,798)`** — past the 1360 px client width, a no-op | element list unchanged |
| 6 | `click element=87 'Send to every model'` | **sent**; all three panels show the user bubble, `Stop`, and a spinner | posted click at `(3127,746)` |
| 7 | poll `capture mode=ax` after ~20 s | **all panels done** | `Text 'ChatGPT-6 Luna finished responding'`, `Text 'Claude (Latest Model) finished responding'`, `PROTOTYPE OK`, `TTFT 634 ms / Total 851 ms / 14 → 8 tokens / 1 credit`, `TTFT 338 ms / 494 ms / 38 → 12 tokens` |
| 8 | element inventory during streaming | `Copy all answers` exists while streaming | `Button 'Copy all answers' @ [2319, 727, 32, 32]`, plus per-panel `Copy message` |
| 9 | element inventory after completion | `Copy all answers` disappears; per-panel `Copy message` remains | 129 elements, no copy-all |

## Three corrections this run forced

1. **A first a11y probe returning only furniture is not a failed surface — it is an unawakened tree.**
   Chrome exposes the whole page after one capture. `kernel/resolve.py` now documents the retry, and
   `Probe.acceptable()` still rejects furniture-only answers so the ladder cannot settle there.
2. **`coordinate=` is unreliable; `element=` is not.** Same window, same capture: the coordinate click
   was rescaled by the driver to a different point, the element click landed inside the target. Two
   coordinate clicks, two wrong outcomes; one element click, correct. This is now a hard rule in
   `INTERVENTION.md` §1 and belongs in `kernel/act.py` as a refusal, not a convention.
3. **The cleanest completion signal is a live region, not a heuristic.** Both panels emit
   `<model> finished responding` as text. TTFT/token strips are also present and are better *evidence*
   (they prove the run's cost and latency) but worse *triggers* — they can appear while tokens still
   stream.

## What this changes in the backlog

- `tasks/chatplayground.json` gains `"finished responding"` as a positive done signature and drops to
  a single-poll confirm (the live region is authoritative).
- `kernel/act.py` must refuse `coordinate=` when an element handle exists for the target — a
  one-line policy with live evidence behind it.
- Extraction becomes: hover panel → `Copy message` (per panel, DOM order) → clipboard, because
  `Copy all answers` is only present mid-stream. `Copy all answers` stays the fast path when the run
  is still streaming and the caller wants a partial sweep.

## Extraction — what actually works

`Copy all answers` exists **only while a response is streaming**; once the last panel finishes it is gone
from the tree (measured twice, 129 elements both times, no copy-all node). So a completed sweep is
extracted two ways, both verified:

1. **Per-panel `Copy message`** (assistant row, e.g. `#72`) → clipboard. Verified: clipboard returned
   `PROTOTYPE OK` (12 chars). The user-message copy at `#57` returns the *prompt* — row matters.
2. **Rebuild from the accessibility tree** — [`../extract.py`](../extract.py) groups panels by their
   `Model: <name>. Change model` headers, finds each panel's `Assistant` marker, and reads the `Text`
   nodes below it until the telemetry strip (detected by shape: `TTFT 634 ms`, `14 → 8 tokens`,
   `1 credit`). Output was diffed against the app's own paste-all document:

   ```
   # Reply with exactly: PROTOTYPE OK

   ## ChatGPT-6 Luna

   PROTOTYPE OK

   ## Claude (Latest Model)

   PROTOTYPE OK

   ## GLM 5.3 Flash

   PROTOTYPE OK
   ```

   **Result: MATCH** (byte-identical after newline normalisation), 3/3 panels, including GLM whose panel
   is off-viewport. Saved as [`../transcripts/chatplayground_pasteall_20261122.md`](../transcripts/chatplayground_pasteall_20261122.md).
   Two filters were needed: GLM emits a `Thought for 1s` reasoning marker and a `Response stats`
   header that the app's own export omits.

## Not proven by this run

- The `Copy all answers` control used mid-stream for a *partial* sweep (it exists then; not exercised).
- The login gate (`Continue with Google` → auto-sign-in). The user's Chrome was already signed in, so
  step `ensure_login` was a no-op. The pause-on-credential path is designed (`INTERVENTION.md` §3) but
  has not been exercised.
- Any non-browser surface. That is the point of the kernel, and it remains the bigger test: items A4
  and A7 in `NEXT_STEPS.md`.
- Multi-paragraph answers: the tree-based rebuild was verified on one-line answers; long answers may
  split across many `Text` nodes whose paragraph boundaries still need a rule.
