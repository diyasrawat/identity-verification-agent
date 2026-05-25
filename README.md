# VerifyIQ: Identity Cross-Verification Agent

An AI-powered identity verification system that cross-checks PAN, Aadhaar, and Bureau data for Indian lending applications. It runs 7 deterministic checks in under 100ms, then an AI agent performs a second-pass reasoning step — keeping costs near zero while surfacing intelligent, structured verdicts for underwriters.

## How to Run

```bash
export OPENROUTER_API_KEY=your_key_here
bash start.sh
```

Then open **http://localhost:5173** in your browser.

## Mock Files

| File | Applicant | Scenario |
|------|-----------|----------|
| `file1_clean.json` | FL-001 | All 7 checks pass — PAN, Aadhaar, Bureau perfectly consistent |
| `file2_soft.json` | FL-002 | Soft name mismatch — PAN has "P. Kumar" vs Aadhaar "Prashant Kumar" (abbreviation pattern, likely same person) |
| `file3_hard.json` | FL-003 | Hard DOB mismatch — PAN says 1990-04-12, Aadhaar + Bureau say 1985-07-23 (hard block, loan cannot proceed) |

## Architecture

**Hybrid deterministic + LLM design:**

- **7 checks run as pure Python** — regex, exact match, and rapidfuzz fuzzy matching. Zero LLM calls, completes in <100ms regardless of load.
- **Input normalization** — all names uppercased and punctuation-stripped before fuzzy comparison; all dates parsed to ISO format via `python-dateutil` before exact comparison.
- **LLM fires in three cases only:**
  1. A name check returns `soft_fail` (score 70–84) → AI writes a one-sentence explanation
  2. Agent second-pass reasoning → analyzes all failures together, returns PROCEED / REVIEW / REJECT
  3. Analyst clicks "Ask AI" on any failed check → AI gives a 2–3 sentence underwriting note
- **Model:** `anthropic/claude-haiku-4-5` via OpenRouter API
- **Cost per file:** <$0.001 (max 3 LLM calls × ~150 tokens)
- **At scale:** 50,000 files/day ≈ $50/day

**Verdict logic (deterministic, no LLM):**
- Any `hard_fail` → `HARD BLOCK`
- Any `soft_fail` → `SOFT ISSUES — HUMAN REVIEW`
- All pass → `CLEAN`

## Agentic Capabilities

After deterministic checks complete, an AI agent performs a second-pass reasoning step — analyzing all failures together to detect patterns (e.g. multiple soft fails suggesting data entry error vs one hard fail suggesting fraud). Returns a structured verdict: **PROCEED / REVIEW / REJECT** with a confidence level (HIGH / MEDIUM / LOW) and a one-sentence reasoning note displayed directly in the UI.

This agentic loop runs on every verification call and costs ~1 LLM call (~200 tokens) only when failures are present.

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + Python |
| Fuzzy matching | rapidfuzz |
| Date normalization | python-dateutil |
| LLM | OpenRouter API (`anthropic/claude-haiku-4-5`) |
| Frontend | React 18 + Vite |
| Styling | Tailwind CSS v3 |
