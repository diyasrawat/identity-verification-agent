# VerifyIQ: Identity Cross-Verification Agent

An AI-powered identity verification system that cross-checks PAN, Aadhaar, and Bureau data for Indian lending applications. It runs 7 deterministic checks in under 100ms, then calls Claude Haiku only when a soft mismatch is detected — keeping AI costs near zero while still surfacing intelligent explanations.

## How to Run

```bash
export ANTHROPIC_API_KEY=your_key_here
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
- **LLM fires in two cases only:**
  1. A name check returns `soft_fail` (score 70–84) → Claude Haiku writes a one-sentence explanation
  2. Analyst clicks "Ask AI" on any failed check → Claude Haiku gives a 2–3 sentence underwriting note
- **Model:** `claude-haiku-4-5-20251001`
- **Cost per file:** <$0.001 (max 3 LLM calls × ~150 tokens)
- **At scale:** 50,000 files/day ≈ $50/day

**Verdict logic (deterministic, no LLM):**
- Any `hard_fail` → `HARD BLOCK`
- Any `soft_fail` → `SOFT ISSUES — HUMAN REVIEW`
- All pass → `CLEAN`

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + Python |
| Fuzzy matching | rapidfuzz |
| LLM | Anthropic Python SDK (Claude Haiku) |
| Frontend | React 18 + Vite |
| Styling | Tailwind CSS v3 |
