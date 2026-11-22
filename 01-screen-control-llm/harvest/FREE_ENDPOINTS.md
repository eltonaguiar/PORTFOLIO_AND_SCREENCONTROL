# Passwordless AI endpoints — what still answers, measured 2026-11-22

Goal: a quick second opinion without an account, an API key, or a paid plan. Everything below was
called for real from this machine; the numbers are from those calls, not from documentation.

## Scoreboard

| Endpoint | Auth | Result | Detail |
|---|---|---|---|
| **duck.ai** (browser) | **none** | **WORKS** | model `GPT-6 Luna`, Fast mode. Answered a 676-char methodology prompt; 92-line answer harvested (10.4 KB). No account, no captcha in a real browser. |
| `text.pollinations.ai/<prompt>?model=openai` (GET) | none | **partial** | short prompts return 200 (`"OK"` in 0.15–0.22 s, `openai-fast` answered a 100-char question in 4.2 s); a 140-char question returned **402 Payment Required** |
| `text.pollinations.ai/openai` (POST) | none | **partial** | 402 without a `Referer` header; with `Referer` + a short prompt → 200 and an OpenAI-shaped body (`id: pllns_…`, `choices[0].message.content`, plus a `reasoning` field). Any longer prompt → 402 |
| `text.pollinations.ai/models` | none | works | anonymous tier advertises exactly **one** model: `openai-fast` |
| DuckDuckGo `/duckchat/v1/status` | none | **closed** | 200 but returns only `x-vqd-hash-1` (JS proof-of-work). The old `x-vqd-4` token flow is gone, so the API is not usable headlessly |
| `ai.hackclub.com/chat/completions` | none | **gone** | 404 |
| **Local Ollama** | none | **WORKS** | 8 local models: `qwen3-vl:2b/4b/8b`, `llama3.1:8b`, `devstral:24b`, `starcoder2:15b`, `llama3.2-vision:11b`, `hermes-desktop` |

## What the 402s actually mean

Pollinations is not gated by an API key — it is gated by **credits per request**. The same endpoint
returned 200 for `Reply with exactly: OK` and 402 for a 140-character question seconds later, and a POST
that failed without a referrer succeeded with one for a short prompt. So:

- treat `text.pollinations.ai` as a **tiny-prompt** channel (health checks, one-liners, label reads);
- do not build a research loop on it;
- a `Referer` header is worth sending on POST.

## Recommendation

1. **duck.ai in a real browser** for a genuine second opinion — it is the only no-account surface that
   answered a full methodology prompt, and it is harvestable with the standard
   gutter-click → `Ctrl+A` → `Ctrl+C` path (see `CAPTURE_CONTRACT.md`).
2. **Local Ollama** when the question is private, long, or repeated — no rate limit at all.
3. **Pollinations** only for one-line probes.

## Reproduce

```bash
# tiny prompt, no auth
curl -s "https://text.pollinations.ai/Reply%20with%20exactly%3A%20OK?model=openai"

# POST needs a referrer
curl -s https://text.pollinations.ai/openai \
  -H 'Content-Type: application/json' -H 'Referer: https://example.local/' \
  -d '{"model":"openai","messages":[{"role":"user","content":"Reply with exactly: OK"}]}'

# local, unlimited
curl -s http://127.0.0.1:11434/api/tags | head -c 300
```

## Caveat on the browser path

Driving a browser for this only works while the window's origin is tracked correctly. On 2026-11-22 a
window was moved to `(0,0)` and the driver kept offsetting coordinate clicks by the previous origin
`(1912,50)`, so every pixel click landed ~1912 px off — outside the window. **Element handles are immune
to this; coordinates are not.** Prefer `set_value` + element clicks, and re-capture immediately before
acting so the snapshot binding stays valid (a capture of a different mode in between invalidates indices
with `snapshot_id_required`).
