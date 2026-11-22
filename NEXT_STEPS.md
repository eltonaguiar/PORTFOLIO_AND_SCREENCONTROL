# NEXT_STEPS — the machine-readable backlog

**How this file is used.** A scheduled agent (Hermes cron `pasc-progress`, every 3 hours) reads this file, picks
the **first unchecked item whose prerequisites are met**, does it, verifies it, commits, ticks the box, and
appends one line to [`PROGRESS_LOG.md`](PROGRESS_LOG.md). A human can do the same by hand. Never tick a box
without verification; never delete an item — cancel it with a reason instead.

Item format: `- [ ] **N — title** · size · definition of done`.

---

## Track A — screen control (folder `01-screen-control-llm/`)

- [x] **1 — Static gates S1–S6 on our own harness** · S · done 2026-11-22, see [`STATIC_GATE_AUDIT.md`](STATIC_GATE_AUDIT.md)
- [ ] **2 — `kernel/capture.py`** · M · window-scoped capture (Windows Graphics Capture / D3D11), per-monitor-v2 DPI
      math, crop helper, screen↔window↔client transforms. **DoD:** unit test asserts the same element box maps to
      the same screen point at 100% and 150% scaling; no full-screen grabs in the code path.
- [ ] **3 — `kernel/resolve.py`** · M · the five-rung ladder from `PC_AGENT_CONTROL_RESEARCH.md` §4.6
      (native → a11y selector → text/OCR → marks → pixels) with per-window-class caching. **DoD:** prints the rung
      it chose for VS Code, Windows Terminal, Explorer and Chrome on this machine, and re-probes after a resize.
- [ ] **4 — `kernel/act.py`** · M · the twelve verbs, each returning the `{ok, effect, verified, evidence}` envelope
      from `TOOL_INTERFACE.md`, with the approval classes 0–3 enforced in code. **DoD:** click/type/set_value on
      three surfaces with a read-back verification, and a class-3 action refused without an approval token.
- [ ] **5 — kernel acceptance test** · S · one script drives VS Code (type in editor), Windows Terminal (run a
      command), Explorer (rename a file), Chrome (open a page) — each verified, no per-app code. **DoD:** exits 0
      from a clean shell; transcript committed under `01-screen-control-llm/transcripts/`.
- [ ] **6 — `overseer.py`** · L · stop classifier + signature hashing + brief injection + budgets + `STOP` file,
      per `PC_AGENT_CONTROL_RESEARCH.md` §5. **DoD:** passes a simulated session (stop → continue → loop detected →
      steer with a new fact → done) without touching a real vendor agent; test committed.
- [ ] **7 — wire approval classes into the docs** · S · link `TOOL_INTERFACE.md` §6 from `02-`'s evidence rules and
      from `act.py`; add the class table to `01-*/README.md`. **DoD:** no broken links; index regenerated.

## Track B — trading (folder `03-trading-strategies/`)

- [ ] **8 — score auto-expired rows as their own class** · M · **blocked: lives in `findtorontoevents.ca`, owned by
      the fleet** (asked on COMS). Locally: document the required schema change and the failure mode it fixes
      (wide-TP strategies escaping judgement forever). **DoD:** a written spec in `03-*/` even if the upstream fix
      is done elsewhere.
- [ ] **9 — forward-gate dashboard** · S · one script that reads the audit3 ledger JSON and prints: pods by status,
      rows per pod, and which gate clause is the binding one for each. **DoD:** runs against the live URL, output
      committed as `03-trading-strategies/results/forward_gate_<UTC>.json`.
- [ ] **10 — cost-basis versioning** · S · capture `payload.slippage_validation` per class into a committed file,
      with a hash, so a verdict can always be recomputed against the costs it used. **DoD:** file committed; the
      audit doc references it instead of quoting numbers from memory.

## Track C — repo hygiene (continuous)

- [ ] **11 — keep `TRACKING.md` current** · S · automated (cron `pasc-index-sync`, every 3 h). **DoD:** `python
      scripts/update_index.py --check` exits 0 on `main`.
- [ ] **12 — one audit per new model answer** · S · whenever a new `REALTIMECHALLENGE_*.md` or playbook arrives:
      review it, preserve the input under `REVIEWS/inputs/`, add the row to `REVIEWS/README.md`. **DoD:** the review
      cites at least one verifiable artefact (price, repo, line number) per claim.

---

## Rules for the scheduled agent

1. `git pull --rebase` first; the sibling agent commits to `main` frequently. On conflict, take the newer artifact
   and reconcile — never force-push, never delete a peer's file.
2. Do **one** item per run. Small, verified, committed beats broad and unverified.
3. Run the verification in the DoD. If it cannot be run here (needs the other repo, needs a GUI), say so, mark the
   item blocked with the reason, and move to the next.
4. Append exactly one line to `PROGRESS_LOG.md`: `YYYY-MM-DDTHH:MMZ | item N | verdict | commit`.
5. If three consecutive runs are blocked, stop changing code and post the blocker to COMS instead.
