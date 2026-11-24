# Driving VS Code AI panels from code (Kilo / Zoo / Copilot over CDP)

**Status: WORKING.** Verified 2026-11-23/24 on Windows 11, VS Code `1.144.0`
(`2c33b50b16`, Electron 43.8.3, Chrome 150) against a Remote-SSH workspace
(`ssh-remote+eltonsGX10`). Three panels were read **and** written in the same window with no
keyboard, no mouse, and no accessibility layer:

| Panel | Layer | Verified by |
|---|---|---|
| Kilo Code | webview iframe | message + reply read back from the transcript |
| Zoo Code | webview iframe | task delivered, `Stop` control appeared, rebase executed |
| GitHub Copilot Chat | **native workbench DOM** | `CDP-RECV-OK` echoed back twice |

The code is `screen_control/vscode_panels.py` in this folder.

---

## 1. Why CDP rather than screen automation

Each panel is either a webview or Monaco DOM, so CDP addresses the actual input element. That
removes the two failure modes that make keyboard/mouse automation of an IDE unreliable:

- **stale coordinates** — the composer moves when a message lands; a remembered point posts
  somewhere else (measured: a click on the chat surface centre landed 245 px right of the real
  input and silently did nothing);
- **focus theft** — any capture/focus round-trip can send typed text into the wrong panel.

CDP sends to a named target, so text cannot go astray. The remaining hazards are all *state*
hazards, documented in §5.

---

## 2. Preconditions (two independent blockers)

### 2.1 Launch with a debug port

```bash
code --remote-debugging-port=9333 \
     --folder-uri "vscode-remote://ssh-remote+<host>/<abs/path>"
```

- `--remote-debugging-port` is **not** in the CLI's known-options list; it warns and forwards the
  flag to Electron, where the listener lives. Confirm with `/json/version` → `Chrome/<v> … Electron/<v>`.
- **Do not use 9222.** It is commonly already bound by a Chrome research window, in which case the
  DevTools listener never binds to VS Code and `/json/version` answers as Chrome.

### 2.2 A clean PATH, or Remote-SSH fails with `spawn EPERM`

Hermes's bundled `ssh.exe` lives inside a WindowsApps package and shadows the real one:

```
where ssh →
  C:\Program Files\WindowsApps\...HermesAgent...\git-...-win32-x64\usr\bin\ssh.exe   ← first, refused
  C:\Windows\System32\OpenSSH\ssh.exe                                                ← wanted
```

Windows refuses to spawn the packaged binary, so the remote never connects and the window shows
`Could not establish connection to "<host>": spawn EPERM`. A per-process `PATH` override was **not
sufficient** — `ssh` still resolved to the packaged one. The durable fix is a VS Code setting:

```json
"remote.SSH.path": "C:\\Windows\\System32\\OpenSSH\\ssh.exe"
```

Launch from a **script file**, not an inline `cmd /c`: nested quoting mangles the folder-uri and
produces `Windows cannot find '\\'`.

### 2.3 Chromium rejects every Origin header

```
Handshake status 403 Forbidden
```

Connect with no `Origin` at all — `websocket.create_connection(url, suppress_origin=True)`. This
avoids a relaunch with `--remote-allow-origins=*`.

---

## 3. Three layers, three techniques

Enumerate `http://127.0.0.1:9333/json/list`. Note what is **absent**: Copilot Chat.

| Panel | Appears as | Reach it via |
|---|---|---|
| Kilo Code | `iframe` target | its own target → `contentDocument` |
| Zoo Code | `iframe` target | its own target → `contentDocument` |
| **Copilot Chat** | **nothing** — native DOM | the `page` target |

> Concluding "the Copilot panel isn't open" because no webview target exists is a **false
> negative**. Check `document.body.innerText` on the `page` target for the panel's text first.

### 3.1 Webviews (Kilo / Zoo)

The extension UI is one nested frame deeper than the target:

```js
const d  = document.querySelector('iframe').contentDocument;
const ta = d.querySelector('textarea');
const set = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
set.call(ta, text);                              // plain ta.value = ... is ignored by React
ta.dispatchEvent(new Event('input', {bubbles: true}));
ta.focus();
```

Submit with a real Enter, **no `char` event** (a `char` inserts a newline instead of sending):

```python
Input.dispatchKeyEvent(type="keyDown", windowsVirtualKeyCode=13, nativeVirtualKeyCode=13,
                       key="Enter", code="Enter", text="\r", unmodifiedText="\r")
Input.dispatchKeyEvent(type="keyUp",   windowsVirtualKeyCode=13, nativeVirtualKeyCode=13,
                       key="Enter", code="Enter")
```

### 3.2 Copilot (native DOM / Monaco)

**The click must land on the `textarea.ime-text-area` rect.** `Input.insertText` does nothing
unless Monaco genuinely holds text focus, and clicking the visual centre of the chat surface is
not enough:

| Attempt | Result |
|---|---|
| `insertText`, no click | not landed, Send stays `disabled` |
| click surface centre (1575, 890) → insert | not landed, `disabled` |
| **click `.ime-text-area` rect (1330, 906) → insert** | **landed, `disabled → false`** |

**Pick the right textarea.** Several `ime-text-area`s exist — one belongs to the Output panel.
Select the one on the right of the window (`rect.x > 1000`), or you type into a log view.

Enter submits even when the Send button is absent from the DOM entirely (seen in plan mode, with
6 `chat-input-surface` nodes and 0 send buttons).

---

## 4. Verification (the part that stops you lying to the user)

A successful CDP call is not a successful task. Two cheap readbacks:

```js
// before: did the text land?
surface.querySelector('.view-lines').innerText.includes(text)     // NBSP! normalise first
// before: is Send now live?
/disabled/.test(sendBtn.className)                                 // false == ready
// after:  did it submit?
composer === "" && document.body.innerText.includes(replyMarker)
```

**Normalise U+00A0.** Monaco renders spaces as non-breaking spaces, so
`'git log --oneline -3' in composer_text` is `False` against a composer that visibly contains it.
A marker with no spaces in it (`CDP-RECV-OK`) passes anyway, which is exactly how this bug hides
for hours.

**Ask for a token back.** Give the agent a unique marker to echo (`… Reply with CDP-RECV-OK`), so
the reply itself is the proof rather than your own optimism.

---

## 5. State hazards (each one cost a wrong report)

### 5.1 The greyed-out Send arrow is the idle signal

When the composer is empty, Send carries the `disabled` class. That is unambiguous idle.

Two signals that **do not** work:

- **Button labels alone.** A hidden zero-width control
  `{"label":"Cancel restoring this checkpoint","vis":false,"w":0}` made an idle Copilot read as
  busy. Require `offsetParent !== null` **and** a non-zero `getBoundingClientRect()`.
- **Transcript length growth.** The chat DOM is virtualised: length *fell* `9956 → 7668` while the
  agent was actively working. Growth is noise in both directions.

### 5.2 Read only the newest turn

A transcript accumulates stale `BLOCKED`, `DONE`, and stale button labels. Scanning the whole body
for `/STEP .* BLOCKED/` or for a `Run` button returns `True` from an earlier turn and reverses your
conclusion. Slice from the last message **you** sent:

```js
const i = body.lastIndexOf('<phrase from your own last message>');
const newest = i >= 0 ? body.slice(i) : body.slice(-900);
```

### 5.3 Identify panels by extension globals, not by model name

Model strings change — Zoo's footer went from `subq-savant-1.4` to `deepseek-flash` — and then two
different panels collapse to one identity and one of them never gets nudged. Kilo injects
`window.KILO_*` into its webview; test for `kilocode\.kilo-code|KILO_TOP_BAR`.

### 5.4 Exclude `<script>` text from "last N nodes" reads

Kilo's webview contains the extension's boot script as a text node. A naive tree-walk returns
`window.KILO_SETTINGS = {};` as the "latest message". Skip `SCRIPT`/`STYLE`/`NOSCRIPT` parents.

### 5.5 Plan mode is read-only — it cannot execute a plan

Kilo Code's Plan mode refuses to run commands or write files, and says so:

```
STEP A1 BLOCKED: python -m pytest … > PLAN/logs/A1.log 2>&1
:: plan-mode is read-only — cannot run pytest or write non-plan files (and redirect is denied)
```

So *"put them in plan mode"* and *"give them a step-by-step execution plan"* are contradictory.
Plan mode writes the plan; an implementation mode executes it. Switch modes first, via the element
handle — the menu scrolls, and items sit at negative y (measured `Code` at `y = -333`), so a
coordinate click lands outside the panel:

```js
[...doc.querySelectorAll('.mode-switcher-trigger-label')][0].click();     // opens menu
[...doc.querySelectorAll('div,button,li,[role="menuitem"],span')]
  .filter(e => (e.innerText||'').trim() === 'Code' && e.children.length === 0)
  .pop().click();
// confirm by re-reading .mode-switcher-trigger-label — it must read 'Code'
```

Vendors differ: Kilo's Plan mode is genuinely read-only, while Copilot's Plan mode still wrote
`PLAN/logs/C1_PR5.md` and reported "Made changes". Do not generalise the restriction.

---

## 6. Keeping agents productive (the protocol that works)

Measured failure mode: an agent handed an open-ended request answers in ~10 seconds and ends the
turn **asking the operator to choose**. That looks like idleness and stalls the queue forever.

What converts a 10-second answer into git-visible work is a bounded step with a mandatory artifact:

```
STEP <id> DONE: <file path | commit sha | PR number>
STEP <id> BLOCKED: <command> :: <error>
STEP <id> BLOCKED: approval
```

Rules that did the work:

1. **One step per turn**, never "summarise the plan back".
2. **Every step ends in an artifact** someone can check without trusting the agent.
3. **Never ask the operator to choose** — pick the option that touches fewer files and say so.
4. **On an approval prompt, stop** and report `BLOCKED: approval`. Do not retry, do not work
   around it by hand-editing.
5. **Persist the plan in the repo** with checkboxes, so a successor agent reads the file instead
   of needing the chat history.

Note the hard ceiling: a keeper can nudge an idle panel, but it **cannot** clear an approval gate.
A panel parked on `Run`/`Deny` stays parked until a human or an auto-approve rule clears it.

---

## 7. Failure table (all observed, with the actual text)

| Symptom | Cause | Fix |
|---|---|---|
| `Handshake status 403 Forbidden` | Chromium rejects any Origin | `suppress_origin=True` |
| `Could not establish connection … spawn EPERM` | WindowsApps-packaged `ssh.exe` shadows System32 | `"remote.SSH.path"` setting |
| `Windows cannot find '\\'` | inline `cmd /c` quoting mangles the folder-uri | launch from a script file |
| `/json/version` answers as Chrome, not VS Code | port 9222 already bound by Chrome | use 9333 |
| insert does nothing in Copilot | clicked surface centre, not the textarea rect | click `ime-text-area` rect |
| composer clears, message never appears | submit target wrong; click didn't submit | verify text appears in transcript |
| agent looks busy but is idle | hidden zero-width `Cancel` | require visible + non-zero box |
| text landed in a log view | typed into the Output panel's textarea | pick the textarea with `rect.x > 1000` |
| `includes(cmd)` false though composer shows it | Monaco NBSP | normalise `\u00a0` → space |
| `STEP BLOCKED: plan-mode is read-only` | Plan mode cannot write/run | switch to `Code` |
| two panels share one identity | model name changed in footer | identify by `KILO_*` globals |
| `code chat` exits 0 and does nothing | no `VSCODE_IPC_HOOK_CLI` outside a VS Code terminal | don't use it; drive the panel |

---

## 8. Caveats

- `code chat` is not a substitute: outside a VS Code terminal it has no IPC hook, **exits 0**, and
  does nothing. Exit code is worthless as evidence.
- Sessions are per-window. Relaunching VS Code invalidates every attached websocket; re-attach.
- `iframe.contentDocument` is readable from *inside* the webview target but **cross-origin blocked
  from the page target** (returns zero-length text and looks like an empty panel).
- `Page.getFrameTree` on the page shows only the top frame; out-of-process webviews are separate
  targets, not child frames.
