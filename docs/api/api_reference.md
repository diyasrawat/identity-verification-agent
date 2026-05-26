# API Reference — VerifyIQ Backend

Base URL: `http://localhost:8000`  
All endpoints return JSON. CORS is open (`allow_origins=["*"]`).  
API documentation (Swagger UI): `http://localhost:8000/docs`

---

## Verification Endpoints

### POST /verify
Simple verification without the full orchestrator pipeline. Runs 7 checks and LLM reasoning, no address/fraud/verdict agents.

**Request body:**
```json
{
  "applicant_id": "FL-001",
  "pan": {
    "number": "ABCPK1234D",
    "name": "Prashant Kumar",
    "dob": "1990-04-12",
    "gender": "M",
    "father_name": "Ramesh Kumar"
  },
  "aadhaar": {
    "last4": "1234",
    "name": "Prashant Kumar",
    "dob": "1990-04-12",
    "gender": "M",
    "father_name": "Ramesh Kumar"
  },
  "bureau": {
    "name": "Prashant Kumar",
    "dob": "1990-04-12",
    "pan_linked": "ABCPK1234D",
    "aadhaar_last4": "1234"
  }
}
```

**Response:**
```json
{
  "applicant_id": "FL-001",
  "checks": [/* array of check result objects */],
  "verdict": "CLEAN",
  "confidence_score": {"score": 100, "label": "HIGH CONFIDENCE", "color": "green"},
  "agent_note": "All checks passed...",
  "confidence": "HIGH",
  "recommendation": "PROCEED",
  "reasoning": "All deterministic checks passed with no mismatches."
}
```

---

### POST /orchestrate
Full 7-agent pipeline. The primary endpoint used by the frontend.

**Request body:** Same as /verify plus optional `addresses` and `doc_dates`.

```json
{
  "applicant_id": "FL-001",
  "pan": { ... },
  "aadhaar": { ... },
  "bureau": { ... },
  "addresses": {
    "aadhaar": "12, MG Road, Pune 411001",
    "pan": "12 MG Road, Pune",
    "bank_statement": "12, Mahatma Gandhi Road, Pune 411001"
  },
  "doc_dates": {
    "aadhaar": 2024,
    "pan": 2019,
    "bank_statement": 2026
  }
}
```

**Response:** Full result with all agent outputs.
```json
{
  "applicant_id": "FL-001",
  "pipeline_steps": [
    {"step": 1, "name": "Data Extraction & Normalization", "status": "complete", "summary": "3 fields normalized"},
    {"step": 2, "name": "Identity Cross-Check", "status": "complete", "summary": "Verdict: CLEAN | 0 hard, 0 soft fails"},
    {"step": 3, "name": "Address Verification", "status": "complete", "summary": "Verdict: CONSISTENT | 0 hard conflicts"},
    {"step": 4, "name": "LLM Reasoning Pass", "status": "complete", "summary": "Recommendation: PROCEED"},
    {"step": 5, "name": "Fraud Signal Analysis", "status": "complete", "summary": "Fraud Score: 0/100 (LOW RISK)"},
    {"step": 6, "name": "Underwriter Verdict", "status": "complete", "summary": "Final Decision: PROCEED"},
    {"step": 7, "name": "Audit Logging", "status": "complete", "summary": "Audit ID: AUD-0001"}
  ],
  "checks": [/* 7 check objects */],
  "identity_verdict": "CLEAN",
  "confidence_score": {"score": 100, "label": "HIGH CONFIDENCE", "color": "green"},
  "reasoning_result": {
    "agent_note": "All checks passed...",
    "confidence": "HIGH",
    "recommendation": "PROCEED",
    "reasoning": "..."
  },
  "address_result": {
    "verdict": "CONSISTENT",
    "canonical_address": "12, MG Road, Shivaji Nagar, Pune 411001",
    "canonical_source": "aadhaar",
    "conflicts": [],
    "trust_scores": {"aadhaar": 90, "pan": 34},
    "graph_lookups": {...},
    "agent_analysis": "..."
  },
  "fraud_result": {
    "fraud_score": 0,
    "risk_level": "LOW",
    "fraud_signals": [],
    "fraud_narrative": "No significant fraud signals detected."
  },
  "final_verdict": {
    "final_verdict": "PROCEED",
    "verdict_color": "green",
    "underwriter_notes": "SUMMARY: ...\nKEY FINDINGS: ...\nRECOMMENDED ACTION: ..."
  },
  "audit_entry": {"audit_id": "AUD-0001", ...},
  "observation": {...},
  "new_proposals_generated": 0,
  "rules_applied": 0
}
```

---

### POST /verify-live
Live testing endpoint with configurable thresholds. Used by the LiveTestPanel component.

**Request body:**
```json
{
  "pan": { "number": "...", "name": "...", "dob": "...", "gender": "...", "father_name": "..." },
  "aadhaar": { "last4": "...", "name": "...", "dob": "...", "gender": "...", "father_name": "..." },
  "bureau": { "name": "...", "dob": "...", "pan_linked": "...", "aadhaar_last4": "..." },
  "pass_threshold": 85,
  "soft_threshold": 55,
  "initial_leniency": true,
  "test_case_name": "My Test Case",
  "test_category": "manual",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "checks": [/* check results */],
  "verdict": "CLEAN",
  "confidence_score": {"score": 100, "label": "HIGH CONFIDENCE", "color": "green"},
  "mode": "live_test",
  "thresholds_used": {"pass_threshold": 85, "soft_threshold": 55, "initial_leniency": true}
}
```

Notes:
- If `test_case_name` or `session_id` is provided, the run is saved to SQLite `test_sessions` table.
- Thresholds default to 85/55/true if not provided.
- `test_category` should be one of: `name_test`, `dob_test`, `gender_test`, `pan_test`, `judge_demo`, `manual`

---

### POST /explain
Get AI explanation for a specific failed check. Used by the AskAI drawer.

**Request body:**
```json
{
  "check": {
    "check": "Name Match (PAN vs Aadhaar)",
    "input_a": "PAN: P. Kumar",
    "input_b": "Aadhaar: Prashant Kumar",
    "result": "soft_fail",
    "reason": "..."
  },
  "full_profile": { /* full profile dict */ }
}
```

**Response:**
```json
{
  "explanation": "The name 'P. Kumar' on PAN appears to be an abbreviation of 'Prashant Kumar' on Aadhaar..."
}
```

---

## Check Result Object Shape

Every check function returns this structure:
```json
{
  "check": "Name Match (PAN vs Aadhaar)",
  "input_a": "PAN: Prashant Kumar",
  "input_b": "Aadhaar: Prashant Kumar",
  "result": "pass",
  "reason": "Names match (95% similarity).",
  "fuzzy_score": 95,
  "raw_score": 95,
  "transliteration_applied": false,
  "initial_match_detected": false,
  "thresholds_used": {"pass": 85, "soft": 55},
  "is_custom": false
}
```

Result values: `"pass"` | `"soft_fail"` | `"hard_fail"`

---

## Rule Engine Endpoints

### POST /rules/create
Generate Python rule code from plain English description.

**Request:**
```json
{ "rule_description": "Gender on PAN and Aadhaar must match exactly" }
```

**Response:**
```json
{
  "rule_description": "Gender on PAN and Aadhaar must match exactly",
  "func_name": "custom_check_gender_exact_match",
  "generated_code": "def custom_check_gender_exact_match(profile):\n    ...",
  "status": "generated"
}
```

---

### POST /rules/save
Persist a generated rule to `custom_rules.json`. After saving, the rule runs on every verification.

**Request:** Same object returned by `/rules/create`.

**Response:**
```json
{ "status": "saved", "total_rules": 3 }
```

---

### GET /rules/list
List all active custom rules.

**Response:**
```json
{
  "rules": [
    {"func_name": "custom_check_gender_exact_match", "rule_description": "Gender on PAN and Aadhaar must match exactly"}
  ]
}
```

---

### DELETE /rules/{func_name}
Remove a custom rule by its function name.

**Response:**
```json
{ "status": "deleted", "total_rules": 2 }
```

---

## Self-Improving Agent Endpoints

### GET /self-improve/memory
Returns the full pattern memory object.

**Response:**
```json
{
  "total_runs": 15,
  "date_formats": {"YYYY-MM-DD": 20, "DD/MM/YYYY": 3},
  "name_patterns": {"FULL_NAME": 12, "INITIAL_FIRST_NAME": 3},
  "soft_fail_patterns": {"INITIAL_FIRST_NAME": 3},
  "hard_fail_patterns": {},
  "recent_observations": [/* last 10 observation objects */],
  "typo_frequency": {}
}
```

---

### GET /self-improve/stats
Summary statistics for the header badge.

**Response:**
```json
{
  "total_runs": 15,
  "patterns_discovered": 5,
  "pending_proposals": 2,
  "approved_proposals": 1,
  "top_date_formats": [["YYYY-MM-DD", 20], ["DD/MM/YYYY", 3]],
  "top_name_patterns": [["FULL_NAME", 12]],
  "typos_caught": 0
}
```

---

### GET /self-improve/proposals
All proposals across all statuses.

**Response:**
```json
{
  "pending": [
    {
      "id": "PROP-0001",
      "type": "DATE_FORMAT_HANDLER",
      "trigger_pattern": "DD/MM/YYYY",
      "observation": "Date format 'DD/MM/YYYY' seen 3 times across 15 runs",
      "proposed_action": "Add explicit handler for DD/MM/YYYY format in normalize_date()",
      "priority": "MEDIUM",
      "auto_generate": true,
      "status": "pending",
      "created_at": "2026-05-26T10:00:00"
    }
  ],
  "approved": [],
  "rejected": [],
  "total_pending": 1,
  "total_approved": 0
}
```

---

### POST /self-improve/proposals/{proposal_id}/approve
Approve a proposal. If `auto_generate=true`, triggers LLM code generation.

**Response:** Updated proposal object with `status: "approved"` and optionally `generated_code`.

---

### POST /self-improve/proposals/{proposal_id}/reject
Reject a proposal.

**Response:** Updated proposal object with `status: "rejected"`.

---

## Self-Healing Endpoint

### GET /healing/log
Returns all healing events and known error patterns.

**Response:**
```json
{
  "total_healed": 2,
  "unique_error_patterns": 1,
  "healing_log": [
    {
      "timestamp": "2026-05-26T10:00:00",
      "error_signature": "a1b2c3d4",
      "check_name": "Date of Birth (PAN vs Aadhaar)",
      "error_type": "TypeError",
      "error_message": "'NoneType' object has no attribute...",
      "analysis": {
        "root_cause": "Null DOB value passed to normalize_date",
        "error_category": "NULL_VALUE",
        "proposed_fix": "Add null check before calling normalize_date",
        "severity": "MEDIUM",
        "auto_fixable": true
      },
      "healed": true
    }
  ],
  "known_errors": [
    {
      "signature": "a1b2c3d4",
      "check_name": "Date of Birth",
      "count": 2,
      "root_cause": "Null DOB value",
      "proposed_fix": "Add null check",
      "auto_fixable": true,
      "severity": "MEDIUM"
    }
  ]
}
```

---

## Audit & Metrics Endpoints

### GET /audit
In-memory audit log for the current server session.

**Response:**
```json
{
  "entries": [
    {
      "audit_id": "AUD-0001",
      "timestamp": "2026-05-26T10:00:00",
      "applicant_id": "FL-001",
      "agents_run": ["extraction", "identity", "address", "reasoning", "fraud", "verdict"],
      "final_verdict": "PROCEED",
      "fraud_score": 0,
      "confidence_score": 100,
      "identity_verdict": "CLEAN",
      "address_verdict": "CONSISTENT",
      "checks_run": 7,
      "hard_fails": 0,
      "soft_fails": 0,
      "rules_applied": 0
    }
  ]
}
```

---

### GET /evaluation/metrics
Runs all 3 mock files through the orchestrator and computes precision/recall against hardcoded ground truth.

**Response:**
```json
{
  "precision": 100.0,
  "recall": 100.0,
  "f1_score": 100.0,
  "accuracy": 100.0,
  "true_positives": 4,
  "false_positives": 0,
  "false_negatives": 0,
  "true_negatives": 17,
  "per_file": {
    "FL-001": {"verdict_correct": true, "check_accuracy": [...]},
    "FL-002": {"verdict_correct": true, "check_accuracy": [...]},
    "FL-003": {"verdict_correct": true, "check_accuracy": [...]}
  },
  "interpretation": {
    "precision": "100.0% of flagged issues were real issues",
    "recall": "100.0% of actual issues were caught",
    "f1": "Overall F1 score: 100.0%"
  }
}
```

---

## Memory & History Endpoints

### GET /memory/stats
File system + SQLite statistics.

**Response:**
```json
{
  "json_files": {
    "pattern_memory": {"exists": true, "size_bytes": 512, "last_modified": "2026-05-26 10:00:00"},
    "proposals": {"exists": false, "size_bytes": 0, "last_modified": null},
    "healing_log": {"exists": false, "size_bytes": 0, "last_modified": null},
    "custom_rules": {"exists": true, "size_bytes": 1024, "last_modified": "2026-05-26 09:00:00"}
  },
  "sqlite": {
    "table_counts": {
      "verifications": 15, "check_results": 105, "pattern_observations": 0,
      "proposals": 0, "healing_events": 0, "test_sessions": 10
    },
    "db_size_bytes": 32768
  },
  "summary": {
    "total_verifications": 15,
    "total_test_sessions": 10,
    "total_healing_events": 0,
    "total_proposals": 0
  }
}
```

---

### POST /memory/reset
Reset a JSON memory file (deletes it, defaults used on next access).

**Request:**
```json
{ "key": "pattern_memory" }
```

Valid keys: `"pattern_memory"`, `"proposals"`, `"healing_log"`, `"custom_rules"`

**Response:**
```json
{ "status": "reset", "key": "pattern_memory" }
```

---

### GET /history/verifications?limit=50
Last N verifications from SQLite.

**Response:**
```json
{
  "verifications": [
    {
      "id": 15, "applicant_id": "FL-001", "verdict": "CLEAN",
      "confidence_score": 100, "confidence_label": "HIGH CONFIDENCE",
      "timestamp": "2026-05-26T10:00:00", "mode": "orchestrate"
    }
  ],
  "count": 15
}
```

---

### GET /history/verifications/{id}/checks
All check results for a specific verification.

**Response:**
```json
{
  "verification_id": 15,
  "checks": [
    {
      "id": 105, "verification_id": 15,
      "check_name": "PAN Format Validity", "result": "pass",
      "input_a": "ABCPK1234D", "input_b": "Normalized: ABCPK1234D",
      "reason": "PAN 'ABCPK1234D' is valid format.",
      "fuzzy_score": null, "is_custom": 0
    }
  ]
}
```

---

### GET /history/test-sessions?limit=100
Last N test sessions.

**Response:**
```json
{
  "sessions": [
    {
      "id": 10, "session_id": "judge-abc12345",
      "test_case_name": "TC-01: Perfect Clean Match",
      "test_category": "judge_demo",
      "verdict": "CLEAN", "confidence_score": 100,
      "pass_threshold": 85, "soft_threshold": 55,
      "initial_leniency": 1,
      "timestamp": "2026-05-26T10:00:00",
      "checks": [/* check objects */]
    }
  ],
  "count": 10
}
```

---

### GET /history/patterns
Returns pattern memory (same data as `/self-improve/memory`).

---

## Testing Endpoint

### POST /test/run-all-judge-cases
Runs all 10 judge test cases from `test_data/judge_test_cases.py`.

**Response:**
```json
{
  "session_id": "judge-abc12345",
  "total": 10,
  "correct": 10,
  "accuracy": 100.0,
  "results": [
    {
      "name": "TC-01: Perfect Clean Match",
      "description": "All fields perfectly consistent across PAN, Aadhaar, Bureau",
      "expected_verdict": "CLEAN",
      "actual_verdict": "CLEAN",
      "passed": true,
      "confidence_score": {"score": 100, "label": "HIGH CONFIDENCE", "color": "green"},
      "checks": [/* 7 check objects */]
    }
  ]
}
```
