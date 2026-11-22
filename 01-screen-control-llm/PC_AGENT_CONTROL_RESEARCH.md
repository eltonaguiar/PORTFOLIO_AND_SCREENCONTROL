# PC control by local AI — free options, architecture, and how to make agents stop stopping

Research date: 2026-11-22 · Target: Windows 11 workstation + Linux agents (VS Code Remote-SSH `eltonsGX10`, RustDesk) + logged-in browser sessions.
Nothing was installed for this report. Every "verified" item below was measured or read off this machine; everything else is cited.

**Companion files in this folder:** [`MEASUREMENTS.md`](MEASUREMENTS.md) (every number, with reproduction
commands), [`FACTCHECK.md`](FACTCHECK.md) (four popular LLM answers audited against the real repositories),
[`README.md`](README.md) (one-page summary and build order).

---

## 0. Bottom line

1. **There is no single "complete PC control" product worth adopting.** The free stack already exists in layers — you pick one *actuator*, one *perceiver*, one *supervisor*. Buying/installing a monolith buys you a worse version of the three.
2. **You already own the best local actuator**: `cua-driver 0.21.0` (from [trycua/cua](https://github.com/trycua/cua), MIT, 32.7k★, pushed today). Verified on your box: UIAutomation reachable, D3D11/Windows Graphics Capture OK, background input that does **not** move your cursor or steal focus.
3. **OCR is not the hard part — but it is a coarse instrument.** RapidOCR read your Copilot Chat panel's prose and button labels (`Keep`, `Undo`, `Describe what to build`, `Allow all`) correctly, and mangled the embedded Python badly (`2006-11-30` → `2886-11-38`, `A/B` → `AOA`, `/tmp/p6/...` → `/tmp/ p6/...`), at **19.0 s per full frame**. So: OCR for "what is this panel, is it busy, which button is there" — never for code, numbers, or evidence. The hard part is deciding *"has it stopped, or has it finished?"* and supplying **information**, not encouragement.
4. **You already have the wrong primitive installed.** `dealenx.go-auto-continue-0.0.2` sends a configurable phrase ("continue") into chat every N seconds on a timer. Blind re-sends make loops longer, burn quota, and teach the model nothing. The replacement is ~200 lines of event-driven supervisor (design in §5).
5. **For the Linux agents: do not use RustDesk as the control channel.** RustDesk gives you pixels and nothing else — no accessibility tree, no exit codes, no transcript, no git. If SSH is available, control over SSH and watch over RustDesk. Pixels are the fallback, not the plan.
6. **Scope is "anything on screen", so build one kernel, not one bot per app.** A single perceive→resolve→act→verify loop with a *capability ladder* (API → accessibility → text/OCR → element detection → coordinates) covers VS Code, browsers, consoles, JetBrains, Office, Explorer, RustDesk and games. What changes per app is only **which rung of the ladder answers** (§4.5–4.6).

---

## 1. Verified on this machine (measurements, not doc quotes)

| Finding | Evidence |
|---|---|
| RTX 5070, 12 GB VRAM, driver 617.42 | `nvidia-smi` |
| Local VLMs available: `qwen3-vl:2b/4b/8b`, `llama3.2-vision:11b`, `devstral:24b`, plus LM Studio runtime | `ollama list`, `~/.lmstudio` |
| **4B VLM throughput on real work**: 1259-token screenshot prompt → 77 tok/s generation, ~8 s per 600-token answer | timed Ollama call on a 1456×818 VS Code frame |
| **Chat VLMs are bad grounders**: `qwen3-vl:2b/4b/8b` via Ollama ignore `"think": false`, emit `<think>…`, and consume the entire output budget without ever printing coordinates (2b 3.7 s, 4b 9.3 s, 8b 10.2 s — all empty responses at 60 tokens; still empty at 600) | probe script, 3 models × 2 prompts |
| **VS Code is invisible to Windows UI Automation as configured** — `capture(mode=ax)` on the Code window returned exactly 3 elements (Minimize/Maximize/Close), no bounds, no editor, no chat | cua-driver AX capture |
| **OCR is good on prose, bad on code**: RapidOCR read the chat column's English text and button labels correctly, but mangled the embedded Python and every number (`2886-11-38` for `2006-11-30`, `AOA` for `A/B`, `n-(n)d` for a format string) — 106 boxes, **19.0 s for the full 1456×818 frame** | RapidOCR pass over the same frame |
| **VLM label reading is model-size dependent**: "which action button sits under the diff summary?" → `Keep` in ~1.0 s from `qwen3-vl:4b` and `:8b`; **`qwen3-vl:2b` returned an empty answer** on the same prompt | probe2, 3 models |
| **OCR needs a crop, not a full frame**: 19 s end-to-end makes full-frame OCR unusable inside a control loop; the chat panel alone is ~400×800 and OCRs in a fraction of that | timing above |
| `cua-driver` health: UIAutomation ✅, Windows Graphics Capture ✅, MCP session active | `hermes computer-use doctor` |
| GitHub Copilot CLI **1.0.49** installed, supports `--autopilot`, `--max-autopilot-continues`, `--allow-all`/`--yolo`, `--resume`, `--output-format` | `copilot --help` |
| **Copilot quota is currently exhausted**: a live `--autopilot` smoke test returned `402 … You have exceeded your monthly quota` and made 0 changes | real run in a scratch dir |
| Installed agent tooling: `anthropic.claude-code 2.1.33x`, `kilocode`, `kimi-code`, `openai.chatgpt`, `openclaude`, `openrouter`, `dealenx.go-auto-continue` | `~/.vscode/extensions` |

Two consequences worth internalising:

- **The quota failure is the textbook case for a supervisor that classifies stop reasons.** "Continue" cannot fix a 402. An agent that re-sends `continue` into a quota-exhausted session wastes your time and, in credit-metered harnesses, your money.
- **Accessibility is a switch, not a given.** `editor.accessibilitySupport: "on"` (or launching with `--force-renderer-accessibility`) turns the VS Code Electron tree on and gives you the chat transcript as text — no OCR, no vision, no ambiguity. Same class of switch exists everywhere: Chromium `--force-renderer-accessibility`, Linux `AT_SPI_BUS`, macOS VoiceOver APIs.

---

## 2. The five layers (keep them separate)

| Layer | Job | Best free choice | What breaks if you skip it |
|---|---|---|---|
| **Actuator** | move mouse, send keys, click a control | `cua` / `cua-driver` (MIT); Windows-MCP (MIT); AutoHotkey v2 (GPL-2.0) for deterministic macros | coordinates drift, focus theft, DPI breakage |
| **Perceiver** | know what's on screen | UIA / AT-SPI first, then RapidOCR, then a grounding model | you OCR a screenshot and lose hit targets |
| **Grounder** | "where is X?" in pixels | UI-TARS / ShowUI-2B / OmniParser (dedicated) — **not** a chat VLM | 10 s per frame and empty answers (measured) |
| **Orchestrator** | decide the next action, own the loop | Copilot CLI `--autopilot`, Copilot SDK, Claude Code Stop hooks, Agent-S, or your own loop | the agent stops at every turn boundary |
| **Supervisor** | judge *progress vs. stall*, inject facts, enforce budget | **nothing off the shelf** — ~200 lines bespoke (§5) | blind `continue` forever |

---

## 3. The catalog (licenses/stars/last-push verified via GitHub API on 2026-11-22)

### 3.1 Actuators — desktop control

| Project | License | ★ | Last push | Notes |
|---|---|---|---|---|
| **trycua/cua** (`cua-driver`, `cua-computer`) | MIT | 32.7k | 2026-11-22 | Cross-platform (Win/mac/Linux), **background** input, UIA + AT-SPI + X11, MCP server, sandbox VMs, trajectory recording. Already installed here and healthy. |
| **CursorTouch/Windows-MCP** | MIT | 12.0k | 2026-11-22 | Pure Windows, ~19 tools (Screenshot, Snapshot, Click, Type, App, Shell, Registry…), UIA-based, vision optional, `--tools`/`--exclude-tools` allowlists. Best drop-in for Claude Desktop/Cursor. |
| **pywinauto** | BSD-3 | 6.5k | 2026-11-08 | Library, not agent. `backend="uia"` gives you the real control tree; the reference for "click the button named Save". |
| **FlaUI** | MIT | 3.2k | 2026-08-13 | .NET UIA wrapper; same role as pywinauto if you prefer C#. |
| **AutoHotkey v2** | GPL-2.0 | 13.5k | 2026-11-20 | The reliable deterministic layer: hotkeys, `Send`, window activation, COM/UIA access. Ideal target for "AI picks the macro, macro does the clicking". |
| **AutoIt** | freeware | — | — | Free but closed; `ControlClick`/`WinWait` are rock-solid for old Win32 dialogs. |
| **Jitbit Macro Recorder** | freeware | — | — | Records mouse/keys, editable script (JitScript). **CLI: `MacroRecorder.exe "macro.mcr" /a` plays immediately** (+ `/c` closes after). No AI API and no parameter passing — so "AI-controlled" means *templating the .mcr text and replaying it*, or driving its UI. Fine as a deterministic executor, wrong as the brain. |
| **Pulover's Macro Creator** | free (AHK v1) | — | — | Recorder/editor that emits AutoHotkey; can run `.ahk` from CLI. Same niche as Jitbit, open and inspectable. |
| **SikuliX → Oculix** | MIT | — | — | Image-template matching + OCR. Upstream SikuliX archived Mar 2026; **Oculix** is the MIT continuation. Use only where there's no selector at all. |
| **UI.Vision RPA** | AGPL-3.0 (dual) | 1.9k | 2026-10-02 | Browser-native macros + XModules for desktop; has OCR and a JS API; CSV-driven runs. Great for browser flows, AGPL if you modify. |
| **Robot Framework + `rpaframework`** | Apache-2.0 | 1.6k | 2026-11-20 | Python/Robot DSL, actively released (33.0.2, Oct 2026), covers browser/API/files **and** desktop modules. The maintainable choice if you want tests-as-automation. |
| **OpenRPA** | MPL-2.0 | 3.1k | 2026-11-09 | UiPath-like designer, Windows-only; last tagged release Jun 2025. Orchestration via OpenFlow (not free). |
| **TagUI** | Apache-2.0 | 6.4k | 2026-11-08 | Plain-English scripting, easiest on-ramp; AI Singapore discontinued maintenance. Freeze-only. |
| **simular-ai/Agent-S (S3)** | Apache-2.0 | 13.0k | 2026-11-22 | Full computer-use agent framework, cross-platform, SOTA-lineage, bring your own model (local or API). Closest thing to "a free operator" you can point at a task. |
| **microsoft/UFO²** | MIT | 10.2k | 2026-10-30 | Windows AgentOS from MS Research: **hybrid UIA + vision + app APIs**, multi-agent, "non-disruptive execution". Best reference architecture for exactly the problem you described. |
| **OpenInterpreter** | Apache-2.0 | 68.9k | 2026-11-22 | Code-execution-first agent that can also drive the desktop; runs local models. |
| **bytebot-ai/bytebot** | Apache-2.0 | 11.1k | 2025-09-12 | Self-hosted computer-use agent in a Linux desktop VM; stale-ish but the containerised pattern is useful. |

**Reliability ladder** (do not skip rungs): app API / CLI → DOM/CDP → UIA/AT-SPI selector → vision grounding on a dedicated model → image template → raw coordinates. Every rung down costs ~an order of magnitude in flake rate.

### 3.2 Perceivers / grounders

| Tool | License | Notes |
|---|---|---|
| **Windows.Media.Ocr** (built into Win10/11) | free, no install | Zero-dependency OCR via WinRT; genuinely good on UI text and fast enough for a perceive-act loop (tens of ms on a UI-sized frame; I did not benchmark it here). Callable from PowerShell 5.1 (`[Windows.Media.Ocr.OcrEngine]`), C#, or Python via `winsdk`. |
| **RapidOCR / PaddleOCR** | Apache-2.0 | **Already installed here** (`rapidocr_onnxruntime`). Reliable on prose and button labels; unreliable on code/numbers; 19 s for a full 1456×818 frame with 106 boxes, so **always crop to the region** you care about. Returns text + boxes, so results double as hit targets. |
| **Tesseract** | Apache-2.0 | Weakest on anti-aliased UI text; keep only as a fallback. |
| **microsoft/OmniParser v2** | CC-BY-4.0 (repo) | Icon detector + captioner + OCR → Set-of-Marks element list with IDs and semantics. This is the piece that makes a *chat* model able to click accurately; run it locally (V2 checkpoints) or via OmniTool in a Win11 VM. |
| **showlab/ShowUI-2B** | Apache-2.0 | 2B grounding model, 75.1% zero-shot ScreenSpot. Fits your 12 GB card with room to spare. |
| **UGround (2B/7B)** | MIT | Pure-vision grounding; 10M-element training set; see the SeeAct-V framework. |
| **bytedance/UI-TARS-desktop** | Apache-2.0 | End-to-end GUI agent model + desktop app + SDK; grounding SOTA for its size class; MCP support. |
| **Qwen3-VL (2B/4B/8B)** | Apache-2.0 | You have it. Excellent *reading*, poor *grounding* in this Ollama build (see §1). Use it for "what does this panel say", not "where do I click". |
| **screenpipe** | NOASSERTION (check) | Local 24/7 screen+audio capture, a11y-tree/OCR text into SQLite, REST + MCP. This is your **audit trail / memory** layer ("what did the agent actually see at 14:32"), not a controller. |

### 3.3 "Keep going" features already built into harnesses (free)

| Harness | Native mechanism | Detail |
|---|---|---|
| **Copilot CLI** | `--autopilot` + `--max-autopilot-continues N` | In autopilot, if the model stops without calling `task_complete`, the CLI **injects a synthetic user message**: *"You have not yet marked the task as complete… If you were planning, stop planning and start implementing. You aren't done until you have fully completed the task."* That restarts the tool loop. Pair with `/goal <objective> --max-ai-credits N` for a spend cap. `--plan --mode autopilot` = plan then auto-continue without approval. |
| **Copilot SDK** | `session.idle` vs `session.task_complete` | `session.idle` **always** fires when the loop ends; `task_complete` only if the model said so. So: `if idle and not task_complete → your supervisor decides`. This is the cleanest programmatic hook that exists for "it stopped but isn't done". |
| **Claude Code** | `Stop` hook | A hook can block the turn from ending (exit code / JSON `decision: block`) so the model keeps working. Guard with `stop_hook_active` and a counter — per the hook docs/community write-ups Claude Code ends the turn itself after 8 consecutive continuations, which is the built-in circuit breaker. |
| **VS Code Copilot Chat** | `chat.agent.maxRequests` (raise well above default) + the auto-approve family, plus `.github/copilot-instructions.md` "beast mode" text: *"keep going until the query is completely resolved… keep working until every todo item is checked off"* | Community-proven (burkeholland's "Beast Mode"); verify key names in the current Settings UI — this build's extension is bundled, not on disk to grep. |
| **Kilo Code / others** | own autopilot toggles | Present in your install; same idea. |

Ranking: **harness-native continuation > instruction-file pressure > GUI injection.** GUI injection is social engineering of a vendor's UI; it breaks on every redesign and can't see why the agent stopped.

### 3.4 Browsers (for the "check my LinkedIn" class of task)

| Tool | License | Notes |
|---|---|---|
| **ChromeDevTools/chrome-devtools-mcp** | Apache-2.0 | 58.7k★, pushed today. Official Google MCP; `--autoConnect` attaches to the Chrome you're already logged into (with a user consent prompt), or point it at a debug port. |
| **microsoft/playwright-mcp** | Apache-2.0 | 40.0k★. Accessibility-snapshot-driven; strong for repeatable flows. |
| **browser-use/browser-use** | MIT | 121.7k★. LLM-driven navigation on top of Playwright; good for exploratory "go find X". |
| **UI.Vision RPA** | AGPL-3.0 | Record/replay in the user's own browser profile with visual assertions + OCR. The "deterministic clicks" half of a login flow. |

**Chrome 136+ gotcha (verified in Chrome's own blog):** `--remote-debugging-port` and `--remote-debugging-pipe` are **ignored on the default user-data dir**. To attach to a logged-in profile you must either (a) launch with `--user-data-dir` pointing at a copy/non-standard path, or (b) use the sanctioned interactive route (`chrome://inspect` / DevTools MCP `--autoConnect`) where the user clicks **Allow**. There is no silent flag-only path to the real profile any more.

---

## 4. Four topologies — pick per target, not globally

| # | Target | Perception available | Control available | Verdict |
|---|---|---|---|---|
| **A** | This Windows box (VS Code, Copilot, Explorer, Office) | UIA tree (once a11y is on) + D3D screen capture + OCR | background clicks/keystrokes that don't steal focus | **Richest.** Do everything here. |
| **B** | Linux host reachable by SSH (`eltonsGX10`) | AT-SPI tree over DBus, files, stdout, exit codes, git | `xdotool`/`ydotool`, app CLIs, `git`, remote agent CLIs | **Best for agents.** Skip the GUI entirely wherever a CLI exists. |
| **C** | Linux host *only* via RustDesk | pixels (compressed, possibly scaled) | synthetic input into the RustDesk viewer window | **Last resort.** Everything is a vision problem; you also inherit scaling artifacts and focus rules. |
| **D** | Browser session (LinkedIn, portals) | DOM + CDP + a11y snapshot | CDP clicks/typing, JS, or real input | **Use CDP, not pixels.** Chrome 136 profile caveat in §3.4. |

### 4.1 Linux without a monitor (topology B) — the recipe that avoids pixels

```bash
# from the Windows side, over the existing SSH path
ssh eltonsGX10 'echo $DBUS_SESSION_BUS_ADDRESS; echo $AT_SPI_BUS_ADDRESS'   # must be the *session* addresses
# inside a session: pyatspi / libatspi reads the tree
python3 -c "import pyatspi; d=pyatspi.Registry.getDesktop(0); print([a.name for a in d])"
# typing without a display server:
ydotool type "text"            # Wayland/uinput, needs a daemon + permission
xdotool key --clearmodifiers ctrl+s   # X11 only
```
Notes that matter: AT-SPI needs `DBUS_SESSION_BUS_ADDRESS` **and** `AT_SPI_BUS_ADDRESS` from the *same* logged-in session (a fresh ssh shell does not inherit them — read them from the running session's `/proc/<pid>/environ`). On Wayland, `xdotool` is a no-op; `ydotool` needs `uinput` access. If the box has no display at all, either run apps under `Xvfb` (+ `dbus-run-session`) or don't automate the GUI — automate the CLI, which is what an agent should be doing on Linux anyway.

### 4.2 RustDesk (topology C) — what to do differently

- RustDesk forwards synthetic mouse/keys, so injection works — but **everything you know about the remote app is a picture**. Budget ~200–500 ms per perceive→act cycle, plus 1 model call.
- Force the viewer to **100% scale, no "fit window"**, and anchor all coordinates to the *remote* resolution you read from the stream; otherwise every click is off by the zoom factor.
- Compression artifacts hurt OCR on small text; crop-and-upscale the region of interest (2×) before OCR. Measured rule of thumb: full-frame OCR is fine for prose, region-crop+2× is what saves 9-px UI labels.
- Detect "is it still working?" from pixels: a spinner/Stop-button present = busy. Never inject "continue" while busy — you'll queue a message that lands mid-turn and derails it.
- Prefer RustDesk for **watching** and SSH for **acting**: same host, different channels.

### 4.3 Browser (topology D) — LinkedIn-shaped tasks

1. Never headless, never a fresh profile for a logged-in task.
2. Attach over CDP (`--user-data-dir=<copy>` + `--remote-debugging-port`, or DevTools MCP `--autoConnect` with the user's Allow click).
3. Human cadence: 80–250 ms between keys, no instant `navigate` after a click, scroll in increments. Automation that outruns a human is the #1 signal these sites score.
4. **Login, 2FA, CAPTCHA, "verify it's you" → stop and hand back.** Never type a credential the user didn't hand you for that session; never solve a challenge silently.
5. Read state from the DOM/a11y snapshot, act from the DOM; use vision only for canvas widgets and image CAPTCHAs (which you don't touch).

---

## 4.5 Any app on screen — the universal surface matrix

The kernel is the same everywhere; what varies is **which channel exists**. Probe cheaply (one capture + one a11y walk), record the ceiling, cache it per `(process, window class, dpi)`.

| Surface class | Best channel (rung 1–2) | Fallback (rung 3–4) | Sharp edges |
|---|---|---|---|
| **Native Win32 / WinForms / WPF** | UIA Control view: `InvokePattern`, `ValuePattern`, `SelectionPattern`, `TextPattern` via pywinauto `backend="uia"` or cua-driver elements | OCR on the owner-drawn region → vision grounding | Owner-drawn controls expose no children; deep trees are slow (scope `FindFirst`, use a `CacheRequest`); some controls lie about bounds |
| **Electron / Chromium apps** (VS Code, Slack, Teams, Discord, Obsidian, Postman) | Force a11y on → the whole DOM-like tree appears: `--force-renderer-accessibility`, VS Code `editor.accessibilitySupport: "on"`, each app's screen-reader mode. **Bonus: Electron accepts `--remote-debugging-port` and then CDP drives the renderer** — the single biggest reliability win per app | Screenshot + OCR (prose/buttons) → vision for dense UI | A11y **off by default** = bitmap (measured: VS Code returned 3 elements). Relaunch required; some apps ship `a11y` flags only in dev builds |
| **Terminals / consoles** (Windows Terminal, conhost, mintty, WSL, SSH) | **Do not type into a terminal you can own**: keep the process, read its stdout/exit code. For an agent that lives in one: run it inside **tmux** — `tmux send-keys`, `tmux capture-pane -p` is a universal, scriptable PTY channel that also survives disconnects | UIA `TextPattern` on Windows Terminal/conhost buffer; OCR for mintty (exposes almost nothing) | Typing into a terminal you don't own is a race with the program's own prompt; escape sequences and repaint break OCR; never parse ANSI through OCR — capture the stream |
| **Browsers** (Chrome, Edge, Firefox) | CDP for Chromium (DOM, JS, network, iframes), Marionette/WebExtension for Firefox, `chrome-devtools-mcp --autoConnect` to the logged-in profile | Forced-a11y UIA tree inside Chromium; OCR of the rendered page | Chrome 136+ ignores the debug port on the default profile; native file pickers are OS dialogs, not DOM; cross-origin iframes need CDP frame targeting |
| **Java / Swing / AWT** (JetBrains IDEs, some enterprise tools) | **Java Access Bridge** → surfaces through UIA; JetBrains also exposes a remote-dev backend and CLI | OCR + vision | JAB is off unless enabled (`jabswitch -enable`, or the IDE's screen-reader mode); without it the window is a bitmap |
| **Remote desktop clients** (RustDesk, AnyDesk, TeamViewer, mstsc/RDP, VNC, Parsec) | Treat as *pixels inside a local window*; use clipboard and file-transfer/redirect as a **non-pixel data channel** (RDP drive redirection, `xfreerdp /drive`, RustDesk file transfer) | Vision grounding on a crop; OCR for read-back | Map local→remote coordinates (never "fit window"); force 100 % scale; compression ruins small text → crop + 2× upscale; latency means every act needs a longer settle; never inject while the remote is busy |
| **Games / DirectX / canvas / CAD viewports** | None — vision only, foreground input only | Grounder + raw coordinates on a proven-static layout | Anti-cheat rejects synthetic input; no text layer; out of scope unless explicitly asked |
| **Phone (scrcpy)** | `adb shell input tap/swipe`, `uiautomator dump` — a real API, not pixels | scrcpy window + vision | USB debugging handshake; slow `dump` on big screens |
| **VMs / hypervisor consoles** (VMConnect, VMware, VirtualBox) | Guest agent / SSH / RDP into the guest | Pixels of the console window | Console is a framebuffer; keyboard capture quirks; guest tools matter |
| **Multi-monitor / DPI / virtual desktops** | Per-monitor-v2 DPI awareness; window-relative math | — | 125/150 % scaling silently offsets every coordinate; capture must be scoped to a window, not "the screen" |

**The one rule:** structure before pixels. Every rung down costs ~an order of magnitude in reliability, and each app class above has a documented way to climb back up.

## 4.6 The surface resolver (how "anything" becomes tractable)

```
resolve(window) -> Surface
  1. native channel?      app CLI/COM/extension API/CDP endpoint/adb/tmux  → Surface(kind=api)
  2. a11y probe?          walk Control view; count nodes with (label, bounds) > N
                          → Surface(kind=selector, nodes=[...])
  3. text layer?          UIA TextPattern, else OCR on a crop
                          → Surface(kind=text, lines=[(text, box)])
  4. element detection?   OmniParser / ShowUI / UI-TARS over the frame
                          → Surface(kind=marks, marks=[(id, box, label, interactable)])
  5. coordinates          only for surfaces proven static
                          → Surface(kind=pixels)
```
Cache the result and the rung; invalidate on resize, theme change, app update, or two failed verifications in a row. The probe is cheap (one capture + one tree walk) and it is what lets one agent handle VS Code, a console, LinkedIn and RustDesk without four codebases.

**Universal action grammar** — twelve verbs cover every GUI; everything else is composition:

`activate(element)` · `set_value(element, text)` · `click(point)` · `type(text)` · `key(combo)` · `scroll(dir, n, at)` · `drag(a→b)` · `focus(window)` · `read_text(region|element)` · `clipboard_get/set` · `window(op)` · `wait_for(predicate)`

Map each to the best available mechanism (UIA pattern → `SendInput` → CDP → pixel) and **verify with a re-read of the smallest region that should have changed** (element value, crop hash, or a text diff). Verify → escalate → re-verify is the loop; never retry blindly.

---

## 5. The supervisor: how to take charge and stop stopping

The goal isn't "send continue". It's **replace the human's judgment at the turn boundary**. Four things a human does that a timer can't:

1. decides *is this done, stalled, blocked, or looping*;
2. supplies the missing **fact** (full error, the file it hasn't opened, the decision it's avoiding);
3. restates the **definition of done** and the next single step;
4. calls **stop** when continuing is waste.

### 5.1 Classify the stop before acting

| Observed at the boundary | Real cause | Action |
|---|---|---|
| Last message is "Next I'll …" with no tool call | turn-limit / model politeness | **Continue**, with a nudge that forbids plan-only turns |
| "Should I …?" on a non-destructive, allowlisted op | approval reflex | **Auto-approve + continue** (or fix the harness allowlist so it stops asking) |
| Open question that only the user can answer (product decision, credentials) | genuine block | **Escalate to human** — this is what you want to be interrupted for |
| Same command, same output, twice | loop | **Do not continue.** Inject diagnosis (§5.3) |
| Test/exit-code unchanged across N attempts, no diff | no-progress | **Steer** to a different hypothesis; cap at 2 |
| `402 quota`, `401`, expired token, disk full, port in use | environmental | **Stop and report.** Continuing cannot fix it |
| Summary matches DoD + verification command passed | done | **Stop, keep the diff** |
| Stop button/spinner still visible | still busy | **Do nothing** (never queue input mid-turn) |

### 5.2 Loop detection that actually works

Signature per step: `sha1(tool_name + normalized_args + normalized_output)`.

- same signature **twice** → stop continuing; the next message must contain a *new fact*.
- `git diff --stat` unchanged for 3 steps while tests fail → no progress.
- edit ping-pong: same file, opposite hunks, twice → freeze that file, ask for a written hypothesis.
- normalisation matters: strip timestamps, PIDs, absolute temp paths, and truncate output to the failing block — otherwise identical failures look different and you miss the loop.

### 5.3 The steer brief — this is the "insight into specifics" you asked about

Every injected message should be a **brief**, not a word:

```
STATE: 3 failed attempts on tests/test_runner.py::test_retry — same AssertionError (sig 9f2c).
GOAL (unchanged): make that test pass without touching retry.py's public API.
EVIDENCE: full traceback attached below; retry.py:88 sets max_attempts=1 before reading config.
ALREADY TRIED (do not repeat): raising the timeout; reverting commit 4a1f2e.
NEXT SINGLE ACTION: read config.py:40-70 and print the resolved value in the test.
VALIDATION: `pytest tests/test_runner.py -k retry` must go green; no other file may change.
```

Where the supervisor gets those fields from — this is why it must read the machine, not the chat:

| Field | Source |
|---|---|
| attempts / signatures | transcript adapter (CLI JSON, SDK events, PTY, OCR) |
| what really changed | `git status --porcelain`, `git diff --stat`, checkpoint hashes |
| real failure | the command's captured **full** stdout/stderr (not the agent's summary — truncated tails are the #1 cause of loops) |
| goal & DoD | `TASK.md` / `PLAN.md` with checkboxes, owned by the supervisor, rewritten each cycle |
| next step | a cheap local model (`devstral:24b`/`qwen3:14b` on your box) over the brief, or rules |

That last row is the important design choice: **keep the plan on disk, not in the context window.** Context compaction is what makes long agents "forget" they were mid-task; a `PLAN.md` with unchecked boxes survives every compaction, every model switch, and every crash.

### 5.4 Injection paths, best → worst

| Harness | Path | How | Verify with |
|---|---|---|---|
| Copilot CLI / Claude Code / any CLI | **flags** | `copilot -p "…" --autopilot --max-autopilot-continues 10 --allow-all --output-format json` | parse events; exit code |
| Copilot SDK | **JSON-RPC events** | send next prompt on `session.idle` without `task_complete` | event stream |
| VS Code Chat / vendor GUI | **UIA textbox** | focus chat input via UIA → `type` → `Enter` (cua-driver background) | read back the transcript text |
| Anything with no a11y | **pixels** | OCR the panel, locate the input box and the Continue/Keep control, click | OCR the reply header for "working/stopped" |

The GUI path is legitimate and sometimes the *only* path (a vendor agent with no API). But note what it costs: you're reading the agent's prose instead of its state, so the supervisor's judgment is only as good as the transcript you can OCR. Turn a11y on wherever you can.

### 5.5 Budgets and kill switches (non-negotiable)

- **Step cap** (e.g. 40), **wall clock** (e.g. 45 min), **credit/token cap**, **diff-size cap** (e.g. 1500 lines).
- **Denylist** of commands/paths (force-push, `rm -rf`, migrations, prod URLs, `.env`, keychains).
- **Git checkpoint before every run**; the supervisor's undo is `git restore`, never "ask the agent to undo".
- **One writer per repo/worktree** — parallel agents on one tree is how you get mystery regressions.
- **Kill switch**: a file (`STOP`) the loop checks each cycle, plus `process_manage` to terminate the child tree. Your memory notes you've been bitten by daemons that were killed with no verification — same rule applies here.
- **Audit trail**: ndjson log of every perceive/act/decision, plus optional screenpipe for the pixel record.

---

## 6. Guardrails and risks

| Risk | Reality | Mitigation |
|---|---|---|
| **Screen content is untrusted input** | A README, a web page or another agent's message can contain "click here / run this". Content on screen is data, never instructions. | Supervisor owns the goal; tool calls must map to the plan; strip instruction-like text from perception context or flag it for review. |
| **Credentials** | The vault rule applies to the agent too: never type a password/2FA/card, even if it "sees" one. | Stop at login walls; let the human authenticate; then attach to the session. |
| **Irreversible actions** | `git push --force`, migrations, sends, purchases, deletions. | Denylist + human approval gate + dry-run mode first. |
| **Anti-bot / ToS** | LinkedIn and friends detect cadence, fingerprint, headless flags. | Real profile, human cadence, low volume, stop on challenge. Assume your account is at risk if you go fast. |
| **Quota/credits** | Verified: your Copilot quota is out right now; a blind continue loop cannot fix it. | Classify before continuing; fail loud. |
| **Context compaction** | Long runs "forget" the task mid-way → the classic stop-with-narration behaviour. | `PLAN.md` on disk, re-injected every cycle. |
| **DPI / scaling** | 125%/150% display scaling silently offsets every coordinate. | Per-monitor-v2 DPI awareness; always compute screen→window-relative with the live window rect; verify one click before a batch. |

---

## 7. What I'd actually build (universal, phased, no purchases)

### Phase 0 — flip the structure switches (highest win per minute)

Every one of these converts a bitmap into a tree. Nothing to install; just config.

| App class | Switch | Effect |
|---|---|---|
| VS Code (and forks) | `"editor.accessibilitySupport": "on"`, or launch `code --force-renderer-accessibility` | whole workbench tree, incl. chat + terminals, becomes readable text |
| Other Electron apps (Slack, Teams, Discord, Obsidian) | their screen-reader/accessibility mode, or `--force-renderer-accessibility` in the launcher | same |
| JetBrains IDEs | `jabswitch -enable` (Java Access Bridge) or IDE "screen reader" support | editor/tool windows become selectors instead of pixels |
| Chromium browsers | attach CDP instead of reading pixels; a11y only as fallback | DOM instead of OCR |
| Windows Terminal / conhost | leave as-is (UIA `TextPattern` already works) | buffer text is readable |
| RustDesk / RDP viewers | 100 % scale, no "fit to window", file transfer/clipboard enabled | stable coordinate mapping + a non-pixel data channel |

### Phase 1 — the kernel (one codebase, every app)

Three modules, ~400 lines total, using what's already on this box:

```
capture.py   # window-scoped capture (D3D/Graphics Capture), per-monitor-v2 DPI math,
             # crop helper, screen<->window<->client coordinate transforms
resolve.py   # the §4.6 ladder: api → selector → text/OCR → marks → pixels; cached per window class
act.py       # the §4.6 twelve verbs over UIA patterns / SendInput / CDP / pixels,
             # each returning a verdict, with verify(crop|element|text) built in
```

Acceptance test for the kernel: one script drives **four different surfaces in one run** — TypeScript in VS Code's editor, a command in Windows Terminal, a file rename in Explorer, a page in Chrome — each with a post-action verification, no per-app code. If it can't, the ladder is wrong, not the app.

### Phase 2 — channel upgrades (replace pixels where a real channel exists)

- **Terminals:** run long-lived agents inside `tmux`; `send-keys` + `capture-pane -p` becomes your universal console adapter (and it survives disconnects — the reason your agents die mid-task today).
- **Browsers:** Chrome DevTools MCP `--autoConnect` (or a copied profile + debug port) → DOM, not pictures.
- **Electron apps:** `--remote-debugging-port` where the app allows it → CDP into the renderer.
- **Linux hosts:** SSH + AT-SPI + `xdotool`/`ydotool`; RustDesk stays a viewer.
- **Phones:** `adb` + `uiautomator` instead of mirror pixels.

### Phase 3 — the supervisor (§5)

`overseer.py`: task ledger (`TASK.md`), transcript adapters (CLI JSON / SDK events / UIA textbox / OCR), signature hashing, stop-reason classifier, decision table §5.1, injected briefs §5.3, budgets + `STOP` file, ndjson audit. Built on top of the kernel so it can read *any* agent's window, not just Copilot's.

### Phase 4 — the residue (only where nothing else works)

RustDesk pixels, games, CAD viewports: add a grounding model. On this 12 GB card: **ShowUI-2B** (Apache-2.0, 75.1 % ScreenSpot) or **UI-TARS-2B** for direct grounding; **OmniParser v2** if you want an element list with labels instead of a bare coordinate. Do not attempt this with `qwen3-vl` as a grounder (measured failure, §1).

**Coverage check** — after all phases, every surface you named is handled:

| You said | Handled by |
|---|---|
| VS Code (editor, chat, terminal panel) | a11y switch → selectors; Electron CDP if wanted |
| Browser (logged-in sessions) | CDP + human cadence; a11y/OCR fallback |
| Console | tmux/PTY stream; UIA TextPattern; OCR last |
| RustDesk / remote desktop | pixel channel + clipboard/file transfer; grounder for the residue |
| Anything else on screen | kernel ladder, no per-app code |

**Deliberately skipped:** monolithic "AI PC control" suites, image-template matching as a primary strategy, per-second `continue` timers, and any cloud computer-use API (all of it is either redundant with the above or sends your screen off-machine).

---

## 8. Sharp edges (things that will bite)

1. **Chat VLMs ≠ grounders.** Measured: qwen3-vl ignores `think:false` in this Ollama build and burns the budget thinking. Use `qwen2.5-vl`, a dedicated grounding model, or parse `thinking` and re-prompt with "answer only".
2. **Electron/Chromium a11y is off by default** → the product you're driving looks like a bitmap. Flip the switch; don't build an OCR pipeline around a config toggle.
3. **Background input hits a wall on some Electron consent dialogs / DirectInput surfaces** → escalate to foreground deliberately, as a *reaction* to a failed verification, never as a guess.
4. **Truncated tool output is the #1 loop cause.** Give the agent the full failing block before you give it "continue".
5. **`session.idle` fires on every turn end**, including successful ones — never treat it as "done".
6. **RustDesk scaling/compression** corrupts coordinates and small text; crop+upscale for OCR.
7. **Two agents, one worktree** = corrupted state. Worktrees or separate clones, always.
8. **A "Continue" click during an active turn is queue-poisoning.** Check busy/stopped first.

---

## 9. Sources

- trycua/cua · CursorTouch/Windows-MCP · microsoft/UFO (UFO²) · simular-ai/Agent-S · OpenInterpreter · bytebot · pywinauto · FlaUI · AutoHotkey · TagUI · OpenRPA · rpaframework · screenpipe · ShowUI · UGround · OmniParser · UI-TARS · browser-use · playwright-mcp · chrome-devtools-mcp — all via GitHub API (license/★/last push) on 2026-11-22.
- UI-TARS paper: <https://arxiv.org/abs/2501.12326> · OmniParser: <https://arxiv.org/abs/2408.00203> · ShowUI: <https://arxiv.org/abs/2411.17465> · UGround: <https://arxiv.org/abs/2410.05243> · ZonUI-3B (3B grounding on one 4090): <https://arxiv.org/abs/2506.23491> · UFO²: <https://arxiv.org/abs/2504.14603>
- Copilot CLI autopilot: <https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/use-autopilot-mode> · Copilot SDK agent loop (`session.idle` / `task_complete`): <https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/agent-loop> · CLI command reference (`/goal`, `--max-autopilot-continues`, restore): <https://github.com/github/docs/blob/main/content/copilot/reference/copilot-cli-reference/cli-command-reference.md>
- Claude Code Stop hooks + `stop_hook_active`: <https://code.claude.com/docs/en/hooks>
- Beast Mode / VS Code agent settings: <https://gist.github.com/burkeholland/88af0249c4b6aff3820bf37898c8bacf>
- Chrome 136 remote-debugging change: <https://developer.chrome.com/blog/remote-debugging-port>
- Jitbit Macro Recorder CLI playback: <https://www.jitbit.com/macro-recorder/playing-macros-command-line/>
- AT-SPI2 architecture: <https://www.freedesktop.org/wiki/Accessibility/AT-SPI2/> · pyatspi: <https://github.com/GNOME/pyatspi2>
- Copilot "stops after saying what it plans" (community thread): <https://github.com/orgs/community/discussions/184524>
