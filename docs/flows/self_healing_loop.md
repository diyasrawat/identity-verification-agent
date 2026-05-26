# Self-Healing System Loop

## Overview

The self-healing system wraps every identity check in a try/except handler. When a check fails with a runtime exception (not a verification failure — an actual Python error), the system catches it, uses the LLM to diagnose the root cause, logs the event, and returns a safe fallback result so the pipeline can continue.

---

## The Healing Flow

```
ORCHESTRATOR calls heal_check():

  heal_check("PAN Format Validity", check_pan_format, profile, pan_number)
                        │
              ┌─────────┴─────────────┐
              │ try:                  │ except Exception as e:
              │   return check_func() │
              │   (normal path)       │  ┌───────────────────────────────────┐
              │                       │  │ 1. create_error_signature(e)      │
              │                       │  │    sig = MD5(f"{type(e)}:{str(e)}")│
              │                       │  │    → 8-char hex fingerprint        │
              │                       │  │                                   │
              │                       │  │ 2. analyze_error_with_llm()       │
              │                       │  │    Sends to LLM:                  │
              │                       │  │    - check name                   │
              │                       │  │    - error type + message          │
              │                       │  │    - error traceback (800 chars)   │
              │                       │  │    - input data (200 chars)        │
              │                       │  │                                   │
              │                       │  │    LLM returns:                   │
              │                       │  │    {root_cause,                   │
              │                       │  │     error_category: FORMAT_ERROR/ │
              │                       │  │       NULL_VALUE/TYPE_MISMATCH/   │
              │                       │  │       ENCODING/THRESHOLD/UNKNOWN, │
              │                       │  │     affected_field,               │
              │                       │  │     proposed_fix,                 │
              │                       │  │     severity: CRITICAL/HIGH/MED/LOW│
              │                       │  │     auto_fixable: bool,           │
              │                       │  │     fix_code: str or null}        │
              │                       │  │                                   │
              │                       │  │ 3. Build healing_entry:           │
              │                       │  │    {timestamp, error_signature,   │
              │                       │  │     check_name, error_type,       │
              │                       │  │     error_message, analysis,      │
              │                       │  │     healed: true,                 │
              │                       │  │     fallback_used: "safe_default"}│
              │                       │  │                                   │
              │                       │  │ 4. _load_healing() from JSON      │
              │                       │  │    Append to data["events"]       │
              │                       │  │    (keep last 100 only)           │
              │                       │  │    Track signature in known_errors │
              │                       │  │    known_errors[sig].count += 1   │
              │                       │  │    memory_store.save("healing_log")│
              │                       │  │                                   │
              │                       │  │ 5. save_healing_event() → SQLite  │
              │                       │  │    (check_name, error_type,       │
              │                       │  │     error_message, root_cause,    │
              │                       │  │     proposed_fix, auto_fixable)   │
              │                       │  │                                   │
              │                       │  │ 6. Return safe soft_fail:         │
              │                       │  │    {check: check_name,            │
              │                       │  │     input_a: str(args[0]),        │
              │                       │  │     input_b: str(args[1]),        │
              │                       │  │     result: "soft_fail",          │
              │                       │  │     reason: "[Self-Healed] ...",  │
              │                       │  │     healed: True,                 │
              │                       │  │     error_signature: sig,         │
              │                       │  │     severity: analysis.severity}  │
              └───────────────────────┘  └───────────────────────────────────┘
                        │                              │
                        └──────────────────────────────┘
                                       │
                                       ▼
                        Pipeline continues to next check
                        (never crashes, always produces a result)
```

---

## Healing Log Data Structure

```json
{
  "events": [
    {
      "timestamp": "2026-05-26T10:00:00",
      "error_signature": "a1b2c3d4",
      "check_name": "Date of Birth (PAN vs Aadhaar)",
      "error_type": "TypeError",
      "error_message": "'NoneType' object has no attribute 'strip'",
      "analysis": {
        "root_cause": "pan.dob field is null — normalize_date() called with None",
        "error_category": "NULL_VALUE",
        "affected_field": "pan.dob",
        "proposed_fix": "Add null guard: if not date_str: return '' in normalize_date()",
        "severity": "MEDIUM",
        "auto_fixable": true,
        "fix_code": "if not date_str: return ''"
      },
      "healed": true,
      "fallback_used": "safe_default"
    }
  ],
  "known_errors": {
    "a1b2c3d4": {
      "count": 2,
      "analysis": { ... },
      "check_name": "Date of Birth (PAN vs Aadhaar)"
    }
  }
}
```

---

## What the HealingPanel Shows

```
HealingPanel.jsx fetches GET /healing/log on mount

If total_healed == 0:
  Shows green box: "System is healthy — no healing events recorded."

If events exist:
  Header: "Total healed: N | Unique patterns: M"

  For each event:
  ┌─────────────────────────────────────────┐
  │ Check: Date of Birth (PAN vs Aadhaar)  │
  │ Error: TypeError                        │
  │ Root cause: pan.dob is null             │
  │ Fix: Add null guard in normalize_date() │
  │ Severity: MEDIUM  Auto-fixable: Yes     │
  │ Signature: a1b2c3d4                     │
  └─────────────────────────────────────────┘

  Known error patterns (grouped by signature):
  Shows recurring errors with hit count
```

---

## Why This Matters

Without heal_check(), a single null value in pan.dob would crash the entire pipeline and return a 500 error to the frontend. The user would see nothing.

With heal_check():
1. The specific check that failed returns soft_fail instead of crashing
2. All other 6 checks still run normally
3. The pipeline produces a partial but useful verdict
4. The developer gets detailed diagnosis with LLM analysis
5. The underwriter knows which check had an issue and why

This is especially important in production where real applicant data can be missing, malformed, or unexpected.

---

## Error Signature System

Each unique error is fingerprinted:
```python
sig = hashlib.md5(f"{type(error).__name__}:{str(error)[:50]}".encode()).hexdigest()[:8]
```

The first time a signature is seen, a new `known_errors[sig]` entry is created.  
Each subsequent occurrence increments `known_errors[sig]["count"]`.

This lets you see: "TypeError on DOB check has happened 8 times" — a systematic data quality issue rather than a one-off.

When `count` is high, this is exactly the kind of signal the **self-improving system** would eventually surface as a `SYSTEMATIC_HARD_FAIL` proposal.
