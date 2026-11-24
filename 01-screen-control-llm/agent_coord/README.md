# agent_coord — a coordination store the fleet can actually share

**Date:** 2026-11-24 · **Owner:** Hermes · **Status:** live and measured on this fleet's real topology

Four seats work this estate concurrently: Kilo and Copilot on the Windows box, Zoo on `eltonsGX10`, Hermes
on Windows. They could not see each other's state, and the attempts to share state through files kept
forking. This is the replacement, with the rejected options recorded so nobody re-litigates them.

---

## 1. Why the obvious approaches do not work

| Option | Verdict | Why |
|---|---|---|
| **SQLite on a shared/network path** | **Rejected** | SQLite's own docs: network filesystems "lie about locking constantly and cannot be trusted"; sharing a file across machines is explicitly unsupported and corrupts |
| **SQLite + WAL** | **Rejected** | WAL needs a `-shm` shared-memory file, which only exists inside one host. Measured here: 4 writers on ONE host without `busy_timeout` lost **400 of 1,600 rows**; with it, 2,400/2,400 |
| **SQLite committed to git** | **Rejected — already failed** | Append-only binary cannot be three-way merged. `trial_ledger.db` forked into three files with 2, 13 and 6 rows because the writer takes its path from `argv[1]` and `dsr.py` defaults to a bare relative name |
| **Turso / libSQL** | **Not chosen** | Their own SDK table says classic libSQL: concurrent writes **"Not supported"**. Turso Cloud's `BEGIN CONCURRENT` (MVCC, row-level) is a hosted/preview service — a new external dependency and vendor for state that must never leave these machines |
| **rqlite** | **Credible alternative, not chosen** | SQLite + Raft + HTTP API is genuinely multi-writer and Docker is active on `eltonsGX10`, so it would run. Rejected as *more* infrastructure than the job needs: a Raft quorum for four agents vs a database that is already reachable from both hosts |
| **Redis** | **Rejected** | The local bus is down (`127.0.0.1:6379` refused) and Redis is not durable for a ledger of record |
| **MQTT / COMS** | **Kept for messages, not records** | A retained topic holds only its LAST message — it is a bus, not a store. Correct for "hands up, I'm taking task X", wrong for "here is what X returned" |

## 2. What was chosen

**MySQL `ejaguiar1_stocks`** — already exists, already reachable from both machines (`mysql.50webs.com:3306`
confirmed from Windows; `pymysql` present on both), and InnoDB gives exactly the two guarantees the fleet
needs: row-level locking with MVCC for concurrent appends, and a single guarded `UPDATE` for task claims.

No new server, no new port, no vendored state.

## 3. Proof — measured, not asserted

| Test | Result |
|---|---|
| **4 writers across 2 machines**, 100 rows each, simultaneous | **400 of 400 rows, 0 errors**, 10.3 s |
| **20 threads racing one task**, one host | **exactly 1 winner** |
| **10 Windows + 10 Linux threads racing one task** | **exactly 1 winner** (Linux lost cleanly, 0) |
| Second seat claiming a held task via CLI | refused, **exit code 3**, prints holder and lease |
| Board view for a claim by an unregistered seat | flags **`CLAIMANT_UNSEEN`** |

Reproduce:

```bash
export COORD_PW=$(ssh eltonsGX10 'grep -E "^stocks[0-9]+$" ~/dbpasses.txt | head -1')
python run_test.py 100          # 4 writers, 2 per machine
python test_concurrency.py --claim-test --rows 20
```

## 4. The schema

| Table | Purpose |
|---|---|
| `agent_seat` | who is who: seat, host, worktree, goal, todo, last_seen |
| `agent_task` | the work board. `status`, `claimed_by`, 30-minute lease |
| `agent_trial` | **append-only**, replaces the forked trial ledgers. Keeps `source_path` provenance |
| `agent_finding` | every claim a seat makes, with `evidence_path` and an optional numeric value — this is what stops "trust me" findings |
| `agent_artifact` | path + sha256 + bytes per output, so an artifact can be verified not described |
| `agent_heartbeat` | liveness, separate from `agent_seat` so a stale goal does not read as a stale agent |
| `v_agent_board` | tasks with `HELD` / `AVAILABLE` / `LEASE_EXPIRED` / `CLAIMANT_STALE` / `CLAIMANT_UNSEEN` |
| `v_trial_census` | trials per family — the denominator multiple-testing corrections actually need |

Every row records the seat that wrote it. A shared store is only better than forked files if provenance
survives; otherwise you get one authoritative number nobody can attribute.

## 5. Using it

```bash
export COORD_PW=...                                   # per-invocation, never stored
python coord.py register --seat kilo-win --host DESKTOP --worktree antigravity --goal "..." --todo "..."
python coord.py claim    --repo PORTFOLIO --slug e9-coord-store --title "..."   # exit 0 = yours
python coord.py post     --repo PORTFOLIO --kind measurement \
        --claim "400/400 cross-machine writes" --evidence agent_coord/README.md --value 400 --unit rows
python coord.py board    --repo PORTFOLIO
python coord.py trials
python coord.py who
```

`claim` is a single guarded `UPDATE ... WHERE status='open' OR lease_until < NOW()`, so the database
decides the winner, not the agent. A claim whose lease expired, or whose seat has not beaten in an hour,
returns to the board as re-claimable instead of blocking the task forever — the failure mode that makes a
fleet look idle when it is actually wedged behind a dead claimant.

## 6. Migration of the forked ledgers

`migrate_trials.py` read all three forks and merged them into `agent_trial` with `source_path` provenance:
**23 rows** in, idempotent on re-run.

The census then exposed a worse problem than the fork — **the family names do not reconcile**:

| family | trials |
|---|---|
| `family_alpha` | 5 |
| `family_momentum` | 4 |
| `alpha` | 2 |
| `momentum` | 2 |
| `cron_dummy` / `dummy` | 2 / 2 |
| `famA`, `var_a`, `var_b`, `equity` | 1–2 each |

`alpha` and `family_alpha` are almost certainly the same lineage recorded under two names, as are
`momentum`/`family_momentum` and `cron_dummy`/`dummy`. **Splitting one family into two rows halves the
trial count and therefore understates the multiple-testing penalty** — which is the exact direction that
flatters a backtest. Until a canonical family name is agreed, `v_trial_census` is descriptive, not a valid
denominator. Pick one naming rule and record it in `agent_trial` going forward; do not rename history.

## 7. Size: what belongs in here and what does not

Measured 2026-11-24 on the live database.

**The coordination store is not a size risk.** Total `ejaguiar1_stocks` size is **57,890 MB**. My 400
concurrency-test rows occupied **128 KB** — about **320 bytes per row** including indexes. One million
findings would therefore be ≈ **305 MB**, or **0.5%** of what already exists. The whole `agent_*` set is
**368 KB**.

**Storing artifacts would be the mistake.** One 5 MB report per seat per day is 20 MB/day ≈ **7 GB/year**,
added to a database that is already large. A row here holds a path, a sha256 and an optional number — never
the report, the CSV or a database file.

**The database is already large, and that is the real finding.** Two tables are 97% of it:

| Table | Rows | Size |
|---|---|---|
| `bt_backtest_trades` | 27,212,129 | **31,486 MB** |
| `at_local_picks` | 76,180,125 | **24,854 MB** |
| `agent_*` (all coordination tables) | 427 | 0.37 MB |

Any table anyone adds is irrelevant next to those two. If quota becomes a problem, the conversation is
about `bt_backtest_trades` and `at_local_picks`, not about the coordination store.

**Path rule:** write repository-relative paths, never absolute local paths — a Windows path means nothing
to the Linux seat.

## 8. Limits, stated plainly

- **Single point of failure.** `mysql.50webs.com` is shared hosting. If it is down, the fleet cannot claim
  or post. It is still better than three forked files that are always readable and always disagreeing.
- **No offline mode.** A seat that loses the network cannot queue writes. rqlite or a local libSQL replica
  would add that, at the cost of running a quorum.
- **The password is per-invocation.** `COORD_PW` is read from `~/dbpasses.txt` at call time and never
  written to disk, a doc, or a commit.
- **Not a scheduler.** This records who took what and what it returned. It does not start or stop agents.
