# Capturing an answer — Chat mode vs Agent mode

A chat answer is not always text. This file defines what "one answer" means per mode, so an extractor
either captures all of it or reports itself incomplete — never silently returns the prose and drops the
artefacts.

## Answer record

```jsonc
{
  "model": "…",
  "mode": "chat" | "agent",
  "text": "…",                       // may be empty in agent mode
  "attachments": [
    {"name": "report.md", "kind": "text/markdown", "bytes": 8123,
     "sha256": "…", "saved_as": "harvest/files/<model>/report.md"}
  ],
  "tool_trace": ["searched web", "opened 3 pages", "wrote file"],   // agent mode only, when shown
  "captured_utc": "…",
  "verdict": "COMPLETE" | "PARTIAL" | "NOTHING_CAPTURED"
}
```

## Chat mode

1. Read the pane's text (clipboard select-all is the most complete route; the a11y tree truncates to the
   viewport).
2. Confirm the pane belongs to the model you think it does — several interfaces render one pane at a
   time behind an avatar/icon, so "the visible answer" is not "all the answers". **Click every pane
   selector and capture each one separately.**
3. `verdict = COMPLETE` only when every selected model contributed a non-empty body.

## Agent mode (harder, and where most harvests quietly lie)

An agent answer can be:

- text only,
- **one attachment** (report, CSV, chart image),
- **a series of attachments** behind a collapsed file list,
- **text + attachments**, where the prose only makes sense next to the files,
- and it may show a **tool trace** ("searched the web", "opened these pages") that is itself part of
  the answer's provenance.

Capture order matters:

1. **Text first** (before any click navigates away or opens a modal).
2. **Enumerate the attachment controls** in that pane — buttons or links whose labels look like files
   (`report.md`, `.csv`, `*.png`, `N files`, `View files`, `Download`, `Open`).
3. **Open the file list** and record each name, type and size as the UI reports them.
4. **Fetch each file** — click to preview/download, then save the bytes and hash them. A preview that
   only renders part of the file is not the file.
5. **Record the tool trace** if the pane exposes one; it is the only evidence of *how* the agent arrived
   at the answer.
6. **Verify the count**: attachments claimed by the UI == attachments written to disk. If not,
   `verdict = PARTIAL` and say which one is missing.

## Failure modes seen on real surfaces

| Symptom | Cause | Handling |
|---|---|---|
| prose captured, files missing | select-all copies text only | enumerate + fetch files separately |
| only one model's answer captured | one pane at a time behind an avatar row | click each pane selector, capture per model |
| answer body truncated | a11y tree exposes only the rendered viewport | scroll + capture, or clipboard |
| click does nothing | a modal overlay intercepts pointer events | dismiss the overlay first, then retry once |
| "temporarily unavailable" from one model | provider-side routing failure | rotate in a different model and re-run; do not count it as a task failure |
| mode selector will not open | custom control that ignores synthetic clicks | set the mode in the product UI once, or drive the DOM over CDP |

## Why this matters for the repo

The harvests in `harvest/` are labelled with a verdict for exactly this reason: a summary built on
half-captured answers is worse than one built on fewer, complete ones. Chat mode harvests here are
`COMPLETE`; the agent-mode and one-pane-at-a-time surfaces are `PARTIAL` until the per-pane and
per-attachment loops have run.
