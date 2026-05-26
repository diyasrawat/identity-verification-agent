# Persistence Layer Flow

## Overview

VerifyIQ uses two persistence mechanisms that work together:
1. **JSON files** — for agent state that needs to be read frequently (pattern memory, proposals, healing log, custom rules)
2. **SQLite database** — for queryable audit history (verifications, checks, test sessions, events)

---

## Persistence Architecture

```
backend/memory_data/                    (created automatically)
├── pattern_memory.json                 ← ObservationAgent reads/writes
├── proposals.json                      ← RuleProposerAgent reads/writes
├── healing_log.json                    ← SelfHealingAgent reads/writes
├── custom_rules.json                   ← main.py reads on every request
└── audit.db                            ← SQLite: all durable history
```

---

## JSON Persistence Flow (memory_store.py)

### How `save()` Works (Atomic Write)

```python
def save(key: str, data) -> None:
    p = _path(key)          # → memory_data/{key}.json
    tmp = p + ".tmp"         # → memory_data/{key}.json.tmp

    # Step 1: Write to temp file
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Step 2: Atomic rename
    os.replace(tmp, p)
    # os.replace is atomic on POSIX + Windows (same drive)
    # If server crashes between steps: .tmp exists but .json is intact
    # If server crashes after step 2: .json is the new complete file
```

Why atomic? If you wrote directly to the .json file and the server crashed mid-write, the file would be corrupted (partial JSON). The .tmp trick ensures you either have the old complete file or the new complete file — never a partial.

### How `load()` Works

```python
def load(key: str) -> dict | list:
    p = _path(key)
    if not os.path.exists(p):
        return DEFAULTS.get(key, {})    # Return default if file missing
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULTS.get(key, {})    # Return default if corrupted
```

Defaults for each key:
```python
DEFAULTS = {
    "pattern_memory": {"date_formats": {}, "name_patterns": {}, ...},
    "proposals": {"pending": [], "approved": [], "rejected": []},
    "healing_log": {"events": [], "known_errors": {}},
    "custom_rules": [],
}
```

---

## SQLite Schema (audit_db.py)

### Tables

```sql
CREATE TABLE verifications (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    applicant_id     TEXT,
    verdict          TEXT,        -- "CLEAN" / "SOFT ISSUES..." / "HARD BLOCK"
    confidence_score INTEGER,     -- 0-100
    confidence_label TEXT,        -- "HIGH CONFIDENCE" etc.
    timestamp        TEXT,        -- ISO 8601
    mode             TEXT,        -- "orchestrate" or "live_test"
    source_file      TEXT,        -- applicant_id used as source identifier
    pipeline_steps   TEXT         -- JSON array of step objects
);

CREATE TABLE check_results (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    verification_id  INTEGER REFERENCES verifications(id),
    check_name       TEXT,
    result           TEXT,        -- "pass" / "soft_fail" / "hard_fail"
    input_a          TEXT,
    input_b          TEXT,
    reason           TEXT,
    fuzzy_score      INTEGER,     -- NULL for non-fuzzy checks
    is_custom        INTEGER      -- 0 or 1 (boolean)
);

CREATE TABLE pattern_observations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    verification_id  INTEGER REFERENCES verifications(id),
    pattern_type     TEXT,
    pattern_value    TEXT,
    count            INTEGER,
    timestamp        TEXT
    -- Currently unused; reserved for future pattern-level SQL queries
);

CREATE TABLE proposals (
    id               TEXT PRIMARY KEY,    -- "PROP-0001"
    title            TEXT,
    description      TEXT,
    proposal_type    TEXT,
    status           TEXT DEFAULT 'pending',
    created_at       TEXT,
    updated_at       TEXT,
    evidence         TEXT,                -- JSON array
    generated_code   TEXT
);

CREATE TABLE healing_events (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    check_name       TEXT,
    error_type       TEXT,
    error_message    TEXT,
    root_cause       TEXT,
    proposed_fix     TEXT,
    auto_fixable     INTEGER DEFAULT 0,
    timestamp        TEXT
);

CREATE TABLE test_sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       TEXT,           -- groups sessions from same run
    test_case_name   TEXT,
    test_category    TEXT,           -- "judge_demo", "manual", etc.
    verdict          TEXT,
    confidence_score INTEGER,
    pass_threshold   INTEGER,
    soft_threshold   INTEGER,
    initial_leniency INTEGER,        -- 0 or 1 (boolean)
    checks_json      TEXT,           -- JSON array of check results
    timestamp        TEXT
);
```

---

## When Each Table Gets Written To

```
POST /orchestrate:
  verifications  ← save_verification() in main.py (after pipeline)
  check_results  ← same call, saves each check as a row

POST /verify-live (if test_case_name or session_id provided):
  test_sessions  ← save_test_session()

POST /test/run-all-judge-cases:
  test_sessions  ← save_test_session() for each of 10 cases

When self_healing_agent.heal_check() catches exception:
  healing_events ← save_healing_event()

When rule_proposer_agent.add_proposal() creates proposal:
  proposals      ← save_proposal()

When rule_proposer_agent.approve_proposal() approves:
  proposals      ← save_proposal() (INSERT OR REPLACE, updates status)
```

---

## Full Write Flow: A Verification Run

```
User clicks FL-001
  │
  ▼
POST /orchestrate → run_orchestrator() runs 7 agents
  │
  ▼
During pipeline:
  SelfHealingAgent (if exception) → healing_log.json + SQLite healing_events
  │
  ▼
After pipeline returns:
  observe_verification()
    → Read pattern_memory.json
    → Update counters
    → Write pattern_memory.json (atomic)
  │
  analyze_and_propose()
    → Read proposals.json
    → Check thresholds
    → If new proposals: write proposals.json + SQLite proposals
  │
  save_verification()
    → INSERT INTO verifications
    → INSERT INTO check_results (one row per check)
  │
  Return response to frontend
```

---

## Memory Dashboard: Querying the Persistence Layer

```
MemoryDashboard.jsx mounts, fires 4 parallel fetches:

GET /memory/stats
  → memory_store.get_stats()
    For each of 4 JSON keys: check file exists, get size + mtime
  → get_db_stats()
    For each of 6 SQLite tables: SELECT COUNT(*) FROM {table}
    Get db file size
  Response: sizes, last modified, row counts

GET /history/verifications?limit=20
  → get_verifications(20)
    SELECT * FROM verifications ORDER BY id DESC LIMIT 20
  Response: last 20 verifications (id, applicant_id, verdict, confidence, timestamp)

GET /history/test-sessions?limit=50
  → get_test_sessions(50)
    SELECT * FROM test_sessions ORDER BY id DESC LIMIT 50
    Also parses checks_json → checks array
  Response: last 50 test sessions

GET /history/patterns
  → get_pattern_memory()
  Response: same as /self-improve/memory
```

---

## Reset Flow

```
User clicks "Reset" button next to pattern_memory.json in MemoryDashboard

POST /memory/reset
  Body: { "key": "pattern_memory" }
  │
  ▼
main.py: reset_memory(data)
  Valid keys: "pattern_memory", "proposals", "healing_log", "custom_rules"
  │
  ▼
memory_store.reset("pattern_memory")
  → os.remove(memory_data/pattern_memory.json)
  │
  ▼
Next time ObservationAgent runs:
  load("pattern_memory") → file not found → returns DEFAULTS["pattern_memory"]
  → all counters start from 0 again

Note: Reset only affects the JSON file.
SQLite verifications/test_sessions are NOT affected by reset.
```

---

## Why Two Persistence Systems?

| Concern | JSON Files | SQLite |
|---|---|---|
| **Read speed** | Very fast (single file read) | Needs query execution |
| **Write pattern** | Entire document rewritten each time | Row-level inserts |
| **Agent access pattern** | Read on every request by agents | Read only in history APIs |
| **Query capability** | Limited (load full dict) | Full SQL: ORDER BY, COUNT, LIMIT |
| **Data type** | Cumulative aggregates (counters, lists) | Individual events per run |
| **Reset** | Delete file | Would need DELETE queries |

JSON is used for **agent working memory** — data agents read and update on every run.  
SQLite is used for **audit history** — data you query afterward, never modified by agents.
