# UI Walkthrough — VerifyIQ Frontend

## Overview

The frontend is a single React 18 application at `http://localhost:5173`. The entire app lives in `App.jsx` which manages global state, with 13 child components rendering specific sections.

---

## Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER  (bg-gray-900)                                      │
│  VerifyIQ: Identity Cross-Verification Agent    [Run Judge] │
│  FlexiLoans · Underwriting Desk                             │
├─────────────────────────────────────────────────────────────┤
│  TAB BAR  (bg-gray-900)                                     │
│  Verification | Address | Fraud | Underwriter | Rules |     │
│  Live Tester | Audit Trail | Self-Improving* | Self-Healing*│
│  | Memory & History                                         │
│  (* = animated green/red dot when data available)           │
├─────────────────────────────────────────────────────────────┤
│  FILE SELECTOR  (visible on Verification/Address/Fraud tabs)│
│  [FL-001 — Clean]  [FL-002 — Soft Mismatch]                 │
│  [FL-003 — Hard Mismatch]                                   │
├─────────────────────────────────────────────────────────────┤
│  MAIN CONTENT  (max-w-6xl mx-auto)                          │
│  Changes based on active tab                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Component-by-Component Reference

### App.jsx — Root Container

**Purpose:** Main application shell. Owns all global state.

**State:**
| State | Type | Purpose |
|---|---|---|
| `selectedFile` | string | Currently selected mock file ID ("FL-001") |
| `profile` | object | Raw JSON loaded from mock file |
| `result` | object | Full response from POST /orchestrate |
| `askAICheck` | object | Check passed to AskAIDrawer when opened |
| `loading` | boolean | True while orchestrate is running |
| `activeTab` | string | Current tab ID |
| `pendingProposals` | number | Count from /self-improve/stats, polled every 10s |
| `healedErrors` | number | Count from /healing/log, polled every 10s |
| `metrics` | object | Precision/recall data, loaded on demand |
| `judgeRunning` | boolean | True while judge demo is running |
| `judgeToast` | object | Toast notification {type, msg} |

**Key interactions:**
- Clicking a file button: fetches profile JSON + calls `/api/orchestrate` → sets `result`
- Clicking "Run Judge Demo": calls `/api/test/run-all-judge-cases` → shows toast → switches to Memory tab
- Tab bar: just sets `activeTab` state

**Live polling:** Two `setInterval` calls poll every 10 seconds:
1. `/api/self-improve/stats` → updates `pendingProposals` (drives green dot on Self-Improving tab)
2. `/api/healing/log` → updates `healedErrors` (drives red dot on Self-Healing tab)

---

### Verification Tab (rendered in App.jsx)

**Components used:** `OrchestrationPanel`, `VerdictBanner`, confidence score bar (inline), agent reasoning panel (inline), `LedgerTable`, summary stats bar (inline)

**What it shows:**
1. **OrchestrationPanel** — 7 pipeline steps with status and summary
2. **VerdictBanner** — CLEAN (green) / SOFT ISSUES — HUMAN REVIEW (yellow) / HARD BLOCK (red)
3. **Confidence Score** — percentage with animated progress bar
4. **Agent Reasoning** — agent_note, confidence label, recommendation badge, reasoning text
5. **LedgerTable** — full 7-check results table
6. **Summary stats** — total checks / passed / failed breakdown
7. **System Accuracy Metrics** — collapsible panel that loads precision/recall on demand

---

### OrchestrationPanel.jsx

**Props:** `steps` — array of pipeline step objects from result.pipeline_steps

**Purpose:** Shows the 7-step pipeline execution as a numbered list with status and summary text.

Each step shows:
- Step number (circle badge)
- Step name
- Status (running → complete)
- Summary line (e.g. "Verdict: CLEAN | 0 hard, 0 soft fails")

---

### VerdictBanner.jsx

**Props:** `verdict` — string ("CLEAN", "SOFT ISSUES — HUMAN REVIEW", "HARD BLOCK")

**Purpose:** Large colored banner showing the identity verdict.

Colors:
- CLEAN → green banner
- SOFT ISSUES — HUMAN REVIEW → yellow banner
- HARD BLOCK → red banner

---

### LedgerTable.jsx

**Props:** `checks` — array of check result objects; `onAskAI` — callback to open drawer

**Purpose:** Tabular display of all 7 (or more with custom rules) check results.

Each row shows:
- Left color border (green=pass, yellow=soft_fail, red=hard_fail)
- Check name
- Input A (what was compared)
- Input B (what it was compared against)
- Result badge (PASS / SOFT FAIL / HARD FAIL)
- Reason text
- Fuzzy score (for name checks)
- "Ask AI" button (appears on non-pass rows)

---

### AskAIDrawer.jsx

**Props:** `check` — the check object, `profile` — full profile, `onClose` — callback

**Purpose:** Sliding panel from the right side of screen. Calls POST /explain for the selected check and displays the AI explanation.

Shows:
- Check name and result
- Input A and B
- Loading spinner while fetching
- AI explanation text
- Close button (x)

---

### Address Tab → AddressPanel.jsx

**Props:** `addressResult` — from result.address_result

**Purpose:** Full address analysis breakdown.

Shows:
- Address verdict (CONSISTENT / LIKELY_SAME / CONFLICTING / NO_ADDRESS_DATA)
- Canonical address (highest-trust source)
- Trust scores bar chart for each document source
- Normalized addresses for each source
- Conflicts list (if any)
- Graph lookup results for each address
- Pincode groups
- Agent analysis text (from LLM if conflicts detected)

---

### Fraud Tab → FraudPanel.jsx

**Props:** `fraudResult` — from result.fraud_result

**Purpose:** Fraud risk assessment display.

Shows:
- Fraud score progress bar (0–100) with color: green (LOW), yellow (MEDIUM), red (HIGH)
- Risk level badge
- Each detected fraud signal with weight and detail
- Fraud narrative text (from LLM if score ≥ 30)

RISK_CONFIG mapping:
- LOW: green colors
- MEDIUM: yellow colors
- HIGH: red colors

---

### Underwriter Tab → UnderwriterNotes.jsx

**Props:** `verdictResult` — from result.final_verdict, `applicantId`

**Purpose:** Final underwriting decision display.

Shows:
- Final verdict (PROCEED / REVIEW / REJECT) with color-coded header
- Decision factors (identity verdict, address verdict, fraud score, confidence)
- LLM underwriter notes (formatted with 3 sections: Summary, Key Findings, Recommended Action)

Verdict colors:
- PROCEED → green header
- REVIEW → yellow header
- REJECT → red header

---

### Rules Tab → RuleEngine.jsx

**Purpose:** Custom rule management interface.

**State:** `ruleText`, `generating`, `generated`, `saving`, `activeRules`

**Flow:**
1. Text area for rule description
2. Example rule chips (click to fill text area)
3. "Generate Rule" button → POST /rules/create → shows code preview
4. Code preview (syntax-highlighted monospace)
5. "Add to Engine" button → POST /rules/save → rule appears in active list
6. "Regenerate" button → re-runs generation
7. Active rules list with ACTIVE badge and Remove button per rule

**API calls:**
- On mount: GET /rules/list
- Generate: POST /rules/create
- Add: POST /rules/save
- Remove: DELETE /rules/{func_name}

---

### Live Tester Tab → LiveTestPanel.jsx

**Purpose:** Manual verification tester with configurable thresholds.

**State:** Input fields for PAN (5 fields), Aadhaar (5 fields), Bureau (4 fields), threshold sliders, test name, loading, result

**Features:**
- 14 input fields organized in 3 sections (PAN / Aadhaar / Bureau)
- Threshold sliders: Pass threshold (50–100), Soft threshold (30–80)
- Initial leniency toggle
- Test case name field + category selector (for saving to history)
- "Verify" button → POST /verify-live
- Result display with verdict, confidence, all check results
- Normalization preview (shows what dates/names were parsed to)

---

### Audit Trail Tab → AuditTrail.jsx

**Purpose:** Shows in-memory session audit log.

**API:** GET /audit on mount

**Shows:**
- Each AUD-XXXX entry as a card
- Applicant ID, timestamp, final verdict, fraud score, confidence, identity/address verdicts
- Counts: checks run, hard fails, soft fails, rules applied

Note: This is session-only (in-memory). SQLite verifications are in Memory & History tab.

---

### Self-Improving Tab → SelfImprovingAgent.jsx

**Purpose:** Pattern memory browser and proposal management.

**Sections:**
1. **Stats bar** — total runs, patterns discovered, pending/approved counts
2. **Pattern Memory** — date formats seen (bar chart), name patterns, top typos
3. **Pending Proposals** — each proposal with type badge, observation, action, priority
   - Approve button → POST /self-improve/proposals/{id}/approve
   - Reject button → POST /self-improve/proposals/{id}/reject
4. **Approved Proposals** — with optionally generated code
5. **Rejected Proposals** — archive

**Green dot on tab:** Appears when pendingProposals > 0 (live-polled)

---

### Self-Healing Tab → HealingPanel.jsx

**Purpose:** Shows all healing events and known error patterns.

**API:** GET /healing/log on mount

**Shows:**
- If no events: "System is healthy — no healing events" (green box)
- Total healed count, unique patterns
- Each healing event: check name, error type, root cause, proposed fix, severity, auto_fixable
- Known error patterns with occurrence count

**Red dot on tab:** Appears when healedErrors > 0 (live-polled)

---

### Memory & History Tab → MemoryDashboard.jsx

**Purpose:** Full persistence layer dashboard.

**API calls on mount (parallel):**
- GET /memory/stats
- GET /history/verifications?limit=20
- GET /history/test-sessions?limit=50
- GET /history/patterns

**Sections (all collapsible):**
1. **Storage Summary** — 4 stat cards (total verifications, test sessions, healing events, proposals) + file sizes
2. **Recent Verifications** — table of last 20 (ID, applicant, verdict, confidence, timestamp)
3. **Test Sessions by Category** — grouped by category (judge_demo, manual, etc.) with pass counts
4. **Pattern Memory** — date formats and name patterns as bar charts
5. **Persistent File Details** — each JSON file size + Reset button

---

## Color Theme Reference

| Element | Tailwind Classes |
|---|---|
| Page background | `bg-gray-950` |
| Card/panel background | `bg-gray-900` |
| Table header / input background | `bg-gray-800` |
| Primary text | `text-gray-100` |
| Secondary text | `text-gray-300` |
| Muted text | `text-gray-400` / `text-gray-500` |
| Active tab indicator | `border-indigo-400 text-indigo-400` |
| Pass badge | `bg-green-900 text-green-400` |
| Soft fail badge | `bg-yellow-900 text-yellow-400` |
| Hard fail badge | `bg-red-900 text-red-400` |
| Agent reasoning panel | `bg-indigo-950 border-indigo-900` |
| Healing healthy state | `bg-green-950 border-green-900` |

---

## State Flow: From Click to Render

```
User clicks "FL-001 — Clean"
         │
         ▼
handleSelectFile(fileConfig) in App.jsx
   setSelectedFile("FL-001")
   setResult(null)           ← clears old result
   setLoading(true)          ← shows "Running agentic pipeline..."
   setActiveTab("verification")
         │
         ▼
fetch("/mock_files/file1_clean.json")
   → setProfile(data)        ← stores raw profile
         │
         ▼
fetch("/api/orchestrate", {method:"POST", body: JSON.stringify(data)})
   → wait for response (~1-3 seconds)
         │
         ▼
setResult(responseJson)       ← triggers re-render
setLoading(false)             ← removes loading indicator
         │
         ▼
React renders all tab components with new data:
   Verification tab: result.checks, result.identity_verdict,
                     result.confidence_score, result.reasoning_result,
                     result.pipeline_steps
   Address tab:      result.address_result
   Fraud tab:        result.fraud_result
   Underwriter tab:  result.final_verdict
```
