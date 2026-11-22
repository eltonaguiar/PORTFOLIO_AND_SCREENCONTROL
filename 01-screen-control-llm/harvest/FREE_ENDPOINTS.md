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

## Local gateways — full measured matrix (2026-11-22, this host)

Every row below is a real call, not documentation.

**Router on `:4000`** — exists on *both* machines (`127.0.0.1` and `192.168.2.52`). All aliases answered;
`back=` is the actual upstream the alias resolved to:

| Alias | Latency | Upstream it resolved to | Verdict |
|---|---:|---|---|
| `ULTRA_FREE_CLOUD_LARGE` | 10.8 s | — | **full 905-char answer to a real question; best free route** |
| `ULTRA_FREE_CLOUD_FAST` | 13.9 s | `meituan/longcat-2.5:free` | works |
| `ULTRA_FREE_CLOUD_TOOLS` | 7.0 s | `gpt-4o-mini-2024-07-18` | works, tool-capable |
| `ULTRA_FREE_KILO` | 2.0 s | `ULTRA_FREE_KILO` | works |
| `ULTRA_FREE_OPENROUTER` | 1.6 s | `ULTRA_FREE_OPENROUTER` | works |
| `ULTRA_FREE_NVIDIA` | 3.8 s | `ULTRA_FREE_NVIDIA` | works |

**vLLM `:8000`** — `Qwen3.6-35B-A3B-NVFP4`, 12.0 s, `finish_reason=length`, **`content` = 0 chars,
`reasoning` = 3,643 chars even at `max_tokens=900`.** A reasoning model spends the whole budget thinking:
budget `max_tokens` at 2–3 k (or strip the reasoning channel), never report `content: null` as an empty
answer.

**Ollama cloud tags** — the Windows box still lists them but they are **dead upstream**:

| Tag | Result |
|---|---|
| `glm-4.6:cloud` | **410 Gone** |
| `kimi-k2.5:cloud` | **410 Gone** |
| `gpt-oss:120b-cloud` | 200 with an **empty** body in 0.3 s |
| `deepseek-v3.1:671b-cloud` | **410 Gone** (earlier probe) |

A tag appearing in `/api/tags` does not mean it is served. Prefer the router aliases for cloud models.

**Kilo `192.168.2.32:53401`** — 15 imported GGUFs, all `Not loaded` until first use, **one model at a
time**; `/v1/models` itself times out while a load is in flight (busy, not down). First call can return
`''` after ~27 s with the model still loading.

## The Linux pool cannot serve a large model right now (measured)

`192.168.2.52` answers `/api/tags` with 26 models and `/api/ps` shows **0 loaded** — yet every real load
fails in ~2 seconds:

| Model | Result |
|---|---|
| `gemma3:12b` | HTTP 500 — `llama-server startup failed … CUDA error: out of memory` in **2.17 s** |
| `qwen3.5:35b-a3b` | same 500, **2.25 s** |

So it is **not** an ollama queue problem: the card is either occupied by something outside ollama or not
usable by it. Consequences:

1. **The Linux pool is not a valid second opinion host today.** Rotation must fall back to the Windows
   router (`ULTRA_FREE_*`) rather than to `.52`.
2. Diagnosing it needs `nvidia-smi` on that host — and **SSH from this Windows box is refused**
   (`eaguiar2015@192.168.2.52: Permission denied (publickey,password)`), so the Linux seat has to report it.
3. A 2-second 500 with `CUDA out of memory` is a *routing* fact. Do not retry smaller-and-smaller models
   hoping one fits; find out what holds VRAM first.

## Vision models are a trap as a default

The script's first version defaulted to the first model in `/api/tags`, which was `qwen3-vl:2b` — a vision
model. It answered a text prompt with **0 characters after 179.7 s**. Defaults now skip `-vl`, `vision`,
`embed`, `bge`, `nomic`, `sqlcoder` and `starcoder`, and prefer a known text model (`qwen3:8b`,
`llama3.1:8b`, …).
