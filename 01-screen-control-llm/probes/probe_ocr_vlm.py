"""Probe: how well can we perceive a Copilot Chat panel without accessibility APIs?
1) RapidOCR over the full screenshot (text + boxes)
2) Local VLM (ollama qwen3-vl:*) grounding: "where is the send button" + "what did the agent say last"
"""
import base64, io, json, sys, time, urllib.request
from pathlib import Path

IMG = Path(sys.argv[1] if len(sys.argv) > 1 else "vscode.png")
raw = IMG.read_bytes()
b64 = base64.b64encode(raw).decode()

# ---------- 1. OCR ----------
t0 = time.time()
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
res, _ = ocr(str(IMG))
dt = time.time() - t0
lines = [(r[1], [int(v) for v in r[0][0]]) for r in (res or [])]
print(f"[OCR] rapidocr: {dt:.2f}s  boxes={len(lines)}  img={IMG.name}")
# right-hand chat column only (x > 1000 of 1456 wide)
chat = [t for t, xy in lines if xy[0] > 1000]
print(f"[OCR] chat-column lines ({len(chat)}):")
for t in chat[:40]:
    print("   ", t)

# ---------- 2. VLM grounding ----------
OLLAMA = "http://127.0.0.1:11434/api/generate"

def ask(model, prompt, img_b64, timeout=600):
    body = json.dumps({
        "model": model, "prompt": prompt, "images": [img_b64],
        "stream": False, "options": {"temperature": 0, "num_predict": 220},
    }).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.loads(r.read())
    el = time.time() - t
    ev = j.get("eval_count") or 0
    return j.get("response", "").strip(), el, ev, (ev / el if el else 0)

Q_GROUND = ("This is a VS Code screenshot, 1456x818. In the right-hand Chat panel there is a chat "
            "input box at the bottom with a submit arrow button on its right edge. Reply with JSON only: "
            '{"x": <pixel x>, "y": <pixel y>, "confidence": <0-1>}')
Q_READ = ("Look at the right-hand Chat panel. Transcribe, verbatim, the last assistant message text and "
          "any button labels visible in the top-right of that panel. Text only, no commentary.")

for model in ("qwen3-vl:2b", "qwen3-vl:4b"):
    for name, q in (("ground", Q_GROUND), ("read", Q_READ)):
        try:
            out, el, ev, tps = ask(model, q, b64)
            print(f"\n[{model} :: {name}] {el:.1f}s  {ev} tok  {tps:.1f} tok/s\n{out[:700]}")
        except Exception as e:
            print(f"\n[{model} :: {name}] FAILED {type(e).__name__}: {e}")
