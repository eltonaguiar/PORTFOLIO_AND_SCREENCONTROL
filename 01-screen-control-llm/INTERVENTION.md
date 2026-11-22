# Human intervention — how the agent hands off instead of guessing

Three ways a human can be in the loop, and what each one is actually good for. The measured facts in
§1 come from this machine, 2026-11-22; the policy in §3 is the recommendation.

## 1. What exists right now (measured)

| Surface | State | Use |
|---|---|---|
| Windows desktop, Chrome on **monitor 2** (window origin ≈ `(1920, 58)`) | live, logged in to ChatPlayground | attended automation; the user can see and take over instantly |
| `http://192.168.2.52:6080/vnc.html` (noVNC) | **HTTP 200 from this host** | remote observation / intervention on the Linux box |
| `192.168.2.52:22` | open | the *correct* automation path for that box (SSH), VNC is only for watching |
| `192.168.2.52:5900` | **closed from outside** | good: websockify proxies it, the raw VNC port is not exposed |
| `192.168.2.52:3000` | open | unclaimed service; identify before relying on it |

Two input findings from the live run, both worth more than they look. The window was measured
directly afterwards with `kernel.capture`: **hwnd 36899254, window rect (1912, 50, 1376, 736),
client 1360×720, `dpi_scale = 1.0`** — monitor 2, 100% scaling, so the early "2.42× scale" reading
from the tool's own caption was wrong and misled the first two clicks.

- **`coordinate=` is window-relative; element `bounds` are desktop-absolute.** Passing `(700, 960)`
  and `(3108, 739)` — computed from a screenshot, treated by me as native — produced posts at
  `(2621, 1019)` and `(5029, 798)`: the driver adds the window origin `(1912, 50)` and, because both
  points lay outside the 1360×720 client area, delivered them *outside the window*. The first cleared
  the open conversation. Element hits need no arithmetic: clicking *element #87 'Send to every model'*
  landed at `(3127, 746)` and sent the message. **Rule: elements, never coordinates.**
- **The window's own accessibility tree is the map**, once Chrome's renderer accessibility is awake.
  The first capture returned 24 elements (tabs and buttons only); after one `som` capture the same
  window returned 95–129 elements including `Edit 'Message every model'`, per-panel
  `Regenerate`/`Copy message`, and the live regions below. A first probe returning only furniture is a
  *retry signal*, not a verdict — that correction now lives in `kernel/resolve.py`.

Resolver caching was exercised against this same window: the second resolve made **0 probes**
(cached), and a synthetic 208 px resize forced **2 probes** — invalidation works on live geometry.

## 2. Three intervention models

**(a) Unattended, headless CDP.** `browser_exec` / Playwright with its own profile. Fast, cheap,
invisible, works with the screen locked. The human cannot see it, so a login wall, 2FA, captcha or
consent dialog is unrecoverable *unless the agent parks and asks*.

**(b) Attended, live window.** The agent drives the user's real Chrome (this run). The user can watch,
can grab the mouse, and will notice a popup on their own. Costs: the user's session is shared state
(a stray click can clear their chat), and the window may be on another monitor or virtual desktop.

**(c) Remote overlay (noVNC / RustDesk).** A *shared view of the target machine*. The only option when
the host has no console (headless Linux, Session 0, a VM), and the only one that works from a phone.
Costs: pixels only — no DOM, no UIA, added latency, and it is a remote-control surface that must be
authenticated.

## 3. Policy: agent-initiated handoff, not continuous watching

The user should not have to babysit. The agent should **stop at a gate, say exactly what it needs, and
stay parked** — then resume on an explicit signal.

```
RUNNING ──detect gate──▶ PAUSED_NEEDS_HUMAN ──signal──▶ RUNNING
                │                                    └──▶ ABORTED (user says no)
                └── artifact: screenshot crop, the control that blocked it,
                    the URL, and the one action required ("choose your Google account")
```

Gates that always pause (never guessed, never typed):

| Gate | Detected by | What the agent does |
|---|---|---|
| Password / 2FA / captcha field | `Edit` with label matching `password`, `code`, `verification`; or an `iframe` captcha | screenshot + URL + "human: complete the sign-in" |
| Consent / permission dialog | a modal role with `Allow`, `Deny`, `Run script` | screenshot; wait |
| Credential-manager overlay (LastPass) | element label containing `LastPass`, or a popup window appearing | `escape` once, re-probe; if it persists, pause |
| Unknown app state | resolver bottoms out at PIXELS *and* the text changed between two polls | pause with both crops |
| Money / irreversible | approval class 3 in `TOOL_INTERFACE.md` §6 | refuse without a token |

**Where the human intervenes is their choice and should not be hard-coded.** If they are at the
machine, they take the mouse. If they are out, they open `vnc.html`. If the run is headless, the agent
posts a screenshot into the chat (Hermes delivers images) and waits for a reply. All three end the
same way: the agent re-probes the surface and continues from the step that paused.

## 4. So: VNC or CDP?

Both, for different jobs, and never VNC as the automation transport:

- **Automating the Linux box → SSH.** `ssh` + the app's own CLI, or `xdotool`/AT-SPI over the SSH
  session. Deterministic, no pixels, no latency.
- **Watching or rescuing the Linux box → noVNC.** Keep it. It is the only view you have when the
  desktop is headless, and it is exactly what you want when the *human* must click something.
- **Automating a browser you also want the human to see → CDP on a visible window.** That is model (b)
  above: the agent keeps the DOM (fast, reliable, typed), the human keeps the pixels (can interrupt).
- **Do not** drive a browser through VNC pixels when CDP is available: you lose selectors, text
  extraction and `finished responding` signals, and you gain OCR error (18.99 s per full frame,
  `2006-11-30` → `2886-11-38` on this machine).

Security: an unauthenticated noVNC endpoint is a remote-control hole. Confirm a VNC password or put it
behind an SSH tunnel (`ssh -L 6080:localhost:6080 user@192.168.2.52`), and treat `:3000` as unknown
until identified.
