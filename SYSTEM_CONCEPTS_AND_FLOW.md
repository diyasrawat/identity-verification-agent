# SYSTEM CONCEPTS AND FLOW — VerifyIQ Identity Cross-Verification Agent

*A complete conceptual guide for revision, interview preparation, and technical demos.*

---

## SECTION 1 — SYSTEM OVERVIEW

### What Does VerifyIQ Do?

VerifyIQ is an identity cross-verification platform built for Indian loan underwriting. When a person applies for a loan, they submit documents from three sources:

1. **PAN card** — India's tax identity number, issued by the Income Tax Department. Contains name, DOB, gender, father's name, and 10-character PAN number.
2. **Aadhaar** — India's national biometric ID, issued by UIDAI. Contains name, DOB, gender, father's name, 12-digit number (often partially masked), and address.
3. **Bureau report** — Credit history from credit bureaus like CIBIL. Contains name, DOB, linked PAN number, and Aadhaar last 4 digits.

All three should describe the same person. But in the real world:
- Names are spelled differently: "Prashant" on PAN, "Prashanth" on Aadhaar (South Indian transliteration variant)
- Dates are in different formats: "12/04/1990" vs "April 12th 1990"
- Some names are abbreviated: "P. Kumar" on PAN, "Prashant Kumar" on Aadhaar
- Fields have typos: "2004 arpil 6th" instead of "2004 April 6"
- Father's name has prefixes: "S/O Ramesh Kumar" vs "Ramesh Kumar"
- Aadhaar numbers may be masked: "XXXX-XXXX-5678" in bureau records

VerifyIQ automatically cross-verifies all these documents, handles all these edge cases, gives a structured verdict, explains its reasoning, and gets smarter over time.

### Why Was It Built?

Manual cross-verification is:
- **Slow**: Takes 15–30 minutes per file when done manually
- **Inconsistent**: Different underwriters make different judgment calls on the same data
- **Expensive**: At high volume (50,000+ files/day), you need an automated first pass

VerifyIQ provides a consistent, explainable, audit-able first pass in under 2 seconds.

### What Problem Does It Solve?

The core challenge is that document data is messy, incomplete, and inconsistent — but real people need to get loans. A system that's too strict will reject legitimate applicants ("Prashanth" and "Prashant" ARE the same person). A system that's too loose will approve fraudulent applications.

VerifyIQ uses a hybrid approach:
- **Deterministic rules** for clear-cut cases (DOB exact mismatch → HARD BLOCK)
- **Fuzzy matching** with multiple normalization layers for name variants
- **LLM reasoning** for judgment calls that need context
- **Fraud scoring** to detect patterns across multiple signals

---

## SECTION 2 — COMPLETE ARCHITECTURE

### Backend Architecture

The backend is a FastAPI application (Python) running on port 8000. It is organized into four logical layers:

```
ROUTE LAYER (main.py)
  23 REST API endpoints
  Handles HTTP request/response
  Coordinates agents and persistence
         │
         ▼
AGENT LAYER (agents/)
  7 specialized agents
  Each has a single responsibility
  Agents are called in sequence by the orchestrator
         │
         ▼
LOGIC LAYER (checks.py + llm_functions.py + knowledge/)
  Pure business logic — no HTTP, no persistence
  Normalization, fuzzy matching, LLM calls
         │
         ▼
PERSISTENCE LAYER (persistence/)
  JSON files for agent state
  SQLite for audit history
```

**FastAPI** was chosen because:
- It's async-first (LLM calls are I/O bound — async lets other requests run while waiting)
- Automatic Swagger documentation at /docs
- Pydantic models for request validation
- CORS middleware for the frontend to call it

### Frontend Architecture

The frontend is a React 18 single-page application built with Vite, running on port 5173.

```
App.jsx (root component — owns all shared state)
   │
   ├── Header (title + Judge Demo button)
   ├── Tab Bar (10 tabs)
   ├── File Selector (3 mock files)
   └── Tab Content Router
         ├── Verification Tab
         │     ├── OrchestrationPanel
         │     ├── VerdictBanner
         │     ├── Confidence Score (inline)
         │     ├── Agent Reasoning (inline)
         │     └── LedgerTable
         ├── Address Tab → AddressPanel
         ├── Fraud Tab → FraudPanel
         ├── Underwriter Tab → UnderwriterNotes
         ├── Rules Tab → RuleEngine
         ├── Live Tester Tab → LiveTestPanel
         ├── Audit Trail Tab → AuditTrail
         ├── Self-Improving Tab → SelfImprovingAgent
         ├── Self-Healing Tab → HealingPanel
         └── Memory Tab → MemoryDashboard

+ AskAIDrawer (floating overlay, opened from LedgerTable)
```

**Vite proxy**: All `/api/*` requests from the frontend are proxied to `http://localhost:8000`, with the `/api` prefix stripped. This means in development, you never need CORS headers for frontend-to-backend calls — the proxy handles it.

### Persistence Layer Architecture

Two systems work together:

**JSON Files (memory_store.py)**:
- Pattern memory — cumulative counters updated every run
- Proposals — list of pending/approved/rejected improvement proposals
- Healing log — error events from self-healing
- Custom rules — active rule function code

Key property: **atomic writes** using `.tmp` file + `os.replace()`. No risk of corruption on crash.

**SQLite (audit_db.py)**:
- 6 tables: verifications, check_results, pattern_observations, proposals, healing_events, test_sessions
- All initialized at startup via `init_db()`
- Uses `sqlite3.Row` factory so rows are returned as dicts

### API Layer Architecture

All 23 endpoints live in `main.py`. They are organized into groups:
- Verification: `/verify`, `/orchestrate`, `/verify-live`, `/explain`
- Rule Engine: `/rules/*` (CRUD)
- Self-Improving: `/self-improve/*`
- Healing: `/healing/log`
- Audit/Metrics: `/audit`, `/evaluation/metrics`
- Memory/History: `/memory/*`, `/history/*`
- Testing: `/test/run-all-judge-cases`

### Orchestration Layer Architecture

The orchestrator (`agents/orchestrator.py`) is a single async function `run_orchestrator()` that:
1. Calls each agent in sequence
2. Passes earlier results to later agents
3. Tracks pipeline steps (name, status, summary for each step)
4. Aggregates all results into one response dict

---

## SECTION 3 — UI FLOW

### Verification Tab

**Purpose:** The main verification view. Shows what happened when you ran a file through the pipeline.

**Data received:** Full result from POST /orchestrate — all agent outputs combined.

**API called:** POST /orchestrate (triggered when file button is clicked)

**State managed:** `result`, `loading`, `selectedFile` in App.jsx

**What the user sees:**
1. **OrchestrationPanel** — 7 numbered pipeline steps. Each shows: step name, status (running → complete), summary line. This gives the underwriter visibility into what happened at each stage.
2. **VerdictBanner** — Large colored banner. CLEAN (green), SOFT ISSUES — HUMAN REVIEW (yellow), HARD BLOCK (red).
3. **Confidence Score** — 0–100% progress bar. Green if ≥ 85%, yellow if 55–84%, red below 55%. Shows how certain the system is within the verdict.
4. **Agent Reasoning** — The LLM's assessment of failures taken together. Shows the recommendation badge (PROCEED/REVIEW/REJECT), agent note, and reasoning.
5. **LedgerTable** — Row-by-row check results. Left border color = pass/fail. Shows what was compared, the result badge, the reason, fuzzy score if applicable. Each failed check has an "Ask AI" button.
6. **Stats bar** — Quick summary: N checks run, N passed, N failed.
7. **System Accuracy Metrics** — Collapsible. Click to run all 3 mock files and see Precision/Recall/F1/Accuracy.

### Address Tab

**Purpose:** Deep dive into address verification.

**Data received:** `result.address_result`

**What the user sees:**
- Address verdict (CONSISTENT / LIKELY_SAME / CONFLICTING / NO_ADDRESS_DATA)
- Canonical address (the most trusted one)
- Trust scores for each document source (bar style)
- Normalized versions of each address
- Conflict list with severity and detail
- Knowledge graph lookup results per address
- Agent analysis text (from LLM if conflicts detected, or static summary otherwise)

### Fraud Tab

**Purpose:** Fraud risk assessment.

**Data received:** `result.fraud_result`

**What the user sees:**
- Fraud score 0–100 with color-coded progress bar
- Risk level badge (LOW/MEDIUM/HIGH)
- Each fraud signal that contributed to the score (name, weight, detail)
- Fraud narrative (LLM-written explanation of what pattern was detected)

### Underwriter Tab

**Purpose:** Final decision and professional notes.

**Data received:** `result.final_verdict`

**What the user sees:**
- Final verdict (PROCEED/REVIEW/REJECT) with colored header
- Decision factors: identity verdict, address verdict, fraud score, confidence score
- LLM underwriter notes formatted in 3 sections: SUMMARY, KEY FINDINGS, RECOMMENDED ACTION

### Rules Tab

**Purpose:** Create, preview, manage custom verification rules.

**API calls:** GET /rules/list (on mount), POST /rules/create (generate), POST /rules/save (add), DELETE /rules/{func_name} (remove)

**State managed:** ruleText (text area), generated (preview object), saving, activeRules list

**Interaction flow:**
1. User types rule description in plain English
2. Clicks Generate → preview appears with Python function code
3. Inspects code, optionally regenerates
4. Clicks Add to Engine → rule runs on every future verification
5. Can remove rules at any time

### Live Tester Tab

**Purpose:** Test any data combination with configurable thresholds.

**API:** POST /verify-live

**State managed:** 14 input fields, pass/soft thresholds, initial_leniency toggle, test_case_name, test_category, loading, result

**Features:**
- All fields individually typed
- Pass threshold slider (50–100, default 85)
- Soft threshold slider (30–80, default 55)
- Initial leniency toggle (whether to apply initial-name detection)
- Name test cases with a "Save session" option
- Result shows same format as verification tab but lighter (no agents)

### Self-Improving Tab

**Purpose:** Review what patterns the system has learned and approve/reject improvement proposals.

**API:** GET /self-improve/stats, GET /self-improve/proposals, POST /self-improve/proposals/{id}/approve|reject

**Live polling:** The tab badge shows a pulsing green dot when pending proposals exist (polled every 10 seconds in App.jsx).

**What the user sees:**
- Pattern stats (total runs, patterns found, pending/approved counts)
- Date formats observed (bar chart)
- Name patterns observed
- Pending proposals (each with type, observation, proposed action, priority)
- Approve/Reject buttons per proposal
- Approved proposals (with optionally generated code)
- Rejected archive

### Self-Healing Tab

**Purpose:** View system health — any exceptions that were caught and healed.

**API:** GET /healing/log

**Live polling:** Red dot on tab badge when healedErrors > 0 (polled every 10 seconds).

**What the user sees:**
- If healthy: green box "System healthy — no healing events"
- If events exist: each event with check name, error, root cause, fix, severity
- Known error patterns grouped by error signature with occurrence count

### Memory & History Tab

**Purpose:** Persistent audit dashboard — everything saved to JSON + SQLite.

**API calls (parallel on mount):** GET /memory/stats, GET /history/verifications, GET /history/test-sessions, GET /history/patterns

**Collapsible sections:**
1. Storage Summary — 4 stat cards + file sizes
2. Recent Verifications — table of last 20
3. Test Sessions by Category — grouped by category (judge_demo, manual, etc.)
4. Pattern Memory — bar charts for date formats and name patterns
5. File Details — JSON file sizes + Reset buttons

---

## SECTION 4 — BACKEND FLOW

### Request Enters FastAPI

1. Browser sends POST /orchestrate with profile JSON
2. CORS middleware allows the request (all origins permitted)
3. Route handler `orchestrate(data: dict)` is invoked
4. `_load_custom_rules()` reads custom_rules.json

### Orchestrator Runs

`run_orchestrator(data, custom_rules)` is called. This is an async function because LLM calls are awaited inside.

### Agents Execute (in sequence)

Each agent is called, receives prior results, returns its result.

1. **ExtractionAgent**: Normalizes all fields. Returns cleaned_profile.
2. **IdentityAgent** (inline): Runs 7 checks via `heal_check()`. Applies custom rules. Computes verdict + confidence.
3. **AddressAgent**: Graph lookup + fuzzy + trust scoring. Returns address_result.
4. **LLM Reasoning**: If failures exist, calls `agent_analyze()`. Returns reasoning_result.
5. **FraudAgent**: Scores 5 signals. If score ≥ 30, calls LLM for narrative. Returns fraud_result.
6. **VerdictAgent**: Determines PROCEED/REVIEW/REJECT. Always calls LLM for notes. Returns verdict_result.
7. **AuditAgent**: Creates AUD-XXXX in memory. Returns audit_entry.

### Verification Checks Happen

Inside IdentityAgent, each check:
1. Runs pure Python normalization (normalize_name, normalize_date etc.)
2. Applies comparison logic (exact match, regex, fuzzy score)
3. Returns `{check, input_a, input_b, result, reason, ...}`
4. If result is soft_fail with no reason: LLM generates 1-sentence explanation

### Verdict Generated

`compute_overall_verdict(checks)`:
- Any hard_fail → "HARD BLOCK"
- Any soft_fail → "SOFT ISSUES — HUMAN REVIEW"
- All pass → "CLEAN"

`compute_confidence_score(checks)`:
- Weighted average: pass=100pts, soft=40pts, hard=0pts
- Critical checks (DOB, PAN, Aadhaar last-4) weighted 2×
- Result: 0–100%

### Audit Saved

After pipeline completes, `save_verification()` writes to SQLite. `observe_verification()` updates JSON pattern memory.

### Memory Updated

Pattern memory JSON is updated with date formats seen, name patterns, typos — information about this specific run is added to the rolling aggregate.

---

## SECTION 5 — AGENT SYSTEM

### Agent 1: ExtractionAgent (agents/extraction_agent.py)

**Role:** Data sanitization. Makes all downstream agents work with clean, standardized data.

**Inputs:** Raw profile dict from JSON.

**Processing:**
- `normalize_name()`: UPPERCASE, strip punctuation, collapse spaces
- `normalize_date()`: Parse any date format to YYYY-MM-DD, correct typos
- Normalize PAN, gender, last4 fields

**Outputs:** Cleaned profile + extraction log (what changed and why)

**Why it exists:** Without normalization, you'd need every check function to handle all possible input variations. Centralizing normalization means check functions receive clean data and can focus on their logic.

### Agent 2: IdentityAgent (inline in orchestrator)

**Role:** Core cross-verification. Runs the 7 definitive checks.

**Inputs:** Cleaned profile, custom rules list.

**Processing:** Calls 7 check functions via `heal_check()`. Applies custom rules. Computes verdict.

**Outputs:** checks[], identity_verdict, confidence_score.

**Why inline:** The identity check is the central logic of the system. It directly uses functions from checks.py and is tightly coupled to the orchestrator's flow.

### Agent 3: AddressAgent (agents/address_agent.py)

**Role:** Multi-source address reconciliation with intelligent conflict detection.

**Inputs:** addresses dict, doc_dates dict, profile.

**Processing:** Knowledge graph lookup for each address pair, fuzzy fallback, trust scoring with recency.

**Outputs:** address_result with verdict, canonical address, trust scores, conflicts, LLM analysis.

**Why it exists:** Address verification is a separate concern from identity verification. It has its own domain knowledge (the graph), its own scoring system, and its own LLM call. Separating it keeps the identity checks clean.

### Agent 4: LLM Reasoning (llm_functions.agent_analyze)

**Role:** Holistic analysis of failures taken together.

**Inputs:** Failed checks summary, full profile.

**Processing:** LLM analyzes whether failures together suggest fraud, data error, or coincidence. Returns structured JSON.

**Outputs:** agent_note, confidence (HIGH/MEDIUM/LOW), recommendation (PROCEED/REVIEW/REJECT), reasoning.

**Why LLM here:** Deterministic rules can't analyze combinations. One soft fail might be fine (abbreviation). Three soft fails plus an address conflict needs contextual judgment. The LLM synthesizes signals.

### Agent 5: FraudAgent (agents/fraud_agent.py)

**Role:** Pattern-based fraud risk scoring.

**Inputs:** identity_result, address_result, profile.

**Processing:** Applies 5 fraud signal checks with weights. Sums to 0–100 score. LLM narrative if score ≥ 30.

**Outputs:** fraud_score, risk_level, fraud_signals[], fraud_narrative.

**Why separate:** Fraud detection is a different reasoning pattern from identity verification. It combines signals from multiple agents and has its own scoring logic. Keeping it separate makes both the identity logic and fraud logic simpler and more testable.

### Agent 6: VerdictAgent (agents/verdict_agent.py)

**Role:** Final decision with professional underwriting notes.

**Inputs:** All previous results.

**Processing:** Deterministic PROCEED/REVIEW/REJECT decision. Always calls LLM for underwriter notes.

**Outputs:** final_verdict, verdict_color, underwriter_notes, decision_factors.

**Why separate:** The verdict logic combines all signals from all previous agents. It's the "last mile" where everything is synthesized into an actionable decision with professional documentation.

### Agent 7: AuditAgent (agents/audit_agent.py)

**Role:** Session audit logging.

**Inputs:** Full orchestration result, profile.

**Processing:** Creates a compact summary entry in memory.

**Outputs:** Audit entry (AUD-XXXX).

**Note:** This is currently in-memory only. The SQLite `save_verification()` in main.py is the durable copy. The AuditTrail tab shows the in-memory list (session only).

### ObservationAgent (agents/observation_agent.py)

**Role:** Learning from every run.

**Not part of the pipeline** — called from main.py after orchestrate returns.

**Processing:** Detects date format patterns, name patterns, typos. Updates pattern_memory.json.

### RuleProposerAgent (agents/rule_proposer_agent.py)

**Role:** Proposing system improvements.

**Not part of the pipeline** — called from main.py after observation.

**Processing:** Checks patterns against threshold, creates proposals, saves to proposals.json + SQLite.

### SelfHealingAgent (agents/self_healing_agent.py)

**Role:** Exception handling + LLM error diagnosis.

**Not a standalone agent** — its `heal_check()` function wraps every check call in the pipeline.

**Processing:** try/except wrapper → LLM analysis on failure → safe fallback result.

---

## SECTION 6 — FUZZY MATCHING CONCEPTS

### The Challenge

Indian names have many legitimate variants:
- Regional transliteration: Prashant ↔ Prashanth (Karnataka suffix -th)
- Vowel variations: Kumar ↔ Kumaar, Raju ↔ Rajoo
- Common abbreviations: P. Kumar ↔ Prashant Kumar
- Religious name variants: Mohammed ↔ Mohammad ↔ Muhammed ↔ Muhamed
- Document data entry: "RAMESH S KUMAR" ↔ "RAMESH SURESH KUMAR"

Standard exact matching fails on all of these. Standard fuzzy matching (just one score) misses some and over-approves others.

### The Multi-Layer Approach

**Layer 1: normalize_name()**
```
"Prashant  Kumar." → "PRASHANT KUMAR"
Steps: UPPERCASE → strip non-word chars → collapse spaces
```

**Layer 2: apply_transliteration()**
```
Token lookup in TRANSLITERATION_GRAPH:
"PRASHANTH" → "PRASHANT"
"MOHAMMED"  → "MOHAMMAD"
"LAXMI"     → "LAKSHMI"
(Each token looked up and canonicalized)
```

**Layer 3: is_initial_match()**
```
Detects abbreviated first names:
"P KUMAR" vs "PRASHANT KUMAR"
→ first token of shorter name is 1 char
→ longer name's first token starts with that char
→ surnames match (both "KUMAR")
→ initial_match = True
```

**Layer 4: fuzz.token_sort_ratio()**
```
Why token_sort_ratio, not simple ratio?
"KUMAR PRASHANT" vs "PRASHANT KUMAR" 
  → ratio = 50% (token order matters)
  → token_sort_ratio = 100% (sorts tokens first → "KUMAR PRASHANT" = "KUMAR PRASHANT")

Computed twice: on raw normalized names AND on transliterated names
best_score = max(raw_score, trans_score)
```

**Layer 5: Threshold Adjustment**
```
Base thresholds: pass=85, soft=55

Adjustments:
• If initial_leniency=True AND initial_match=True:
    adj_pass = 85 - 10 = 75
    adj_soft = 55 - 15 = 40
  (Initial abbreviations get more lenient thresholds)

• If transliteration was applied (trans_score > raw_score):
    adj_soft = adj_soft - 10
  (Transliterated names get slightly more lenient soft threshold)
```

**Layer 6: Final Verdict**
```
If initial_match AND surnames match → soft_fail (LLM explains)
If best_score ≥ adj_pass → pass
If best_score ≥ adj_soft → soft_fail (LLM explains)
Else → hard_fail
```

### Transliteration Graph

```python
TRANSLITERATION_GRAPH = {
    # South Indian endings
    "PRASHANTH": "PRASHANT",
    "VENKATESH": "VENKATESHA",
    # Common vowel variants
    "KUMAAR": "KUMAR",
    "LAXMI": "LAKSHMI",
    # Surname variants
    "SHARMA": "SARMA",
    "MUKHERJEE": "MUKERJEE",
    # Mohammed variants
    "MOHAMMED": "MOHAMMAD",
    "MUHAMMED": "MOHAMMAD",
    "MOHAMAD": "MOHAMMAD",
    # ... 30+ total
}
```

When comparing names, each token is looked up. If a token appears as a key, it's replaced with the canonical value. Reverse check ensures canonical values are also matched.

### Father Name Prefix Stripping

Before fuzzy matching father names:
```python
FATHER_PREFIX_GRAPH = [
    "LATE", "SH", "SHRI", "S/O", "D/O", "W/O",
    "C/O", "SON OF", "DAUGHTER OF", "WIFE OF",
    "F/O", "FATHER OF", "CARE OF",
]
```

"S/O RAMESH KUMAR" → strip "S/O" → "RAMESH KUMAR" → then fuzzy match.

---

## SECTION 7 — SELF-IMPROVING SYSTEM

### The Learning Loop

Every time `/orchestrate` is called, the system learns:
1. What date formats did it see?
2. What name patterns appeared?
3. Were any known typos present?
4. What checks are failing repeatedly?

This data accumulates in `pattern_memory.json`. When any pattern exceeds threshold=3, the system proposes an improvement.

### Observation → Proposal → Approval Loop

```
Run 1: DD/MM/YYYY seen in PAN.dob → count = 1
Run 2: DD/MM/YYYY seen again → count = 2
Run 3: DD/MM/YYYY seen again → count = 3 ← THRESHOLD HIT

→ RuleProposerAgent creates proposal:
  "DATE_FORMAT_HANDLER: DD/MM/YYYY seen 3 times.
   Add explicit handler in normalize_date()"

→ Saved to proposals.json, shown in Self-Improving tab

→ Human clicks Approve
→ LLM generates Python dict:
  {change_type: "format_addition",
   description: "Add DD/MM/YYYY handler",
   code: "r'^\d{2}/\d{2}/\d{4}$'",
   location: "checks.py → normalize_date() formats list"}

→ Developer applies the change manually
```

### Proposal Types

| Type | What triggers it | auto_generate |
|---|---|---|
| DATE_FORMAT_HANDLER | Non-standard date format seen ≥3× | True |
| NAME_THRESHOLD_ADJUSTMENT | INITIAL_FIRST_NAME pattern seen ≥3× | True |
| TYPO_CORRECTION_RULE | Known typo seen in input ≥3× | True |
| SYSTEMATIC_HARD_FAIL | Same check hard-failing ≥6× | False |

SYSTEMATIC_HARD_FAIL has `auto_generate: False` because it often means a data source problem, not a code fix — requires human judgment.

---

## SECTION 8 — SELF-HEALING SYSTEM

### Why Healing Matters

In production, you will get:
- Null/missing fields in applicant data
- Fields with unexpected types
- Edge case date strings that all parsers fail on
- Encoding issues in names with special characters

Without healing, a single bad field causes the entire verification to fail with a 500 error. The underwriter gets nothing.

### The heal_check() Wrapper

```python
def heal_check(check_name, check_func, profile, *args) -> dict:
    try:
        return check_func(*args)     # Normal execution
    except Exception as e:
        # 1. Fingerprint the error
        sig = create_error_signature(e, {"check": check_name})
        
        # 2. LLM diagnosis
        analysis = analyze_error_with_llm(e, check_name, {"args": str(args)})
        
        # 3. Log to JSON + SQLite
        ...log to healing_log.json...
        ...save_healing_event() to SQLite...
        
        # 4. Return safe fallback
        return {
            "check": check_name,
            "result": "soft_fail",
            "reason": f"[Self-Healed] {analysis['root_cause']}. Fix: {analysis['proposed_fix']}",
            "healed": True,
            ...
        }
```

### What the LLM Diagnoses

When an error is caught, the LLM receives:
- Check name and error type
- Error message
- First 800 chars of traceback
- First 200 chars of input data

Returns structured JSON:
```json
{
  "root_cause": "pan.dob is null — normalize_date() called with None",
  "error_category": "NULL_VALUE",
  "affected_field": "pan.dob",
  "proposed_fix": "Add null guard before calling normalize_date",
  "severity": "MEDIUM",
  "auto_fixable": true,
  "fix_code": "if not date_str: return ''"
}
```

### Error Signature System

Each unique error gets an 8-character MD5 fingerprint:
```python
sig = hashlib.md5(f"{type(error).__name__}:{str(error)[:50]}".encode()).hexdigest()[:8]
```

The `known_errors[sig]["count"]` increments each time the same error recurs. This shows systematic issues vs one-off incidents.

---

## SECTION 9 — COMPLETE END-TO-END FLOW

```
USER ACTION: Click "FL-001 — Clean"
    │
    ▼
BROWSER (App.jsx):
  1. fetch("/mock_files/file1_clean.json") → setProfile(data)
  2. fetch("/api/orchestrate", {method: "POST", body: profile_json})
  3. setLoading(true) → shows "Running agentic pipeline..."
    │
    │   (Vite proxy: /api/orchestrate → http://localhost:8000/orchestrate)
    ▼
FASTAPI (main.py):
  4. CORS middleware passes the request
  5. _load_custom_rules() → reads custom_rules.json
  6. await run_orchestrator(data, custom_rules)
    │
    ▼
ORCHESTRATOR (agents/orchestrator.py):
  7.  ExtractionAgent: normalizes names, dates → cleaned_profile
  8.  IdentityAgent: 7 checks via heal_check()
      → check_pan_format → pass
      → check_dob → pass
      → check_gender → pass
      → check_aadhaar_last4 → pass
      → check_name_fuzzy (PAN/Aadhaar) → pass
      → check_name_fuzzy (Bureau/PAN) → pass
      → check_father_name → pass
  9.  All checks pass → identity_verdict = "CLEAN"
  10. LLM Reasoning: no failures → returns static PROCEED/HIGH
  11. AddressAgent: graph confirms MG Road matches → CONSISTENT
  12. FraudAgent: no signals → fraud_score = 0, LOW RISK
  13. VerdictAgent: PROCEED → LLM writes underwriter notes
  14. AuditAgent: creates AUD-0001 in memory
  15. Returns full_result dict
    │
    ▼
FASTAPI (main.py, after orchestrate returns):
  16. observe_verification() → updates pattern_memory.json
      (increments YYYY-MM-DD count, FULL_NAME count)
  17. analyze_and_propose() → no proposals yet (counts below threshold)
  18. save_verification() → SQLite: 1 row in verifications, 7 rows in check_results
  19. Returns JSON response to browser
    │
    ▼
BROWSER (App.jsx):
  20. setResult(responseJson) → React re-renders
  21. setLoading(false) → removes loading indicator
  22. Verification tab shows:
      - OrchestrationPanel: 7 steps all "complete"
      - VerdictBanner: GREEN "CLEAN"
      - Confidence Score: 100% green
      - Agent Reasoning: "All checks passed. PROCEED. HIGH confidence."
      - LedgerTable: 7 rows, all green, all PASS

USER NAVIGATES TO ADDRESS TAB:
  23. AddressPanel receives result.address_result
  24. Shows CONSISTENT verdict
  25. Shows trust scores: bank_statement(75) > aadhaar(67.5 after recency)
  26. Shows graph confirmed: MG Road Pune alias match

USER NAVIGATES TO MEMORY TAB:
  27. MemoryDashboard fetches:
      - GET /memory/stats → shows 1 verification in SQLite
      - GET /history/verifications → shows FL-001, CLEAN, 100%
      - GET /history/patterns → shows YYYY-MM-DD: 2, FULL_NAME: 2
```

---

## SECTION 10 — LEARNING NOTES

### Why Separate Agents?

**Single Responsibility Principle in practice.** Each agent does one thing:
- ExtractionAgent knows nothing about fraud signals
- FraudAgent knows nothing about date format normalization
- VerdictAgent doesn't run fuzzy matching

This means:
- You can test each agent independently
- A bug in AddressAgent doesn't affect IdentityAgent
- You can swap the FraudAgent's logic without touching any other file
- New agents (e.g., a DocumentAuthenticityAgent) can be added as step 8 without modifying existing agents

### Why Fuzzy Matching Beats Exact Matching for Names

Exact matching fails because names have legitimate variations. "Prashanth" and "Prashant" are the same name — one is the South Indian spelling, one is the North Indian spelling. Rejecting this as a mismatch would unfairly block legitimate applicants from Karnataka.

Fuzzy matching scores similarity instead of requiring equality. The multi-layer approach (normalization → transliteration → initial detection → threshold adjustment) handles all the common variants encountered in Indian ID documents.

### Why Persistence Is Needed

Without persistence:
- Every server restart loses all learning (pattern memory resets to zero)
- No history of past verifications for auditing
- Self-improving proposals disappear
- Custom rules disappear
- Healing log is lost

With persistence:
- The system gets smarter over time (more verifications → more pattern data → better proposals)
- Full audit trail for regulatory compliance
- Custom rules survive deployments
- Healing events help developers find systematic data quality issues

### Why the Address Knowledge Graph Improves Fuzzy Matching

"MG Road" and "Mahatma Gandhi Road" have very low string similarity (~30% fuzzy score). Without the graph, this would look like a genuine address conflict and potentially contribute to a fraud flag.

The graph knows these are the same location. It resolves the match before fuzzy matching even runs, preventing false conflicts and making the system smarter about Indian geography.

The graph also catches genuine differences: "MG Road Bangalore" and "Marine Drive Mumbai" would both be in the graph but under different cities, giving a GRAPH_CONFIRMED_DIFFERENT result with high confidence.

### Why Orchestration Matters

Without an orchestrator, you'd have one huge function with all the logic mixed together. The orchestrator pattern:
- Makes the pipeline visible (pipeline_steps in the response)
- Allows each step to fail gracefully without breaking others
- Makes it easy to add/remove/reorder steps
- Separates "what order do things run in" from "what does each thing do"

The 7 pipeline steps visible in the OrchestrationPanel give the underwriter a mental model of what happened — they can see "Address Verification: CONSISTENT | 0 hard conflicts" before looking at the full address details.
