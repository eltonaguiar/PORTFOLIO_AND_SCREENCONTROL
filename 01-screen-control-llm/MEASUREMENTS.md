# Measurements — screen perception on a real Windows workstation

All numbers below were produced on this machine, not quoted from a vendor. Date: **2026-11-22** (local,
UTC−05:00). Reproduce with the commands shown; the probe script is
[`probes/probe_ocr_vlm.py`](probes/probe_ocr_vlm.py).

## Environment

| Item | Value | How it was read |
|---|---|---|
| GPU | NVIDIA GeForce RTX 5070, 12227 MiB, driver 617.42 | `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv` |
| OS | Windows 11 (10.0.26300.9974) x86_64 | `cua-driver doctor` |
| Python | 3.14.2 | `python --version` |
| Local VLM runtime | Ollama with `qwen3-vl:2b`, `qwen3-vl:4b`, `qwen3-vl:8b`, `llama3.2-vision:11b`, `devstral:24b` | `ollama list` |
| OCR | `rapidocr_onnxruntime` (CPU/ONNX) installed in the system Python | `python -c "import rapidocr_onnxruntime"` |
| Desktop driver | `cua-driver 0.21.0` — UIAutomation reachable ✅, Windows Graphics Capture (D3D11) ✅, MCP session active ✅ | `hermes computer-use doctor` |
| Agent CLIs | GitHub Copilot CLI 1.0.49; Claude Code extension 2.1.33x; Kilo Code; Kimi Code | `copilot --version`, `~/.vscode/extensions` |

Test frame: a 1456×818 capture of a VS Code window running a Remote-SSH session, with a Copilot-style agent
chat panel open on the right (visible transcript, code block, diff summary with `Keep` / `Undo`, input box).

---

## 1. Windows UI Automation on an Electron app

```
computer_use(action="capture", app="Code.exe", mode="ax")
```

Result: **3 elements total** — `Button 'Minimize'`, `Button 'Maximize'`, `Button 'Close'` — all with
`bounds: null`. No editor, no terminal, no chat transcript.

Interpretation: Chromium/Electron only builds its accessibility tree when a client asks for it. VS Code
does so when a screen reader is detected, or when `"editor.accessibilitySupport": "on"` /
`--force-renderer-accessibility` is set. **As configured, the entire app was a bitmap to UIA.**

Consequence for the design: for Electron apps the first move is a *config switch*, not an OCR pipeline.

## 2. RapidOCR over the full frame

```
python probes/probe_ocr_vlm.py vscode.png
```

| Metric | Value |
|---|---|
| Wall clock, full frame | **18.99 s** |
| Text boxes returned | **106** |
| Chat column lines (x > 1000) | 42 |

Quality, verbatim examples from the output:

- Correct: `Keep`, `Undo`, `Describe what to build`, `Agent`, `Allow all`,
  `DeepSeek V4.1 Flash / High - Max 1M`, `proceed on next steps!`, `Finished thinking after 1s`.
- Wrong, in the code block: `2886-11-38` for `2006-11-30`, `AOA` for `A/B`, `n-(n)d` for a format string,
  `/tmp/ p6/data/VWELX.csv` (line break injected), `1ocal` for `local`, `AAAAAAAAAAA` for a traceback caret run.

Interpretation: OCR is a good *state* channel (is there a Stop button? which action is offered? what did the
agent say in prose?) and a bad *evidence* channel (numbers, paths, code, stack traces). At 19 s/frame it is
also too slow for a control loop at full-frame resolution — crop the panel (~400×800) instead.

## 3. Local VLM reading one UI label

Prompt: *"In the right-hand Chat panel, what is the exact label of the green/blue action button shown under
the diff summary (two files changed)? Answer with the single word only."*
Image tokens: 1241. `temperature: 0`, `num_predict: 160`, `think: false`.

| Model | Latency | Answer |
|---|---|---|
| `qwen3-vl:2b` | 0.6 s | **(empty)** — thinking trace only |
| `qwen3-vl:4b` | 1.0 s | `Keep` ✅ |
| `qwen3-vl:8b` | 1.0 s | `Keep` ✅ |

## 4. Local VLM returning a click coordinate (grounding)

Prompt: *"Bottom right of the Chat panel there is a chat input box; at its right edge there is a small round
button with an up arrow. Reply with ONLY two integers, the pixel x and y of that button."*
Image tokens: 1259–1277.

| Model | `num_predict=60` | `num_predict=600` |
|---|---|---|
| `qwen3-vl:2b` | 3.7 s — **empty** | — |
| `qwen3-vl:4b` | 9.3 s — **empty** | 7.8 s, 600 tokens, **empty** (still narrating `<think>`) |
| `qwen3-vl:8b` | 10.2 s — **empty** | — |

Interpretation: in this Ollama build, `think: false` does **not** suppress Qwen3's thinking trace, so the
whole output budget is spent inside `<think>` and the answer never arrives. A chat VLM is not a grounder.
Use a dedicated grounding model (ShowUI-2B, UI-TARS, UGround, OmniParser) or a non-thinking VLM.

Throughput reference for the same 4B model on real work: 1259-token image prompt, 600 generated tokens in
**7.8 s ≈ 77 tok/s**, 100 % GPU.

## 5. GitHub Copilot CLI autopilot — live smoke test

```
copilot -p "Create hello.txt containing exactly: hello from autopilot. Then verify its contents and stop." \
  --autopilot --yolo --no-ask-user --max-autopilot-continues 4 --output-format text
```

Result: `402 {"error":{"message":"You have exceeded your monthly quota","code":"quota_exceeded"}}`,
`Changes +0 -0`, `AI Units 0 (3s)`. **No file written.**

Two lessons, both feeding the supervisor design:

1. The flag surface exists and is accepted by 1.0.49 (`copilot --help` lists `--autopilot`,
   `--max-autopilot-continues`, `--allow-all`/`--yolo`, `--resume`, `--output-format`).
2. A quota wall is indistinguishable from "the agent stopped" if you only look at the transcript — and no
   amount of `continue` fixes it. The supervisor must classify the stop reason before acting.

---

## Reproduction notes

- Screenshots used for these probes are **not committed** (they show a private trading repository). Re-run
  the probes against any window: `cua-driver` capture → `probe_ocr_vlm.py <png>`.
- Ollama calls use `http://127.0.0.1:11434/api/generate` with `images: [base64]`; `num_ctx` defaults were
  left untouched. First call after a model load includes load time; the numbers above were steady-state.
- RapidOCR ran on CPU. A GPU/ONNX-runtime build would cut the 19 s substantially; the quality caveats
  (numbers, code) would not change.
