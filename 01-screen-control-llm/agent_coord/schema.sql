-- agent_coord schema — cross-machine coordination for the IDE agent fleet.
--
-- WHY NOT SQLITE: SQLite's own documentation states that network filesystems "lie about locking
-- constantly and cannot be trusted", and WAL additionally requires a shared-memory -shm file that only
-- exists within one host. Measured on this fleet: 4 local writers without busy_timeout lost 400 of 1600
-- rows, and a tracked trial_ledger.db forked into three files with 2, 13 and 6 rows.
--
-- WHY MYSQL: it already exists, both hosts reach it, and InnoDB gives row-level locking plus MVCC, so the
-- two things a fleet actually needs are natively safe: many seats appending at once, and exactly one
-- winner when several seats claim the same task.
--
-- DESIGN RULE: every row records WHICH SEAT wrote it. A shared store is only better than forked files if
-- provenance survives, otherwise you get one authoritative number nobody can attribute.

CREATE TABLE IF NOT EXISTS agent_seat (
  seat           VARCHAR(64)  NOT NULL PRIMARY KEY,
  host           VARCHAR(64)  NOT NULL,
  worktree       VARCHAR(128) NULL,
  role           VARCHAR(64)  NULL,
  goal           TEXT         NULL,
  todo           TEXT         NULL,
  done           TEXT         NULL,
  registered_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_seen      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY k_seen (last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS agent_task (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  repo         VARCHAR(128) NOT NULL,
  slug         VARCHAR(160) NOT NULL,
  title        VARCHAR(255) NOT NULL,
  status       ENUM('open','claimed','blocked','done','abandoned') NOT NULL DEFAULT 'open',
  claimed_by   VARCHAR(64)  NULL,
  claimed_at   DATETIME     NULL,
  lease_until  DATETIME     NULL,
  priority     TINYINT      NOT NULL DEFAULT 3,
  artifact     VARCHAR(512) NULL,
  note         TEXT         NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_task (repo, slug),
  KEY k_status (status, priority),
  KEY k_lease (lease_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Append-only. The replacement for the forked trial_ledger.db files.
-- source_path keeps provenance for rows migrated out of those forks, so nothing is silently re-attributed.
CREATE TABLE IF NOT EXISTS agent_trial (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  run_id       VARCHAR(64)  NOT NULL,
  family       VARCHAR(96)  NOT NULL,
  variant      VARCHAR(96)  NOT NULL,
  sharpe_is    DECIMAL(12,6) NULL,
  sharpe_oos   DECIMAL(12,6) NULL,
  kept         TINYINT(1)   NOT NULL DEFAULT 0,
  cost_bps     DECIMAL(8,2) NULL,
  seat         VARCHAR(64)  NOT NULL,
  source_path  VARCHAR(255) NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_trial (run_id, family, variant, seat),
  KEY k_family (family),
  KEY k_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Every claim a seat makes, with the evidence pointer. This is the table that stops "trust me" findings.
CREATE TABLE IF NOT EXISTS agent_finding (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  task_id       BIGINT UNSIGNED NULL,
  seat          VARCHAR(64)  NOT NULL,
  repo          VARCHAR(128) NULL,
  kind          ENUM('measurement','defect','decision','blocker','correction','handoff') NOT NULL,
  claim_text    TEXT         NOT NULL,
  evidence_path VARCHAR(512) NULL,
  evidence_sha  VARCHAR(64)  NULL,
  value_num     DECIMAL(18,6) NULL,
  value_unit    VARCHAR(32)  NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY k_task (task_id),
  KEY k_seat (seat),
  KEY k_kind (kind, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS agent_artifact (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  seat       VARCHAR(64)  NOT NULL,
  task_id    BIGINT UNSIGNED NULL,
  repo       VARCHAR(128) NOT NULL,
  path       VARCHAR(512) NOT NULL,
  sha256     CHAR(64)     NULL,
  bytes      BIGINT       NULL,
  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_artifact (repo, path, sha256),
  KEY k_task (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS agent_heartbeat (
  seat     VARCHAR(64) NOT NULL PRIMARY KEY,
  host     VARCHAR(64) NOT NULL,
  worktree VARCHAR(128) NULL,
  beat_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  note     VARCHAR(255) NULL,
  KEY k_beat (beat_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- One row per seat, showing what it holds and whether it is alive. A claim held by a seat that has not
-- beaten in an hour is the signal that a task needs re-claiming rather than waiting forever.
CREATE OR REPLACE VIEW v_agent_board AS
SELECT t.id, t.repo, t.slug, t.status, t.claimed_by, t.lease_until,
       s.host AS seat_host, s.last_seen AS seat_last_seen,
       CASE
         WHEN t.status = 'open' THEN 'AVAILABLE'
         WHEN t.lease_until IS NOT NULL AND t.lease_until < NOW() THEN 'LEASE_EXPIRED'
         WHEN s.last_seen IS NULL THEN 'CLAIMANT_UNSEEN'
         WHEN s.last_seen < NOW() - INTERVAL 60 MINUTE THEN 'CLAIMANT_STALE'
         ELSE 'HELD'
       END AS board_state,
       t.updated_at
FROM agent_task t
LEFT JOIN agent_seat s ON s.seat = t.claimed_by;

-- Trial counts per family, the denominator multiple-testing corrections actually need.
CREATE OR REPLACE VIEW v_trial_census AS
SELECT family, COUNT(*) AS trials,
       SUM(kept = 1) AS kept,
       COUNT(DISTINCT seat) AS seats,
       MIN(created_at) AS first_trial,
       MAX(created_at) AS last_trial
FROM agent_trial
GROUP BY family;
