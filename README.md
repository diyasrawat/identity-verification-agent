# VerifyIQ: Identity Cross-Verification Agent

An AI-powered identity verification system for Indian lending that cross-checks PAN, Aadhaar, and Bureau data. It runs 7 deterministic checks in under 100ms, then an AI agent performs a second-pass reasoning step — keeping costs near zero while surfacing intelligent, structured verdicts for underwriters. Includes a live rule engine where users write rules in plain English and the agent converts them to executable Python checks in real time.

<img width="1919" height="921" alt="image" src="https://github.com/user-attachments/assets/f48d1890-c6b4-42c6-8bfb-ed0168a743ec" />
<img width="1914" height="938" alt="image" src="https://github.com/user-attachments/assets/a6e9cbc7-b413-4e0d-9842-80072df34fa5" />
[https://drive.google.com/file/d/1ZfmXZlZgxqqYi-0prhApykUZYuLplzM1/view?usp=drive_link](https://drive.google.com/file/d/1ZfmXZlZgxqqYi-0prhApykUZYuLplzM1/view?usp=drive_link)

## How to Run

```bash
export OPENROUTER_API_KEY=your_key_here
bash start.sh
```

Or manually in two terminals:

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## What It Does

VerifyIQ verifies that a loan applicant's identity documents are consistent with each other. It checks:

- Does the name on PAN match the name on Aadhaar? (fuzzy — handles abbreviations like "P. Kumar" vs "Prashant Kumar")
- Does the date of birth match across all 3 sources?
- Does the Aadhaar last-4 on the bureau record match the actual Aadhaar?
- Is the PAN format valid?
- Do gender and father name match?

After all checks, an AI agent looks at the failures together and gives a single recommendation: **PROCEED**, **REVIEW**, or **REJECT** — with a confidence score (0–100%) and a reasoning note.

---

## Mock Demo Files

| File | Applicant | Scenario |
|------|-----------|----------|
| `file1_clean.json` | FL-001 | All 7 checks pass — PAN, Aadhaar, Bureau perfectly consistent → CLEAN |
| `file2_soft.json` | FL-002 | Soft name mismatch — PAN has "P. Kumar" vs Aadhaar "Prashant Kumar" (initial abbreviation, detected and explained by AI) → SOFT ISSUES |
| `file3_hard.json` | FL-003 | Hard DOB mismatch — PAN says 1990-04-12, Aadhaar + Bureau say 1985-07-23 → HARD BLOCK |

---

## Architecture

### Hybrid Deterministic + LLM Design

```
Applicant Profile JSON
        │
        ▼
┌─────────────────────────────────────────┐
│     7 Deterministic Checks (<100ms)     │
│  PAN format · DOB · Gender · Aadhaar   │
│  last4 · Name fuzzy × 2 · Father name  │
└────────────────┬────────────────────────┘
                 │
        soft_fail detected?
        ┌────────┴────────┐
       YES               NO
        │                 │
  LLM explains       skip LLM
  in 1 sentence
                 │
                 ▼
┌─────────────────────────────────────────┐
│   Custom Rule Engine (0–N rules)        │
│   Plain English → Python, runs live     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   Agent Second-Pass Reasoning           │
│   Analyzes ALL failures together        │
│   Returns: PROCEED / REVIEW / REJECT    │
│   + Confidence: HIGH / MEDIUM / LOW     │
└─────────────────────────────────────────┘
```

### 7 Deterministic Checks

| # | Check | Method | Failure Type |
|---|-------|--------|-------------|
| 1 | PAN Format | Regex `[A-Z]{5}[0-9]{4}[A-Z]` | Hard |
| 2 | Date of Birth (PAN vs Aadhaar) | Exact match after normalization | Hard |
| 3 | Gender (PAN vs Aadhaar) | Exact match | Hard |
| 4 | Aadhaar Last 4 (Bureau vs Aadhaar) | Exact match | Hard |
| 5 | Name (PAN vs Aadhaar) | Fuzzy + initial detection | Soft/Hard |
| 6 | Name (Bureau vs PAN) | Fuzzy + initial detection | Soft/Hard |
| 7 | Father Name (PAN vs Aadhaar) | Fuzzy + initial detection | Soft/Hard |

### Fuzzy Name Matching

- Score ≥ 85 → **Pass**
- Score 55–84 → **Soft Fail** (LLM explains)
- Score < 55 → **Hard Fail**
- Initial pattern detected (e.g. "P. Kumar" vs "Prashant Kumar") → forced **Soft Fail** regardless of score

### DOB Normalization

Handles 30+ date formats including `"2004 arpil 6th"`, `"12/04/1990"`, `"April 12, 1990"`, `"12th Apr 90"` — all normalized to `YYYY-MM-DD` before comparison. Common typos in month names are auto-corrected.

### Confidence Score

After all checks, a weighted score (0–100%) is computed:
- `pass` = 100 pts, `soft_fail` = 40 pts, `hard_fail` = 0 pts
- Critical checks (DOB, PAN Format, Aadhaar Last 4) weighted **2×**
- Score ≥ 85 → HIGH CONFIDENCE · 55–84 → MEDIUM · < 55 → LOW

---

## Agentic Capabilities

### 1. Soft Fail Explainer
When a name check scores 55–84, the AI writes a one-sentence plain-English explanation: *"P. Kumar and Prashant Kumar likely refer to the same person as the first name appears to be an initial abbreviation of Prashant."*

### 2. Second-Pass Agent Reasoning
After all checks complete, the AI agent analyzes failures **together** (not in isolation) to detect patterns:
- Multiple soft fails → likely data entry error → REVIEW
- Hard DOB mismatch alone → possible fraud or wrong document → REJECT
- All passes → PROCEED

Returns structured JSON: `agent_note`, `confidence` (HIGH/MEDIUM/LOW), `recommendation` (PROCEED/REVIEW/REJECT), `reasoning`.

### 3. Ask AI (On-Demand)
Any failed check has an "Ask AI" button that opens a drawer. The underwriter gets a 2–3 sentence assessment: what the mismatch means, how serious it is, and what to do next.

### 4. Custom Rule Engine (Plain English → Live Check)
Underwriters or compliance teams write rules in plain English:

> *"Bureau linked PAN must exactly match the submitted PAN number"*

The agent converts this to a Python function via code generation, previews it, and adds it to the live engine. Custom rules run on every verification from that point — on all 3 mock files and the Live Tester. Rules can be removed at any time. Smart merge logic: if a custom rule relates to an existing check (e.g. a PAN rule), it upgrades that check's result rather than creating a duplicate row.

### 5. Live Format Tester
A full 14-field input panel (PAN × 5, Aadhaar × 5, Bureau × 4) where judges can type any name or date format and see the full verification run in real time — including normalization preview showing exactly what the engine parsed.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/verify` | Run full 7-check verification on a mock profile |
| `POST` | `/verify-live` | Run all checks on manually entered field values |
| `POST` | `/explain` | Ask AI about a specific failed check |
| `POST` | `/rules/create` | Generate Python check from plain English rule |
| `POST` | `/rules/save` | Save a generated rule to the live engine |
| `GET` | `/rules/list` | List all active custom rules |
| `DELETE` | `/rules/{func_name}` | Remove a custom rule |

---

## Cost & Scale

| Metric | Value |
|--------|-------|
| Cost per clean file | $0 (no LLM calls) |
| Cost per soft-fail file | <$0.0003 (1–2 LLM calls × ~150 tokens) |
| Cost per file with agent reasoning | <$0.001 (max 3 LLM calls) |
| At 50,000 files/day | ~$50/day |
| Latency (deterministic checks) | <100ms |
| Model | `anthropic/claude-haiku-4-5` via OpenRouter |

---

## Tech Stack

| Layer | Tech | Purpose |
|-------|------|---------|
| Backend API | FastAPI + Python 3.11 | REST endpoints, async handlers |
| Fuzzy matching | rapidfuzz | Name similarity scoring |
| Date normalization | python-dateutil | Parses 30+ date formats |
| LLM / Agent | OpenRouter API → Claude Haiku 4.5 | Explanations, reasoning, code generation |
| Env management | python-dotenv | Loads `OPENROUTER_API_KEY` from `.env` |
| Frontend | React 18 + Vite 5 | SPA UI |
| Styling | Tailwind CSS v3 | Utility-first CSS |
| HTTP proxy | Vite dev proxy | `/api/*` → `localhost:8000` |

---

## Project Structure

```
hackathon/
├── backend/
│   ├── main.py              # FastAPI app, all endpoints, rule engine logic
│   ├── checks.py            # 7 deterministic check functions + normalization
│   ├── llm_functions.py     # All LLM calls (OpenRouter SDK)
│   ├── requirements.txt
│   └── mock_files/          # 3 demo applicant profiles
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main app shell, file selector, results layout
│   │   └── components/
│   │       ├── VerdictBanner.jsx   # CLEAN / SOFT / HARD BLOCK banner
│   │       ├── LedgerTable.jsx     # Full check results table
│   │       ├── AskAIDrawer.jsx     # Sliding AI explanation panel
│   │       ├── RuleEngine.jsx      # Plain English → Python rule manager
│   │       └── LiveTestPanel.jsx   # 14-field live verification tester
│   └── public/mock_files/   # Static JSON served to frontend
└── start.sh                 # One-command startup script
```
