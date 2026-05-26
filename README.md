# VerifyIQ: Identity Cross-Verification Agent

> **FlexiLoans Hackathon - Underwriting Intelligence Platform**  
> An agentic AI system that cross-verifies Indian identity documents (PAN, Aadhaar, Bureau) for loan underwriting, using a 7-agent pipeline, multi-layer fuzzy matching, self-healing, and self-improving capabilities.

<img width="1919" height="921" alt="image" src="https://github.com/user-attachments/assets/c10f3c92-6f53-4fd9-be05-8817738ce3c3" />
<img width="1879" height="911" alt="image" src="https://github.com/user-attachments/assets/2071d94c-daec-4e33-8fde-45f78acaa688" />
<img width="1909" height="894" alt="image" src="https://github.com/user-attachments/assets/459f6938-d50c-4cb6-9aba-8be86dc54141" />


**DEMO VIDEO:** [https://drive.google.com/file/d/1ZfmXZlZgxqqYi-0prhApykUZYuLplzM1/view?usp=drive_link](https://drive.google.com/file/d/1V2EBppbVRUJlgTmoYiNP-U8tXlR07N-a/view?usp=sharing)

Try For Yourself:
Live Demo: https://identity-verification-agent.vercel.app

API Docs: https://flexiloans-backend.onrender.com/docs  

GitHub: https://github.com/diyasrawat/identity-verification-agent

---

## Problem Statement

Indian lending companies receive loan applications with data from multiple document sources — PAN cards, Aadhaar, credit bureau records, and address proofs. Each source has its own format quirks, regional transliterations, date formats, masked fields, and data entry errors.

Manual cross-verification is slow (15–30 min per file), inconsistent across underwriters, and expensive at volume. **VerifyIQ** solves this with a 7-agent AI pipeline that cross-verifies all document fields in under 2 seconds, explains its reasoning, learns from patterns, heals from failures, and lets underwriters add custom rules in plain English.

---

## Core Innovations

| Innovation | What It Does |
|---|---|
| **7-agent orchestration pipeline** | Extraction → Identity → Address → Reasoning → Fraud → Verdict → Audit |
| **Multi-layer fuzzy name matching** | Raw score + transliteration graph + initial detection — takes the best score across all layers |
| **Graph-aware address matching** | Knowledge graph of 15+ major Indian road aliases resolves "MG Road" = "Mahatma Gandhi Road" before fuzzy matching |
| **Self-healing agents** | Every check is wrapped in `heal_check()` — exceptions caught, LLM diagnoses root cause, pipeline continues |
| **Self-improving system** | Observation agent records patterns per run; rule proposer fires proposals at threshold=3 hits |
| **Plain-English rule engine** | LLM converts natural language rules into live Python check functions, active immediately |
| **Dual persistence** | JSON files for agent memory + SQLite for full audit trail — survive server restarts |
| **Weighted confidence scoring** | Critical checks (DOB, PAN, Aadhaar last-4) weighted 2x in confidence calculation |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        REACT FRONTEND                           │
│   App.jsx ── 10 Tabs ── 13 Components ── Vite Dev Proxy        │
│   localhost:5173  ──  /api/* → localhost:8000                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP / JSON
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND  (port 8000)                       │
│  main.py — 23 API routes — CORS enabled                        │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                  │
           ▼                                  ▼
┌────────────────────────┐        ┌───────────────────────────┐
│  ORCHESTRATOR          │        │  STANDALONE ROUTES        │
│  run_orchestrator()    │        │  POST /verify             │
│  7-step pipeline       │        │  POST /verify-live        │
└──────────┬─────────────┘        │  /rules/* (CRUD)          │
           │                      │  /self-improve/*          │
    ┌──────▼─────────────────────────────────────┐            │
    │           7-AGENT PIPELINE                 │            │
    │                                            │            │
    │  [1] ExtractionAgent                       │            │
    │      normalize names, dates, PAN, gender   │            │
    │                                            │            │
    │  [2] IdentityAgent (inline in orchestrator)│            │
    │      7 checks, each wrapped in heal_check()│            │
    │      + custom rules from custom_rules.json │            │
    │                                            │            │
    │  [3] AddressAgent                          │            │
    │      graph lookup → fuzzy → trust scoring  │            │
    │                                            │            │
    │  [4] LLM Reasoning (llm_functions.py)      │            │
    │      agent_analyze() on failed checks      │            │
    │                                            │            │
    │  [5] FraudAgent                            │            │
    │      5 fraud signals → 0–100 fraud score   │            │
    │                                            │            │
    │  [6] VerdictAgent                          │            │
    │      PROCEED / REVIEW / REJECT + LLM notes │            │
    │                                            │            │
    │  [7] AuditAgent                            │            │
    │      in-memory AUD-XXXX log entry          │            │
    └────────────────────────────────────────────┘            │
           │                                                   │
           ▼                                                   │
┌─────────────────────────────────────────────────────────────┘
│                     PERSISTENCE LAYER
│
│  JSON Files  (backend/memory_data/)     SQLite  (audit.db)
│  ├── pattern_memory.json                ├── verifications
│  ├── proposals.json                     ├── check_results
│  ├── healing_log.json                   ├── pattern_observations
│  └── custom_rules.json                 ├── proposals
│                                        ├── healing_events
│  Atomic write: .tmp → os.replace()     └── test_sessions
│
│                    AI LAYER  (OpenRouter)
│  Model: anthropic/claude-haiku-4-5
│  Used by: SelfHealingAgent · AddressAgent · FraudAgent
│           VerdictAgent · LLM Reasoning · RuleEngine
│           RuleProposerAgent
└──────────────────────────────────────────────────────────────
```

---

## 7-Agent Pipeline Flow

```
Profile Input  { applicant_id, pan{}, aadhaar{}, bureau{}, addresses{}, doc_dates{} }
       │
       ▼
[Step 1]  ExtractionAgent
   normalize_name() on all name fields
   normalize_date() with typo correction on all DOBs
   Uppercase/strip PAN, gender, last4
       │
       ▼
[Step 2]  IdentityAgent  (7 checks, each in heal_check())
   ┌─────────────────────────────────────────────┐
   │ check_pan_format        → pass / hard_fail  │
   │ check_dob               → pass / hard_fail  │
   │ check_gender            → pass / soft / hard│
   │ check_aadhaar_last4     → pass / hard_fail  │
   │ check_name_fuzzy (P↔A)  → pass / soft / hard│
   │ check_name_fuzzy (B↔P)  → pass / soft / hard│
   │ check_father_name       → pass / soft / hard│
   └─────────────────────────────────────────────┘
   + custom rules exec'd from custom_rules.json
   → identity_verdict:  CLEAN / SOFT ISSUES — HUMAN REVIEW / HARD BLOCK
       │
       ▼
[Step 3]  AddressAgent
   graph_lookup() each address → knowledge graph (15+ roads)
   If both found: GRAPH_CONFIRMED_MATCH or GRAPH_CONFIRMED_DIFFERENT
   Fallback: fuzz.token_sort_ratio + pincode comparison
   Trust scoring: Aadhaar(90) > GST(80) > Bank(75) > PAN(45) > utility(35) > self(15)
   Recency multiplier applied based on doc year
   LLM analysis when hard conflicts detected
       │
       ▼
[Step 4]  LLM Reasoning
   agent_analyze() on all failed checks together
   Returns: agent_note, confidence (HIGH/MEDIUM/LOW),
            recommendation (PROCEED/REVIEW/REJECT), reasoning
       │
       ▼
[Step 5]  FraudAgent
   DOB hard mismatch (+40) · Multiple name fails (+25)
   Address+identity cluster (+30) · Pincode mismatch (+20)
   High soft fail count (+15)  →  fraud_score capped at 100
   LLM fraud narrative when score ≥ 30
       │
       ▼
[Step 6]  VerdictAgent
   REJECT if fraud_score ≥ 60 or HARD BLOCK identity
   REVIEW if fraud ≥ 30, SOFT ISSUES, or CONFLICTING addresses
   PROCEED otherwise
   LLM writes professional underwriter notes (3 sections)
       │
       ▼
[Step 7]  AuditAgent
   Creates AUD-XXXX entry in in-memory audit_store
   SQLite save_verification() called from main.py after pipeline
```

---

## Verification Checks

| # | Check | Severity on Fail | Logic Summary |
|---|---|---|---|
| 1 | PAN Format Validity | hard_fail | Regex `^[A-Z]{5}[0-9]{4}[A-Z]$` after normalize_pan() |
| 2 | Date of Birth (PAN vs Aadhaar) | hard_fail | normalize_date() — 25 format patterns + typo map + dateutil fallback |
| 3 | Gender Match | soft or hard_fail | GENDER_GRAPH maps "1"/"Male"/"मेल" → M/F/O canonical |
| 4 | Aadhaar Last-4 Consistency | hard_fail | extract_aadhaar_last4() handles masked formats (XXXX-XXXX-5678) |
| 5 | Name Match (PAN vs Aadhaar) | soft or hard_fail | Multi-layer fuzzy (6 layers — see below) |
| 6 | Name Match (Bureau vs PAN) | soft or hard_fail | Same multi-layer fuzzy |
| 7 | Father Name (PAN vs Aadhaar) | soft or hard_fail | Strip S/O, D/O, SHRI, LATE prefixes → fuzzy |

**Verdict**: Any `hard_fail` → HARD BLOCK. Any `soft_fail` → SOFT ISSUES — HUMAN REVIEW. All pass → CLEAN.

---

## Multi-Layer Fuzzy Name Matching

```
Input:  name_a = "P. Kumar"      name_b = "Prashant Kumar"
                │
                ▼
Layer 1:  normalize_name()
          UPPERCASE, strip punctuation, collapse spaces
          → "P KUMAR"  vs  "PRASHANT KUMAR"
                │
                ▼
Layer 2:  apply_transliteration()
          Lookup each token in TRANSLITERATION_GRAPH
          e.g. PRASHANTH→PRASHANT, MOHAMMED→MOHAMMAD
                │
                ▼
Layer 3:  is_initial_match()
          First token single char AND surnames match?
          → True  (P is initial of Prashant, Kumar==Kumar)
                │
                ▼
Layer 4:  fuzz.token_sort_ratio()
          raw_score   = token_sort_ratio(norm_a, norm_b)
          trans_score = token_sort_ratio(trans_a, trans_b)
          best_score  = max(raw_score, trans_score)
                │
                ▼
Layer 5:  Threshold adjustment
          Default: pass=85, soft=55
          initial_leniency + initial_match: adj_pass-=10, adj_soft-=15
          transliteration applied: adj_soft-=10
                │
                ▼
Layer 6:  Verdict
          initial_match + surnames_match  → soft_fail (LLM explains)
          best_score ≥ adj_pass           → pass
          best_score ≥ adj_soft           → soft_fail
          below both                      → hard_fail
```

---

## Self-Improving System

```
Every /orchestrate call
       │
       ▼
ObservationAgent.observe_verification()
   Records to pattern_memory.json:
   • date_formats: {"YYYY-MM-DD": 12, "DD/MM/YYYY": 4, ...}
   • name_patterns: {"INITIAL_FIRST_NAME": 3, "FULL_NAME": 9}
   • soft_fail_patterns, hard_fail_patterns
   • typos detected in input fields
       │
       ▼
RuleProposerAgent.analyze_and_propose()
   PROPOSAL_THRESHOLD = 3 occurrences
       │
   Proposal types:
   ├── DATE_FORMAT_HANDLER      (new date format seen ≥3×)
   ├── NAME_THRESHOLD_ADJUSTMENT (initials pattern seen ≥3×)
   ├── TYPO_CORRECTION_RULE     (typo seen ≥3×)
   └── SYSTEMATIC_HARD_FAIL     (check failing ≥6× — 2× threshold)
       │
       ▼
Saved to proposals.json + SQLite proposals table
       │
       ▼
Human review via Self-Improving tab in UI
   Approve → auto-generate Python improvement code via LLM
   Reject  → moved to rejected list
```

---

## Self-Healing System

```
In orchestrator, EVERY check is wrapped:

  heal_check("PAN Format Validity", check_pan_format, profile, pan_number)
                   │
          ┌────────┴────────────────────┐
          │ try:                        │ except Exception:
          │   return check_func(*args)  │   1. MD5 error signature
          │                            │   2. LLM analyzes → returns:
          │                            │      root_cause, error_category
          │                            │      proposed_fix, severity
          │                            │      auto_fixable, fix_code
          │                            │   3. Log to healing_log.json
          │                            │      + SQLite healing_events
          │                            │   4. Return safe soft_fail:
          │                            │      "[Self-Healed] ..."
          └────────────────────────────┘
                   │
                   ▼
        Pipeline CONTINUES — never crashes
        HealingPanel UI shows all events
```

---

## Rule Engine Flow

```
User types: "PAN number last 4 chars before final letter must be numeric"
       │
       ▼
POST /rules/create → LLM generates Python function:
   def custom_check_pan_numeric_chars(profile):
       pan = profile.get("pan", {}).get("number", "")
       ...
       return {"check": "...", "input_a": "...",
               "input_b": "...", "result": "pass"/"soft_fail"/"hard_fail",
               "reason": "..."}
       │
       ▼
Preview in RuleEngine.jsx → "Add to Engine"
       │
       ▼
POST /rules/save → saved to custom_rules.json
       │
       ▼
Every future /orchestrate or /verify-live call:
   run_custom_rules(checks, profile)
   Smart merge: rule keyword match → upgrades existing check result
   No match → appended as new check row
```

---

## UI Tabs

| Tab | Component | Purpose |
|---|---|---|
| Verification | OrchestrationPanel, VerdictBanner, LedgerTable | Pipeline steps, verdict, confidence score, agent reasoning, check results |
| Address | AddressPanel | Trust scores by doc source, graph lookups, conflicts, canonical address |
| Fraud | FraudPanel | Fraud score 0–100, 5 fraud signals, risk level, LLM narrative |
| Underwriter | UnderwriterNotes | Final PROCEED/REVIEW/REJECT, LLM underwriter notes (3 sections) |
| Rules | RuleEngine | Write plain English rules, preview generated code, add/remove |
| Live Tester | LiveTestPanel | Configurable thresholds, manual input, named test sessions |
| Audit Trail | AuditTrail | In-memory session audit log |
| Self-Improving | SelfImprovingAgent | Pattern memory stats, proposal list, approve/reject |
| Self-Healing | HealingPanel | Healing events, known error patterns |
| Memory & History | MemoryDashboard | SQLite stats, verification history, test sessions by category |

---

## API Endpoints

### Verification
| Method | Endpoint | Description |
|---|---|---|
| POST | `/verify` | Simple 7-check verification (no orchestrator pipeline) |
| POST | `/orchestrate` | Full 7-agent pipeline — runs all agents |
| POST | `/verify-live` | Live test with configurable thresholds; saves named test sessions |
| POST | `/explain` | AI explanation of a specific failed check |

### Rule Engine
| Method | Endpoint | Description |
|---|---|---|
| POST | `/rules/create` | LLM generates Python function from plain English |
| POST | `/rules/save` | Persist rule to custom_rules.json |
| GET | `/rules/list` | List all active custom rules |
| DELETE | `/rules/{func_name}` | Remove a rule |

### Self-Improving Agent
| Method | Endpoint | Description |
|---|---|---|
| GET | `/self-improve/memory` | Full pattern memory dict |
| GET | `/self-improve/proposals` | All proposals (pending/approved/rejected) |
| GET | `/self-improve/stats` | Summary: total_runs, patterns, proposals counts |
| POST | `/self-improve/proposals/{id}/approve` | Approve — optionally triggers code generation |
| POST | `/self-improve/proposals/{id}/reject` | Reject proposal |

### Self-Healing
| Method | Endpoint | Description |
|---|---|---|
| GET | `/healing/log` | Healing events and known error patterns |

### Audit & Metrics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/audit` | In-memory audit log (session only) |
| GET | `/evaluation/metrics` | Precision/recall/F1 computed against 3 mock files |

### Memory & History (Persistent)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/memory/stats` | JSON file sizes + SQLite table row counts |
| POST | `/memory/reset` | Reset a JSON memory file by key |
| GET | `/history/verifications` | Last 50 verifications from SQLite |
| GET | `/history/verifications/{id}/checks` | All check results for one verification |
| GET | `/history/test-sessions` | Last 100 test sessions |
| GET | `/history/patterns` | Pattern memory (same data as /self-improve/memory) |

### Testing
| Method | Endpoint | Description |
|---|---|---|
| POST | `/test/run-all-judge-cases` | Run 10 named judge test cases, save to SQLite, return accuracy |

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend API | FastAPI + Uvicorn | Async REST API |
| LLM Client | OpenAI Python SDK | Used with OpenRouter base_url |
| AI Model | anthropic/claude-haiku-4-5 via OpenRouter | Reasoning, healing, rule gen, notes |
| Fuzzy Matching | rapidfuzz | `token_sort_ratio` for name similarity |
| Date Parsing | python-dateutil | Fallback parser for exotic date formats |
| Env Vars | python-dotenv | Loads `OPENROUTER_API_KEY` from .env |
| Persistence | sqlite3 (stdlib) + json (stdlib) | Audit DB + agent memory |
| Frontend | React 18 + Vite 5 | SPA |
| Styling | Tailwind CSS v3 | Utility-first dark theme |

---

## Folder Structure

```
hackathon/
├── README.md
├── start.sh                           # One-command startup (Linux/Mac)
├── backend/
│   ├── main.py                        # FastAPI app — all 23 routes
│   ├── checks.py                      # 7 check functions + normalization utils
│   ├── llm_functions.py               # OpenRouter client + AI call functions
│   ├── requirements.txt
│   ├── .env                           # OPENROUTER_API_KEY (git-ignored)
│   ├── agents/
│   │   ├── orchestrator.py            # 7-step pipeline runner
│   │   ├── extraction_agent.py        # Data normalization agent
│   │   ├── address_agent.py           # Address analysis + trust scoring
│   │   ├── fraud_agent.py             # 5-signal fraud scorer
│   │   ├── verdict_agent.py           # Final PROCEED/REVIEW/REJECT + notes
│   │   ├── audit_agent.py             # In-memory audit log
│   │   ├── observation_agent.py       # Pattern memory updater
│   │   ├── rule_proposer_agent.py     # Proposal generator from patterns
│   │   └── self_healing_agent.py      # Exception wrapper + LLM diagnosis
│   ├── knowledge/
│   │   └── address_graph.py           # 15+ Indian road/alias knowledge graph
│   ├── persistence/
│   │   ├── memory_store.py            # Atomic JSON load/save/append/reset
│   │   └── audit_db.py                # SQLite schema + all CRUD functions
│   ├── evaluation/
│   │   └── precision_recall.py        # Precision/recall vs ground truth labels
│   ├── test_data/
│   │   └── judge_test_cases.py        # 10 named test cases (10/10 pass)
│   └── mock_files/
│       ├── file1_clean.json            # FL-001: perfect match — CLEAN
│       ├── file2_soft.json             # FL-002: name abbreviations — SOFT ISSUES
│       └── file3_hard.json             # FL-003: DOB mismatch — HARD BLOCK
├── frontend/
│   ├── index.html
│   ├── vite.config.js                 # /api proxy → localhost:8000
│   ├── tailwind.config.js
│   ├── package.json
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx                    # Main app — tabs, file selector, state
│   │   ├── index.css                  # Dark body background (#030712)
│   │   └── components/
│   │       ├── VerdictBanner.jsx      # CLEAN / SOFT ISSUES / HARD BLOCK
│   │       ├── LedgerTable.jsx        # Check results table with Ask AI
│   │       ├── AskAIDrawer.jsx        # Sliding AI explanation panel
│   │       ├── OrchestrationPanel.jsx # 7-step pipeline progress display
│   │       ├── AddressPanel.jsx       # Address analysis + graph results
│   │       ├── FraudPanel.jsx         # Fraud score + signals
│   │       ├── UnderwriterNotes.jsx   # Final verdict + LLM notes
│   │       ├── RuleEngine.jsx         # Custom rule management UI
│   │       ├── LiveTestPanel.jsx      # Configurable live testing
│   │       ├── SelfImprovingAgent.jsx # Pattern memory + proposals UI
│   │       ├── HealingPanel.jsx       # Healing events log
│   │       ├── MemoryDashboard.jsx    # SQLite + JSON memory stats
│   │       └── AuditTrail.jsx         # Audit log viewer
│   └── public/
│       └── mock_files/                # Static JSON for file selector
└── docs/                              # Full system documentation
```

---

## Quick Start

```bash
# Set API key
echo "OPENROUTER_API_KEY=your_key_here" > backend/.env

# Linux/Mac — one command
chmod +x start.sh && ./start.sh

# Windows — two terminals
# Terminal 1:
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000
# Terminal 2:
cd frontend && npm install && npm run dev
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs

---

## Demo Flow

**Option A — Mock Files:** Click FL-001, FL-002, FL-003 in order. See CLEAN → SOFT ISSUES → HARD BLOCK.

**Option B — Judge Demo:** Click **Run Judge Demo** in the header. Runs 10 test cases covering DOB typos, transliteration, masked Aadhaar, Mohammed variants, father name prefixes. Results save to Memory tab.

**Option C — Live Tester:** Go to Live Tester tab. Enter any PAN/Aadhaar/Bureau data with custom thresholds. Name the test session to save it.

**Option D — Custom Rules:** Go to Rules tab. Type a rule in plain English. Preview the generated Python. Add to engine. Run any mock file to see it active.

---

## Persistence

All memory survives server restarts:

| File | Contents |
|---|---|
| memory_data/pattern_memory.json | Date formats seen, name patterns, typos observed |
| memory_data/proposals.json | Pending/approved/rejected proposals |
| memory_data/healing_log.json | Error events and known patterns |
| memory_data/custom_rules.json | Active custom rule functions |
| memory_data/audit.db (SQLite) | Full verification + check + test session history |

---

## Judge Test Suite (10/10 Pass)

| Case | Scenario | Expected Verdict |
|---|---|---|
| TC-01 | Perfect clean match | CLEAN |
| TC-02 | Initial name abbreviation (P. Kumar) | SOFT ISSUES |
| TC-03 | DOB typo: "arpil" → "april" | CLEAN |
| TC-04 | Transliteration: Prashanth → Prashant | CLEAN |
| TC-05 | Hard DOB mismatch | HARD BLOCK |
| TC-06 | Gender normalization: Male vs 1 | CLEAN |
| TC-07 | Masked Aadhaar: XXXX-XXXX-5678 | CLEAN |
| TC-08 | Mohammed variant: Muhammed → Mohammad | CLEAN |
| TC-09 | Father prefix stripped: S/O Ramesh | CLEAN |
| TC-10 | Completely different identity | HARD BLOCK |

---

## Current Limitations

1. Audit agent (`audit_agent.py`) uses in-memory storage — restarts lose session log (SQLite has durable copy)
2. Address knowledge graph covers 15 roads manually — not auto-updated
3. No document OCR — profile must be pre-formatted JSON
4. No API authentication layer
5. Custom rule execution uses Python `exec()` without sandboxing
6. Single LLM model — no fallback chain

---

## Documentation

- [docs/architecture/system_architecture.md](docs/architecture/system_architecture.md)
- [docs/concepts/how_it_works.md](docs/concepts/how_it_works.md)
- [docs/api/api_reference.md](docs/api/api_reference.md)
- [docs/ui/ui_walkthrough.md](docs/ui/ui_walkthrough.md)
- [docs/flows/verification_flow.md](docs/flows/verification_flow.md)
- [docs/flows/agent_orchestration.md](docs/flows/agent_orchestration.md)
- [docs/flows/self_improving_loop.md](docs/flows/self_improving_loop.md)
- [docs/flows/self_healing_loop.md](docs/flows/self_healing_loop.md)
- [docs/flows/rule_engine_flow.md](docs/flows/rule_engine_flow.md)
- [docs/flows/persistence_flow.md](docs/flows/persistence_flow.md)
- [SYSTEM_CONCEPTS_AND_FLOW.md](SYSTEM_CONCEPTS_AND_FLOW.md)
