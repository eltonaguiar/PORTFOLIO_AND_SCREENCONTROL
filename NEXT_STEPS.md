# NEXT_STEPS — the machine-readable backlog

**How this file is used.** A scheduled agent (Hermes cron `pasc-progress`, every 3 hours) reads this file, picks
the **first unchecked item whose prerequisites are met**, does it, verifies it, commits, ticks the box, and
appends one line to [`PROGRESS_LOG.md`](PROGRESS_LOG.md). A human can do the same by hand. Never tick a box
without verification; never delete an item — cancel it with a reason instead.

Item format: `- [ ] **A1 — title** · size · definition of done`. Sizes: S < 1 h, M ≈ half a day, L ≈ a day+.

*Renumbered 2026-11-22 from the flat 1–12 list, because 12 items was not the whole backlog. Old → new:
1→done, 2→done, 3→A1, 4→A2, 5→A4, 6→A6, 7→A10, 8→B1, 9→B2, 10→B3, 11→C4, 12→C1.*

---

## Already done — kept for context, the scheduler skips this section

- [x] **D1** Repo created, README reframed as multi-AI research, folder split `01 / 02 / 03 / REVIEWS`
- [x] **D2** 13 model documents audited claim-by-claim; inputs preserved under `REVIEWS/inputs/`
- [x] **D3** `TOOL_INTERFACE.md` — 14 tools, effect envelope, approval classes 0–3, task-ledger schema
- [x] **D4** `STRATEGY_SPEC.md` — declaration, gates G1–G8, run manifest, trial accounting, JSON-authoring rule
- [x] **D5** `FABRICATION_CHECKLIST.md` (10 checks) and static gates **S1–S6**
- [x] **D6** S1–S6 **applied to our own harness** — all six PASS (`03-*/STATIC_GATE_AUDIT.md`)
- [x] **D7** `CAPITAL_ALLOCATION.md` from the **live** audit3 ledger (0/67 proven, selection alpha negative in every class, 0/9 pods funded)
- [x] **D8** `TRACKING.md` + `scripts/update_index.py` + cron `pasc-index-sync` (every 3 h, idempotent, `--check`)
- [x] **D9** COMS seat `hermes-deepseek-flash-psc`; broadcasts on allocation, gates, and the blocked upstream fix
- [x] **D10** `kernel/capture.py` + 8 passing tests (real window-scoped grab, crop, 1.5× DPI mapping)

---

## Track A — screen control (`01-screen-control-llm/`)

- [ ] **A1 — `kernel/resolve.py`** · M · the five-rung ladder (§4.6: native → a11y selector → text/OCR → marks →
      pixels) with per-window-class caching and re-probe on resize. **DoD:** prints the rung chosen for VS Code,
      Windows Terminal, Explorer and Chrome on this machine, plus the evidence it used (node counts / text lines). · blocked: no interactive desktop in this unattended cron; DoD needs live windows on VS Code, Terminal, Explorer and Chrome with real node counts / text lines — never faked
- [ ] **A2 — `kernel/act.py`** · M · the twelve verbs, each returning `{ok, effect, verified, evidence}`, with
      approval classes 0–3 enforced in code. **DoD:** click/type/set_value on three surfaces with read-back
      verification; a class-3 verb raises without an approval token; **`coordinate=` is refused when an element
      handle exists for the target** (proven necessary 2026-11-22: a coordinate click was rescaled by the driver
      from `(3108,739)` to `(5029,798)` and missed, while the element click landed). · blocked: act.py is unwritten and its DoD needs read-back verification on three live surfaces — no desktop session in this cron — not faked
- [x] **A3 — kernel unit tests beyond capture** · S · resolve and act covered by tests that do not need a GUI (mock
      the transport). **DoD:** `pytest 01-screen-control-llm/tests -q` covers all three modules; no test requires an
      open window.
- [ ] **A4 — four-surface acceptance test** · S · blocked: no desktop session in this unattended cron; the four-surface script needs live VS Code, Terminal, Explorer and Chrome windows with read-back verification — never faked · one script drives VS Code (type), Windows Terminal (run), Explorer
      (rename), Chrome (open) — each verified, no per-app code. **DoD:** exits 0 from a clean shell; transcript
      committed under `01-screen-control-llm/transcripts/`. **Needs the desktop:** if unattended desktop use is not
      wanted, mark blocked and run manually.
- [ ] **A5 — CI enforcement of approval classes** · S · blocked: prerequisite `kernel/act.py` with per-verb approval classes 0–3 does not exist (A2, blocked); nothing to gate-enforce yet · a test that fails if any verb marked class 2/3 can execute
      without a gate; wired into `.github/workflows/screen-control-tests.yml`. **DoD:** the test fails when the gate
      is deliberately removed.
- [x] **A6 — `overseer.py`** · L · stop classifier + signature hashing + brief injection + budgets + `STOP` file (§5).
      **DoD:** passes a simulated session (stop → continue → loop → steer with a new fact → done) without
      touching a real vendor agent; test committed.
- [x] **A7 — reconcile with the peer's `screen_control/`** · M · two drivers now exist under `01-`: the peer's
      guarded loop and this kernel. Decide the merge — kernel as perception/actuation layer, or adopt the peer's
      policy module wholesale. **DoD:** one documented owner per concern in `01-*/README.md`; no duplicated capture
      or click path.
- [x] **A8 — measure the crop-vs-full-frame claim** · S · capture.py's docstring asserts a panel crop beats the
      measured 18.99 s full-frame OCR. Measure a 400×800 crop with RapidOCR. **DoD:** `01-*/MEASUREMENTS.md` gains a
      row with real elapsed time.
- [x] **A9 — Linux/RustDesk path** · M · verify SSH + AT-SPI from this host to the Linux box, or document exactly
      which step blocks it. **DoD:** one scripted read of a remote window's tree, or a written blocker.
- [x] **A10 — wire approval classes into the docs** · S · link `TOOL_INTERFACE.md` §6 from `02-*`'s evidence rules
      and from `act.py`; add the class table to `01-*/README.md`. **DoD:** no broken links; index regenerated.

## Track B — trading (`03-trading-strategies/`)

- [x] **B1 — score auto-expired rows as their own class** · M · local spec delivered in
      [`03-trading-strategies/EXPIRY_SCORING_SPEC.md`](03-trading-strategies/EXPIRY_SCORING_SPEC.md) — `resolution_class`
      enum `{OPEN,TP_HIT,SL_HIT,TIME_EXPIRED,VOID}`, expiry mark in `realized_bp` (no default `0`), class-average
      semantics, local mapping + verification gates. **Upstream code fix remains blocked** — lives in
      `findtorontoevents.ca`, fleet-owned (asked on COMS); B1's DoD was the local spec, which now exists.
- [x] **B2 — forward-gate dashboard** · S · read the audit3 ledger JSON; print pods by status, rows per pod, and the
      binding gate clause per pod. **DoD:** runs against the live URL; output committed as
      `03-*/results/forward_gate_<UTC>.json`.
- [x] **B3 — cost-basis versioning** · S · capture `payload.slippage_validation` per class into a committed file with
      a hash, so any verdict can be recomputed against the costs it used. **DoD:** file committed;
      `CAPITAL_ALLOCATION.md` cites it instead of quoting numbers from memory.
- [x] **B4 — re-run harness certification after any harness change** · S · `python -m
      realtime_challenge.proof.test_harness` from `03-*/`. **DoD:** 5/5 pass; result appended to `PROGRESS.md`.
      Mandatory whenever a run touches `realtime_challenge/`.

## Track C — repo, fleet, and process

- [x] **C1 — one claim-by-claim audit per new model answer** · S · recurring: review it, preserve the input under
     `REVIEWS/inputs/`, add a row to `REVIEWS/README.md`, cite a verifiable artefact per claim. **DoD:** review
     merged; index regenerated.
- [ ] **C2 — refresh `FACTCHECK.md` when a new tool claim appears** · S · recurring: any newly named MCP server,
      driver or model gets repo-existence + licence + last-push checks. **DoD:** table row added with ✅/🟡/❌. · blocked: no new tool claim (MCP server, driver or model) has appeared since the last FACTCHECK.md update, so there is no row to add — not faked
- [ ] **C3 — weekly COMS reconcile** · S · weekly: read `roster` + `check`, answer asks, re-register the seat with an
      updated `done`, flag any seat duplicating this repo's work. **DoD:** one broadcast per week; seat row current. · blocked: coms.ps1 / COMS MQTT access (broker plus seat registration) is not present on this machine, so the roster cannot be read, asks answered, or a seat broadcast sent — not faked
- [x] **C4 — keep `TRACKING.md` current** · S · automated (`pasc-index-sync`, every 3 h). **DoD:** `python
      scripts/update_index.py --check` exits 0 on `main`.
- [x] **C5 — prune the backlog honestly** · S · monthly: cancel items that no longer matter, with a reason,
     instead of letting the list grow. **DoD:** item count stable or lower; every cancellation has a reason.

---

## Rules for the scheduled agent

1. `git pull --rebase` first; the sibling agent commits to `main` frequently. On conflict, take the newer artifact
   and reconcile — never force-push, never delete a peer's file.
2. Do **one** substantive item per run. Small, verified, committed beats broad and unverified.
3. Run the DoD for real. If it cannot run here (another repo, a GUI, credentials), mark the item blocked with one
   sentence and move to the next unchecked item — never implement a fake to tick a box.
4. Append exactly one line to `PROGRESS_LOG.md`: `YYYY-MM-DDTHH:MMZ | item | verdict | evidence`.
5. Touching `03-trading-strategies/realtime_challenge/` requires `test_harness` to pass afterwards (B4).
6. Three consecutive blocked runs → stop changing code and post the blocker to COMS instead.


---

## Queue additions — 2026-11-22 17:05 EST (Session B was reporting an empty queue)

The hourly Session-B loop declared "queue complete, nothing left to advance" at 16:14. It was not out of
work, it was out of *queued* work. Three items below are pre-registered and take priority in this order.

### Q1 — Book-level trend overlay counter-test (from Mercury3, `notes/reply-mercury3-to-pasc-combining-conditional-2026-11-22`)
Apply a book-level overlay to the same 6 pre-registered hypotheses x 7 crypto majors, 1d bars, 3.3y,
26 bp round turn, daily mark-to-market with a flat day = 0.0%.
- 10-month SMA and 20/200 Donchian on the **book** equity curve; to cash when off; 26 bp on each
  portfolio flip (not per leg).
- **Kill rule (pre-registered):** the overlay book's Sharpe must exceed the best single component
  (0.243) by more than the 95% cluster-bootstrap lower bound of the difference. If it does not,
  Mercury3's condition (ii) — "overlay must sit at book level" — is falsified for this book.
- Report overlay turnover cost too: at 26 bp a monthly book flip can consume the entire improvement.
- **Blocked (this run):** the overlay backtest plus 95% cluster-bootstrap is not implemented; building it is a multi-cell job too large for one unattended cron run, and its output would land in the sibling-owned `03-trading-strategies/results/`.

### Q2 — Mutual-fund NAV staleness (data availability first)
NAV is struck once daily, so the price is mechanically stale. Test whether close vs next-day NAV diverges
> 2% and survives the Questrade $9.95 + load. **Kill:** T+1 gap minus fees <= 0 bp across >= 30 fund-days.
Check data availability before any build; if NAV history is not free and point-in-time, stop and record it.

### Q3 — Interval-fund tender timing (liquidity edge, not a price edge)
Submit redemption at quarter-end; measure acceptance rate and queue length.
**Kill:** acceptance < 50% or queue > 4 quarters. This is the one candidate idea that is not
dead-on-arrival against the cost wall, because it competes on liquidity rather than on spread.
· blocked: submitting a quarter-end redemption and measuring acceptance and queue length needs live market and broker access; live trading and credentials are off-limits in this repo — not faked

### Standing rule for this loop
Before reporting "queue complete", check this file and `03-trading-strategies/ASSET_CLASS_IDEA_HARVEST.md`
for unstarted items. "Nothing to do" is only true when both are exhausted.

### Q4 — Cost-model validation gates (from the CRYPTO/BOND/ETF harvest, kept only after removing an echo)

The usable half of that answer proposed **measurement** tests rather than new alpha, which is the right
instinct for a programme whose binding constraint is cost honesty. Pre-registered thresholds, to be
applied to our own measured series before any new strategy work:
· blocked: these are Session B verdict documents; their artifacts would commit into sibling-owned `03-trading-strategies/` results/ledger, which this session must not touch — not faked

| Gate | Test | Kill |
|---|---|---|
| G-COST-1 | median realised fill cost over >= 30 live fills, 15m horizon | kill the cost assumption if median >= 8.0 bp |
| G-COST-2 | slippage distribution on liquid pairs at 15m | kill if P50 > 8 bp or P90 > 20 bp |
| G-COST-3 | is the 1D cost premium real? recompute on one instrument | kill the +24.21 bp figure if 1D cost > 24.21 bp or < 19 bp (no edge survives the spread) |
| G-COST-4 | vol-target gap decomposition (2.3 vs 10.7 bp/day) on one instrument | kill the vol-target overlay if the gap persists > 5 bp/day after 20 sessions |

Note on provenance: the *other* answer to the same question was an **echo** from the local 8B — it reused
prompt numbers as thresholds and inverted the logic ("kill if next-open gross > +12.43 bp"). Rejected.
A model that cannot produce a number independent of the prompt has not measured anything.
