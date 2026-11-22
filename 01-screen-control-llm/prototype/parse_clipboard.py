"""Turn a 'select-all + copy' dump of a multi-model page into a per-model markdown file.

Why this path: on ChatPlayground the accessibility tree only exposes the rendered (virtualised)
part of a long answer, so tree scraping gives a partial body. The page's own text is complete,
and `Ctrl+A` / `Ctrl+C` in the browser copies it — 36,628 chars for a 3-panel answer set versus
2,243 chars from the tree. This script splits that dump on the `Assistant` marker and the
`TTFT` telemetry line, then assigns panels left-to-right.

Usage:
    python prototype/parse_clipboard.py RAW.txt --models "ChatGPT-6 Luna" "Claude (Latest Model)" "GLM 5.3 Flash" --out out.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

NOISE = re.compile(r"^(Close|Minimise|Restore|Chrome|Chrome Remote Desktop|Prompts|Send|Stop|"
                   r"Copy message|Read aloud|Regenerate response|Edit message|x|\?K)$")


def sections(lines: list[str]) -> list[list[str]]:
    """Split on the `Assistant` … `TTFT` window; that pair marks one model's answer."""
    out, cur, in_answer = [], [], False
    for line in lines:
        s = line.strip()
        if s == "Assistant":
            in_answer, cur = True, []
            continue
        if in_answer and s.startswith("TTFT"):
            out.append(cur)
            in_answer = False
            continue
        if in_answer:
            if s and not NOISE.match(s):
                cur.append(s)
    if cur:
        out.append(cur)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--prompt", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    lines = Path(args.raw).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    secs = sections(lines)
    print(f"sections found: {len(secs)} for {len(args.models)} models")

    parts = []
    if args.prompt:
        parts += [f"# {args.prompt}", ""]
    for i, model in enumerate(args.models):
        body = secs[i] if i < len(secs) else ["(not captured)"]
        parts += [f"## {model}", ""]
        parts += body
        parts += [""]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
