"""Rebuild ChatPlayground's "paste all" output from an accessibility-tree capture.

Why this exists: the app's `Copy all answers` control is present **only while a response is
streaming** (measured 2026-11-22 — it is in the toolbar at x≈2319 during generation and gone once the
last panel finishes). A post-hoc sweep therefore has to reconstruct the same document from the tree,
which is the reliable rung anyway: the panels expose their answer text as `Text` nodes, in order, with
a stable per-panel `Assistant` marker and a metrics strip (`Time to first token`, `Credits used`).

Output matches the app byte-for-byte in shape: `# <prompt>`, then `## <model>` + body per panel.

Usage:
    python prototype/extract.py capture.json --prompt "Reply with exactly: PROTOTYPE OK"
    python prototype/extract.py capture.json --prompt-file prompt.txt --out answers.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

MODEL_HEADER = re.compile(r"^Model:\s*(?P<model>.+?)\.\s*Change model$")
METRICS = {"Time to first token", "Total time", "Tokens in and out", "Credits used"}
NOISE = {"Copy message", "Edit message", "Regenerate response", "Read aloud", "Maximize panel",
         "You"}
#: the metrics strip *values* sit one line above its labels, so they are matched by shape
METRIC_VALUE = re.compile(r"^(TTFT\s|[\d,.]+ ?(ms|s|m)$)|(tokens$)|(^\d+ credits?$)|(^—$)")
CHROME_TEXT = re.compile(
    r"^(Send to|only$|finished responding$)|panel options$|^Thought for \d|^Response stats$"
)


def load_elements(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    elements = data if isinstance(data, list) else data.get("elements", [])
    # bounds can be null for container stubs; drop those early
    return [e for e in elements if e.get("bounds")]


def panels(elements: Iterable[dict]) -> list[tuple[str, int, int]]:
    """(model, x_start, x_end) per panel, ordered left to right."""
    heads: list[tuple[str, int]] = []
    for e in elements:
        m = MODEL_HEADER.match((e.get("label") or "").strip())
        if m:
            heads.append((m.group("model"), e["bounds"][0]))
    heads.sort(key=lambda t: t[1])
    out = []
    for i, (model, x0) in enumerate(heads):
        x1 = heads[i + 1][1] if i + 1 < len(heads) else 10 ** 9
        out.append((model, x0, x1))
    return out


def _in_panel(bounds: list[int], x0: int, x1: int) -> bool:
    # panels sit side by side; the header x is the left edge, allow a small left tolerance
    return x0 - 30 <= bounds[0] < x1 - 30


def extract(elements: list[dict]) -> dict[str, list[str]]:
    """Model -> answer lines, in reading order.

    The window is bounded by the user's message row (the prompt, echoed above the answer) and the
    per-panel metrics strip, whose labels sit one line BELOW their values — so the strip is detected
    by shape (`TTFT 634 ms`, `14 -> 8 tokens`, `1 credit`), not only by label.
    """
    result: dict[str, list[str]] = {}
    model_names = {m for m, _, _ in panels(elements)}
    for model, x0, x1 in panels(elements):
        nodes = []
        for e in elements:
            b = e["bounds"]
            if not _in_panel(b, x0, x1):
                continue
            label = (e.get("label") or "").strip()
            if not label or label in NOISE or label in METRICS:
                continue
            if CHROME_TEXT.search(label):
                continue
            nodes.append((b[1], label))
        nodes.sort()

        assistant_y = next((y for y, lab in nodes if lab == "Assistant"), None)
        if assistant_y is None:
            result[model] = []
            continue

        lines: list[str] = []
        for y, lab in nodes:
            if y <= assistant_y:
                continue
            if METRIC_VALUE.match(lab):      # strip begins here; everything after is telemetry
                break
            if lab in model_names or lab == "Assistant":
                continue
            if not lines or lines[-1] != lab:
                lines.append(lab)
        result[model] = lines
    return result


def render(prompt: str, answers: dict[str, list[str]]) -> str:
    parts = [f"# {prompt}".rstrip(), ""]
    for model, lines in answers.items():
        parts.append(f"## {model}")
        parts.append("")
        parts.extend(lines if lines else ["(no answer captured)"])
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Rebuild ChatPlayground 'paste all' from an AX capture.")
    ap.add_argument("capture", help="elements JSON written by computer_use capture")
    ap.add_argument("--prompt", default="", help="the prompt text, used as the document title")
    ap.add_argument("--prompt-file", help="read the prompt from a file instead")
    ap.add_argument("--out", help="write the markdown here instead of stdout")
    args = ap.parse_args(argv)

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()

    answers = extract(load_elements(Path(args.capture)))
    doc = render(prompt, answers)
    if args.out:
        Path(args.out).write_text(doc, encoding="utf-8")
        print(f"wrote {args.out} ({len(doc)} chars, {len(answers)} panels)")
    else:
        print(doc)
    missing = [m for m, lines in answers.items() if not lines]
    if missing:
        print(f"WARNING: no answer text captured for {missing}", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
