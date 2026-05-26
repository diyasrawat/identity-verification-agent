# Self-Improving System Loop

## Overview

The self-improving system is a passive learning loop built on top of the verification pipeline. It watches every run, records patterns, and proposes improvements when patterns exceed a threshold. A human reviews proposals before any change takes effect.

---

## The Complete Loop

```
                    ┌───────────────────────────────────┐
                    │         EVERY /orchestrate CALL    │
                    │                                   │
                    │  After pipeline completes:         │
                    │  1. observe_verification()         │
                    │  2. analyze_and_propose()          │
                    └──────────────┬────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  OBSERVATION AGENT (agents/observation_agent.py)                 │
│                                                                  │
│  observe_verification(profile, checks, verdict)                  │
│                                                                  │
│  1. Load pattern_memory from pattern_memory.json                 │
│  2. Increment total_runs counter                                 │
│                                                                  │
│  3. Date format detection:                                       │
│     detect_date_format(pan.dob):                                │
│       Matches against patterns like YYYY-MM-DD, DD/MM/YYYY etc.  │
│     → mem["date_formats"]["DD/MM/YYYY"] += 1                     │
│                                                                  │
│  4. Name pattern detection:                                      │
│     detect_name_pattern(pan.name):                               │
│       INITIAL_FIRST_NAME, MULTIPLE_INITIALS, SINGLE_WORD,        │
│       FULL_NAME                                                  │
│     → mem["name_patterns"]["INITIAL_FIRST_NAME"] += 1            │
│                                                                  │
│  5. Typo detection in all text fields:                           │
│     detect_typos(field_text) — checks known typo dictionary      │
│     → mem["soft_fail_patterns"]["typo:januray"] += 1             │
│                                                                  │
│  6. Fail pattern tracking:                                       │
│     Each soft_fail check → record name pattern                   │
│     Each hard_fail check → record check name                     │
│                                                                  │
│  7. Append observation to recent_observations (last 50)          │
│  8. Save memory_store.save("pattern_memory", mem)               │
│                                                                  │
│  Returns: observation dict for this run                          │
└──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  RULE PROPOSER AGENT (agents/rule_proposer_agent.py)             │
│                                                                  │
│  analyze_and_propose(pattern_memory)                             │
│  PROPOSAL_THRESHOLD = 3                                          │
│                                                                  │
│  Scans 4 pattern types:                                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ DATE_FORMAT_HANDLER                                        │  │
│  │ Triggers if: date_format count ≥ 3                        │  │
│  │ AND format is not YYYY-MM-DD, empty, UNKNOWN_FORMAT        │  │
│  │ AND no existing proposal for this format                   │  │
│  │ Example: "DD/MM/YYYY seen 4 times → add explicit handler"  │  │
│  │ auto_generate: True                                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NAME_THRESHOLD_ADJUSTMENT                                  │  │
│  │ Triggers if: INITIAL_FIRST_NAME count ≥ 3                 │  │
│  │ Observation: "Initial name (P. Kumar) seen N times,        │  │
│  │              consistently causes soft fails that get approved"│
│  │ Proposed: Lower soft-fail threshold for initials          │  │
│  │ auto_generate: True                                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ TYPO_CORRECTION_RULE                                       │  │
│  │ Triggers if: typo:X count ≥ 3                             │  │
│  │ Example: "typo:januray seen 3 times → add to typo dict"   │  │
│  │ auto_generate: True, priority: HIGH                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ SYSTEMATIC_HARD_FAIL                                       │  │
│  │ Triggers if: check hard-failing ≥ 6 times (2× threshold)  │  │
│  │ Example: "PAN Format Validity hard failing 8 times —       │  │
│  │           possible data source issue"                      │  │
│  │ auto_generate: False (requires human judgment)             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  For each new proposal:                                          │
│  → add_proposal(proposal)                                        │
│    → assigns PROP-XXXX ID                                        │
│    → saves to proposals.json + SQLite proposals table            │
│                                                                  │
│  Returns: list of newly generated proposals                      │
└──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  PROPOSALS STORED IN proposals.json                              │
│  {                                                               │
│    "pending": [                                                  │
│      {                                                           │
│        "id": "PROP-0001",                                        │
│        "type": "DATE_FORMAT_HANDLER",                            │
│        "trigger_pattern": "DD/MM/YYYY",                          │
│        "observation": "...",                                     │
│        "proposed_action": "...",                                 │
│        "priority": "MEDIUM",                                     │
│        "auto_generate": true,                                    │
│        "status": "pending",                                      │
│        "created_at": "2026-05-26T10:00:00"                      │
│      }                                                           │
│    ],                                                            │
│    "approved": [],                                               │
│    "rejected": []                                                │
│  }                                                               │
└──────────────────────────────────────────────────────────────────┘
                                   │
                     ┌─────────────┴────────────────┐
                     │                              │
                     ▼                              ▼
          ┌──────────────────┐          ┌──────────────────────┐
          │ HUMAN APPROVES   │          │ HUMAN REJECTS        │
          │                  │          │                      │
          │ POST /self-improve│          │ POST /self-improve   │
          │ /proposals/{id}  │          │ /proposals/{id}      │
          │ /approve         │          │ /reject              │
          └────────┬─────────┘          └──────────────────────┘
                   │
                   ▼
       ┌───────────────────────────────────────┐
       │  approve_proposal(proposal_id)        │
       │  → status: "approved"                 │
       │  → moves to data["approved"] list     │
       │  → saves proposals.json               │
       │                                       │
       │  If proposal.auto_generate:           │
       │  → generate_rule_code_for_proposal()  │
       │    LLM generates Python change dict   │
       │    {change_type, description,         │
       │     code, location}                   │
       │  → returned in API response           │
       └───────────────────────────────────────┘
                   │
                   ▼
       NOTE: Auto-generated code describes what
       change should be made (file + location),
       but does NOT automatically modify files.
       Developer applies the change manually.
```

---

## Pattern Memory Data Structure

```python
{
    "date_formats": {
        "YYYY-MM-DD": 20,      # Standard, seen most often
        "DD/MM/YYYY": 4,       # Needs explicit handling
        "ORDINAL_SUFFIX": 2,   # "6th April 2004"
        "MONTH_NAME": 3,       # "April 12 1990"
    },
    "name_patterns": {
        "FULL_NAME": 18,       # "Prashant Kumar" — normal
        "INITIAL_FIRST_NAME": 4, # "P. Kumar" — causes soft fails
        "SINGLE_WORD": 1,      # "Kumar" — unusual
        "MULTIPLE_INITIALS": 0,
    },
    "soft_fail_patterns": {
        "INITIAL_FIRST_NAME": 4,
        "typo:januray": 1,
    },
    "hard_fail_patterns": {
        "Date of Birth (PAN vs Aadhaar)": 2,
    },
    "total_runs": 15,
    "last_updated": "2026-05-26T10:00:00",
    "observations": [
        {
            "timestamp": "2026-05-26T10:00:00",
            "applicant_id": "FL-001",
            "verdict": "CLEAN",
            "patterns_found": [{"field": "pan.name", "pattern": "FULL_NAME"}],
            "typos_found": [],
            "format_anomalies": []
        }
        // ... last 50 observations
    ]
}
```

---

## Why This Architecture?

**Why not just auto-fix patterns?**
Auto-applying code changes is risky. A proposal to "lower threshold for initials" might be correct 95% of the time but wrong in fraud cases. The human approval step ensures a domain expert reviews every change before it affects the verification logic.

**Why PROPOSAL_THRESHOLD = 3?**
One occurrence might be noise. Three occurrences is a pattern. This threshold prevents the system from generating proposals for one-off unusual inputs.

**Why JSON persistence for pattern_memory?**
Pattern memory is a running aggregate. It needs to be readable by agents on every run without database queries. JSON files are fast to read and write, and the atomic write pattern prevents corruption.
