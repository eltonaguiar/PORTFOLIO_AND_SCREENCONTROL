# Run 2 — multi-site series: what blocked, and what it proves about the kernel

Date: 2026-11-22 · Task: [`../tasks/multi_site_research.json`](../tasks/multi_site_research.json)
Verdict: **partial**. Two sites reached, both signed in, sequence not completed. The blockers are
surface properties, not task logic — which is exactly what a control kernel has to absorb.

## What worked

| Step | Evidence |
|---|---|
| Navigate a *running* browser without synthetic input | `chrome.exe --new-tab https://arena.ai/` → "Opening in existing browser session", new tab appeared |
| arena.ai already signed in as the right account | `Button 'zerounderscore@gmail.com'` @ (1930,720); sidebar shows the user's own chat history |
| New chat opened | `Hyperlink 'New Chat'` click → "What would you like to do?" + `Ask anything…` composer |
| Switch tabs by pixel click | click (145,19) → posted (2066,78) → `Document 'Compare · ChatPlayground AI'` became the active document |
| Per-panel composers still exposed | `Edit 'Send to ChatGPT-6 Luna only'` @ (2155,675,304,33) — `set_value` works on these |

## What blocked (measured)

1. **Chrome's content area drops background key and scroll events.** Both `key ctrl+l` and `scroll`
   returned `code: background_unavailable`, `target_class: Chrome_WidgetWin_1`, with
   `escalation.recommended: "foreground"`. Clicks and `set_value` (UIA ValuePattern) *do* work in
   background. So on a browser, the split is: **pointer/value = background; keyboard/wheel = foreground**.
   A foreground scroll was re-issued and succeeded — the approval path works, it just costs a visible
   focus change per event, which is not acceptable for a 3-prompt series driven blind.
2. **`app="chrome.exe"` is ambiguous once two Chrome windows exist.** `chrome --new-tab` also produced a
   second window (`30542890`, "stackscoial multi ai - Google Search"), and a transient profile-picker
   window appeared with "Who's using Chrome?". A capture by `app=` then resolved to the *wrong* window
   and returned 15 elements of profile UI instead of the page. Fix, verified: capture with
   `pid=45600, window_id=36899254`. **Element indices are only meaningful within one window.**
3. **The global composer leaves the accessibility tree** once a conversation has messages. 129 elements,
   and `Edit 'Message every model'` is simply absent (it was `#86` before the first send). The
   per-panel `Send to <model> only` edits remain. So a second prompt has to go through a panel-scoped
   composer, or the page has to be scrolled (foreground) to re-expose the footer.

## Why this is a useful failure

Each item is a rule the kernel now needs, and none of them is app-specific:

- **Window identity is part of the target**, not a global: `(pid, window_id)` must be carried through
  every capture and every action, and an element handle from one window must never be used against
  another. `kernel/capture.py` already carries `origin`; it must also carry the window identity.
- **Split the input verbs by delivery class.** On browser surfaces: `set_value`/click → background;
  `key`/`scroll`/`type` → foreground, therefore *budgeted* and *announced*, never looped.
- **A missing control is a state, not an error.** "Composer not in tree" means: scroll (foreground), or
  switch to the panel-scoped equivalent. The resolver should enumerate equivalents per surface.

## Next actions (in order)

1. Add `set_value`-first prompting to the chatplayground adapter: per-panel composer when the global one
   is absent, which needs **no foreground input at all**.
2. Run p1–p3 through that path, extract after each with `extract.py`, then clear (`Clear all`, broom icon)
   and verify the empty state before the next prompt.
3. For arena.ai: its composer is a contenteditable outside the exposed tree. Either find its element after
   a foreground scroll, or accept arena as foreground-only and run it last, announced.
4. Record both surfaces' control maps in this file as they are discovered — the next run should not have
   to rediscover them.
