# System Architecture — VerifyIQ

## Overview

VerifyIQ is a full-stack identity verification platform built as a decoupled React frontend + FastAPI backend. The backend exposes 23 REST endpoints and runs a 7-agent pipeline for each verification request. A dual persistence layer (JSON + SQLite) stores all agent memory and audit history across server restarts.

---

## High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         BROWSER (port 5173)                          │
│                                                                      │
│  React 18 + Vite 5 + Tailwind CSS v3                                │
│                                                                      │
│  App.jsx ──► 10 Tab Router                                          │
│               ├── Verification (OrchestrationPanel + VerdictBanner  │
│               │                 + LedgerTable + ConfidenceScore)    │
│               ├── Address (AddressPanel)                             │
│               ├── Fraud (FraudPanel)                                 │
│               ├── Underwriter (UnderwriterNotes)                     │
│               ├── Rules (RuleEngine)                                 │
│               ├── Live Tester (LiveTestPanel)                        │
│               ├── Audit Trail (AuditTrail)                           │
│               ├── Self-Improving (SelfImprovingAgent)                │
│               ├── Self-Healing (HealingPanel)                        │
│               └── Memory & History (MemoryDashboard)                │
│                                                                      │
│  State: selectedFile, profile, result, activeTab, proposals count    │
│  Polling: /api/self-improve/stats + /api/healing/log (10s interval) │
└────────────────────────┬─────────────────────────────────────────────┘
                         │  HTTP Fetch → /api/* (Vite proxy)
                         │  → strips /api prefix
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (port 8000)                       │
│                                                                      │
│  main.py                                                             │
│  ├── CORS middleware (allow_origins=["*"])                           │
│  ├── init_db() called at startup                                     │
│  ├── 23 route handlers                                               │
│  ├── run_custom_rules() helper                                       │
│  └── compute_confidence_score() helper                               │
│                                                                      │
│  checks.py (no FastAPI dependency — pure Python)                    │
│  ├── normalize_name, normalize_date, normalize_gender                │
│  ├── normalize_pan, normalize_father_name                            │
│  ├── apply_transliteration, is_initial_match                        │
│  ├── GENDER_GRAPH, TRANSLITERATION_GRAPH, FATHER_PREFIX_GRAPH       │
│  ├── check_pan_format, check_dob, check_gender                      │
│  ├── check_aadhaar_last4, check_name_fuzzy, check_father_name       │
│  └── compute_overall_verdict, compute_confidence_score              │
│                                                                      │
│  llm_functions.py                                                    │
│  ├── OpenAI client → base_url="https://openrouter.ai/api/v1"        │
│  ├── MODEL = "anthropic/claude-haiku-4-5"                           │
│  ├── explain_soft_fail()   — 1-sentence name mismatch explanation   │
│  ├── explain_ask_ai()      — on-demand check explanation             │
│  ├── agent_analyze()       — structured verdict reasoning (async)   │
│  └── create_rule_code()    — generates Python function (async)      │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────────┐
         ▼               ▼                   ▼
┌─────────────┐  ┌──────────────┐  ┌────────────────────┐
│  AGENTS/    │  │  KNOWLEDGE/  │  │  PERSISTENCE/      │
│             │  │              │  │                    │
│ orchestrator│  │ address_graph│  │ memory_store.py    │
│ extraction  │  │ 15+ road     │  │   load/save/append │
│ address     │  │ nodes with   │  │   atomic .tmp swap │
│ fraud       │  │ aliases,     │  │                    │
│ verdict     │  │ cities,      │  │ audit_db.py        │
│ audit       │  │ pincodes     │  │   6 SQLite tables  │
│ observation │  └──────────────┘  │   init on startup  │
│ rule_proposer                    └────────────────────┘
│ self_healing│
└─────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                 OPENROUTER API                              │
│  anthropic/claude-haiku-4-5                                │
│  Used by: address_agent, fraud_agent, verdict_agent,       │
│           self_healing_agent, rule_proposer_agent,         │
│           llm_functions (explain + analyze + create)       │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Module Dependency Map

```
main.py
  │
  ├── checks.py
  │     └── rapidfuzz, re, datetime, dateutil
  │
  ├── llm_functions.py
  │     └── openai (OpenRouter), os, json, dotenv
  │
  ├── agents/orchestrator.py
  │     ├── checks.py
  │     ├── llm_functions.py
  │     ├── agents/extraction_agent.py
  │     │     └── checks.py (normalize_name, normalize_date)
  │     ├── agents/address_agent.py
  │     │     ├── knowledge/address_graph.py
  │     │     ├── openai (OpenRouter)
  │     │     └── rapidfuzz
  │     ├── agents/fraud_agent.py
  │     │     └── openai (OpenRouter)
  │     ├── agents/verdict_agent.py
  │     │     └── openai (OpenRouter)
  │     ├── agents/audit_agent.py  (in-memory only)
  │     └── agents/self_healing_agent.py
  │           ├── openai (OpenRouter)
  │           ├── persistence/memory_store.py
  │           └── persistence/audit_db.py
  │
  ├── agents/observation_agent.py
  │     └── persistence/memory_store.py
  │
  ├── agents/rule_proposer_agent.py
  │     ├── openai (OpenRouter)
  │     ├── persistence/memory_store.py
  │     └── persistence/audit_db.py
  │
  ├── persistence/memory_store.py
  │     └── json, os (stdlib)
  │
  ├── persistence/audit_db.py
  │     └── sqlite3, json (stdlib)
  │
  └── test_data/judge_test_cases.py  (only used by /test/run-all-judge-cases)
```

---

## Data Flow: A Single Verification Request

```
1. Browser sends POST /api/orchestrate
   Body: { applicant_id, pan{}, aadhaar{}, bureau{}, addresses{}, doc_dates{} }

2. Vite proxy strips /api → POST http://localhost:8000/orchestrate

3. main.py @app.post("/orchestrate")
   a. Calls run_orchestrator(data, custom_rules=_load_custom_rules())
   b. Gets full_result dict back
   c. Calls observe_verification() → updates pattern_memory.json
   d. Calls analyze_and_propose() → may create new proposals
   e. Calls save_verification() → writes to SQLite
   f. Returns full_result + observation + new_proposals_generated

4. Frontend receives JSON, React setState triggers re-render
   All 10 tab components pull their data from result object
```

---

## Persistence Architecture

### JSON Layer (memory_store.py)
```
backend/memory_data/
├── pattern_memory.json    — ObservationAgent reads/writes per run
├── proposals.json         — RuleProposerAgent reads/writes
├── healing_log.json       — SelfHealingAgent reads/writes
└── custom_rules.json      — main.py reads on every verification
                             main.py writes on /rules/save and /rules/delete

Atomic write pattern:
  1. Write data to {key}.json.tmp
  2. os.replace(.tmp, .json)  ← atomic on POSIX and Windows (same drive)
  Guarantees no partial-write corruption on server crash
```

### SQLite Layer (audit_db.py)
```
backend/memory_data/audit.db

Tables:
  verifications       — one row per /orchestrate call
  check_results       — one row per check per verification (FK: verification_id)
  pattern_observations — reserved for future pattern-level SQL queries
  proposals           — mirror of proposals.json (queryable)
  healing_events      — each exception caught by heal_check()
  test_sessions       — each /verify-live or /test/run-all-judge-cases run
```

---

## Frontend State Architecture

```
App.jsx (root state owner)
├── selectedFile    — which mock file is selected ("FL-001" etc.)
├── profile         — raw JSON loaded from the mock file
├── result          — full response from /orchestrate (all agent outputs)
├── askAICheck      — the check object for the open AskAI drawer
├── loading         — boolean for pipeline running indicator
├── activeTab       — current tab ID ("verification", "address", etc.)
├── pendingProposals — count polled from /self-improve/stats (10s)
├── healedErrors    — count polled from /healing/log (10s)
├── metrics         — precision/recall data (loaded on demand)
├── judgeRunning    — boolean for Judge Demo button state
└── judgeToast      — toast notification state

Components with their own local state:
├── LiveTestPanel   — input fields, loading, result, threshold sliders
├── RuleEngine      — ruleText, generated, activeRules
├── SelfImprovingAgent — proposals, memory, stats, loading states
├── HealingPanel    — log data, loading
├── MemoryDashboard — stats, verifications, testSessions, patterns
└── AuditTrail      — entries
```

---

## Confidence Score Algorithm

```python
weights = {"pass": 100, "soft_fail": 40, "hard_fail": 0}
critical_prefixes = ["Date of Birth", "PAN Format", "Aadhaar Last"]

for check in checks:
    score = weights[check.result]
    weight = 2 if any(p in check.name for p in critical_prefixes) else 1
    weighted_sum += score * weight
    weight_total += 100 * weight

final_score = round((weighted_sum / weight_total) * 100)

Thresholds:
  ≥ 85 → HIGH CONFIDENCE (green)
  ≥ 55 → MEDIUM CONFIDENCE (yellow)
  < 55 → LOW CONFIDENCE (red)
```

---

## Address Trust Scoring

```
Document Source  | Base Trust | Reasoning
─────────────────┼────────────┼──────────────────────────────────────────
aadhaar          |     90     | Biometric-verified government ID
gst              |     80     | Government-registered business address
bank_statement   |     75     | Bank-verified, recent
pan              |     45     | Often not updated after moves
utility_bill     |     35     | Could be old, may not reflect current home
self_declared    |     15     | No third-party verification

Recency multiplier (based on doc_dates in profile):
  age 0-1 years → 1.00
  age 1-2 years → 0.85
  age 2-3 years → 0.70
  age 3+ years  → 0.50
  unknown       → 0.75

Final trust score = base × recency_multiplier
Canonical address = address from highest-scoring source
```
