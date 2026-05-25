import sqlite3
import os
import json
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "memory_data", "audit.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id TEXT,
                verdict TEXT,
                confidence_score INTEGER,
                confidence_label TEXT,
                timestamp TEXT,
                mode TEXT DEFAULT 'orchestrate',
                source_file TEXT,
                pipeline_steps TEXT
            );

            CREATE TABLE IF NOT EXISTS check_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verification_id INTEGER REFERENCES verifications(id),
                check_name TEXT,
                result TEXT,
                input_a TEXT,
                input_b TEXT,
                reason TEXT,
                fuzzy_score INTEGER,
                is_custom INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS pattern_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verification_id INTEGER REFERENCES verifications(id),
                pattern_type TEXT,
                pattern_value TEXT,
                count INTEGER,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                proposal_type TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT,
                evidence TEXT,
                generated_code TEXT
            );

            CREATE TABLE IF NOT EXISTS healing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_name TEXT,
                error_type TEXT,
                error_message TEXT,
                root_cause TEXT,
                proposed_fix TEXT,
                auto_fixable INTEGER DEFAULT 0,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS test_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                test_case_name TEXT,
                test_category TEXT,
                verdict TEXT,
                confidence_score INTEGER,
                pass_threshold INTEGER,
                soft_threshold INTEGER,
                initial_leniency INTEGER,
                checks_json TEXT,
                timestamp TEXT
            );
        """)


def save_verification(applicant_id: str, verdict: str, confidence: dict,
                      checks: list, mode: str = "orchestrate",
                      source_file: str = None, pipeline_steps: list = None) -> int:
    init_db()
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with _conn() as conn:
        cur = conn.execute(
            """INSERT INTO verifications
               (applicant_id, verdict, confidence_score, confidence_label,
                timestamp, mode, source_file, pipeline_steps)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                applicant_id, verdict,
                confidence.get("score", 0), confidence.get("label", ""),
                ts, mode, source_file,
                json.dumps(pipeline_steps or []),
            ),
        )
        vid = cur.lastrowid
        for c in checks:
            conn.execute(
                """INSERT INTO check_results
                   (verification_id, check_name, result, input_a, input_b,
                    reason, fuzzy_score, is_custom)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    vid,
                    c.get("check", ""),
                    c.get("result", ""),
                    c.get("input_a", ""),
                    c.get("input_b", ""),
                    c.get("reason", ""),
                    c.get("fuzzy_score"),
                    1 if c.get("is_custom") else 0,
                ),
            )
        return vid


def save_test_session(session_id: str, test_case_name: str, test_category: str,
                      verdict: str, confidence: dict, checks: list,
                      pass_threshold: int, soft_threshold: int, initial_leniency: bool):
    init_db()
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with _conn() as conn:
        conn.execute(
            """INSERT INTO test_sessions
               (session_id, test_case_name, test_category, verdict, confidence_score,
                pass_threshold, soft_threshold, initial_leniency, checks_json, timestamp)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                session_id, test_case_name, test_category,
                verdict, confidence.get("score", 0),
                pass_threshold, soft_threshold,
                1 if initial_leniency else 0,
                json.dumps(checks), ts,
            ),
        )


def save_healing_event(check_name: str, error_type: str, error_message: str,
                       root_cause: str, proposed_fix: str, auto_fixable: bool):
    init_db()
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with _conn() as conn:
        conn.execute(
            """INSERT INTO healing_events
               (check_name, error_type, error_message, root_cause,
                proposed_fix, auto_fixable, timestamp)
               VALUES (?,?,?,?,?,?,?)""",
            (check_name, error_type, error_message, root_cause,
             proposed_fix, 1 if auto_fixable else 0, ts),
        )


def save_proposal(proposal: dict):
    init_db()
    with _conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO proposals
               (id, title, description, proposal_type, status,
                created_at, updated_at, evidence, generated_code)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                proposal.get("id"),
                proposal.get("title", ""),
                proposal.get("description", ""),
                proposal.get("proposal_type", ""),
                proposal.get("status", "pending"),
                proposal.get("created_at", ""),
                proposal.get("updated_at", ""),
                json.dumps(proposal.get("evidence", [])),
                proposal.get("generated_code", ""),
            ),
        )


def get_verifications(limit: int = 50) -> list:
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM verifications ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_verification_checks(verification_id: int) -> list:
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM check_results WHERE verification_id = ?",
            (verification_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_test_sessions(limit: int = 100) -> list:
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM test_sessions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["checks"] = json.loads(d.pop("checks_json", "[]"))
            except Exception:
                d["checks"] = []
            result.append(d)
        return result


def get_healing_events(limit: int = 100) -> list:
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM healing_events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_db_stats() -> dict:
    init_db()
    with _conn() as conn:
        tables = ["verifications", "check_results", "pattern_observations",
                  "proposals", "healing_events", "test_sessions"]
        counts = {}
        for t in tables:
            row = conn.execute(f"SELECT COUNT(*) as n FROM {t}").fetchone()
            counts[t] = row["n"]
        size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        return {"table_counts": counts, "db_size_bytes": size}
