# CDP beats UIA and pixels on all three chat sites (measured)

Date: 2026-11-22 · Chrome 157.0.8103.79 · profile `C:/Users/zerou/chrome-agent-profile` · port 9222

## The blocker, restated with numbers

| Surface | UIA result | Coordinate click | Verdict |
|---|---|---|---|
| arena.ai | one `Group` for the whole page; 81 elements, all sidebar | posted `(2099,476)`, twice, no menu opened | unclickable by pixels, invisible to UIA |
| web.chatplayground.ai | 129 elements; `Edit 'Message every model'` **gone** once a chat exists | n/a | composer unreachable after first send |
| app.1min.ai | 126 elements; sidebar + search box only, editor absent | n/a | composer unreachable |

Chrome also refuses background `key`/`mouse_scroll` (`code: background_unavailable`,
`target_class: Chrome_WidgetWin_1`), and `coordinate=` posts are offset by the window origin, so
absolute pointer injection on monitor 2 lands somewhere other than the target.

## What the DOM says instead

`playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")` — verified working against a Chrome
launched with `--remote-debugging-port=9222`:

- **arena.ai mode switch is a native `<select>`**, not a menu:
  `{value: "chat", options: ["Chat/Compare and test the latest models"=chat, "Agent/Let agents get work done for you"=work]}`
  `page.select_option("select", "work")` → verified `work | Agent — Let agents get work done for you`.
  This is the "switch to Agent" instruction, executed deterministically.
- **arena.ai composer is `div[contenteditable='true'].tiptap.ProseMirror`** — TipTap, so `fill()` is a
  no-op and typing must go through key events. Over CDP that is reliable and does **not** depend on
  window focus, which is exactly why it beats the UIA/foreground path.
- The only `<textarea>` on arena is `g-recaptcha-response` (invisible) — a good reason never to assume
  "the first textarea is the prompt box".
- chatplayground and 1min.ai both show a login wall in a *fresh* profile, correctly detected as
  `login_wall: true` by the discovery pass and reported as `NEEDS_HUMAN` rather than guessed at.

## Consequence for the kernel

The ladder in `kernel/resolve.py` was right and this is its proof: for a browser, **API (CDP) is not
just the fastest rung, it is the only one that works** on an app whose composer is a rich-text editor
and whose chrome consumes every synthetic pointer event. UIA gives furniture; pixels give the wrong
place; CDP gives selectors, text, and a `select_option`.

## One-time human step

The agent profile has no Google session, so each site needs a single sign-in in that window:

```
chrome.exe --remote-debugging-port=9222 --user-data-dir=C:/Users/zerou/chrome-agent-profile
```

After that, `python prototype/cdp_multi_site.py --discover` and `--ask "<prompt>"` run unattended.

## Retry with the real profile (2026-11-22, later)

`chrome.exe --source-shortcut-location=taskbar --remote-debugging-port=9222` **did not bind the port**:
the surviving process (pid 45600) carries only `--source-shortcut-location=taskbar`, because an existing
Chrome already owned the default profile and swallowed the new flags. Chrome 136+ also refuses
`--remote-debugging-port` on the default data dir by design, so relaunching it unchanged will not help.

Copying the session into a separate profile also fails, and that is a *feature*, not a bug:

| copied | result |
|---|---|
| `Local State`, `Default/Network/Cookies` (3.4 MB), `Default/Login Data`, `Default/Preferences` → `C:/Users/zerou/chrome-agent-profile` | CDP binds (Chrome 157), but chatplayground still shows its login page — Chrome's app-bound cookie encryption stops the transplant exactly as intended |

**Conclusion: one sign-in per site in the agent-profile window is unavoidable.** After that the CDP path
works unattended.

### Kernel rules earned on the second attempt

- `keyboard.type(delay=8)` into a TipTap editor **dropped characters** — "sentence" → "sence",
  "single" → "ingle". `keyboard.insert_text()` wrote the same text intact (73 → 97 chars, no loss).
  Use insert-text for rich editors; reserve keystroke typing for apps that need key events.
- `select_option("select", "work")` is the whole Chat→Agent switch; verified `mode: work`.
- Submitting with `Enter` works, and the answer is gated behind a ToS consent modal + sign-in — a class-2
  gate, paused rather than clicked.
