# How VerifyIQ Works — Beginner's Guide

This document explains the entire system from a conceptual level. No prior experience required. We explain *why* things are built the way they are, not just what files contain what code.

---

## The Big Picture

When someone applies for a loan, the bank has documents from three sources:
1. **PAN card** — tax identity, has name, DOB, gender, father's name
2. **Aadhaar** — national ID, has name, DOB, gender, last 4 digits, address
3. **Bureau report** — credit history, has name, DOB, linked PAN, Aadhaar last 4

These three sources should all describe the same person. But in reality:
- Names are spelled differently ("Prashant" on PAN, "Prashanth" on Aadhaar)
- Dates are in different formats ("12/04/1990" vs "April 12th 1990")
- Some fields are abbreviated ("P. Kumar" vs "Prashant Kumar")
- Some fields have typos ("2004 arpil 6th")

VerifyIQ's job: **automatically decide if these three documents describe the same person** and give the underwriter a clear verdict.

---

## Why Agents? Why Not Just Code?

Simple rule-based code breaks instantly:
- Is "Prashant Kumar" the same as "Prashanth Kumar"? (transliteration variant)
- Is "P. Kumar" the same as "Prashant Kumar"? (abbreviation)
- Is "2004 arpil 6th" the same as "2004-04-06"? (typo + unusual format)

You need a combination of:
1. **Deterministic logic** — for things that have clear rules (PAN format regex, Aadhaar last-4 exact match)
2. **Fuzzy matching** — for names that are "close enough"
3. **LLM reasoning** — for edge cases where context matters

Breaking this into **specialized agents** makes each piece independent, testable, and replaceable:
- The extraction agent only normalizes data
- The identity agent only runs checks
- The address agent only analyzes addresses
- The fraud agent only looks for fraud patterns
- The verdict agent only makes the final decision

Each agent has a single responsibility. If the address agent breaks, the rest still work.

---

## Step-by-Step: What Happens When You Click FL-001

### Step 1: File is Loaded
The browser fetches `/mock_files/file1_clean.json` and stores it in `profile` state. This JSON contains the applicant's PAN, Aadhaar, Bureau data.

### Step 2: API Call to /orchestrate
The browser sends a POST request to the FastAPI backend with the profile JSON. Because of the Vite proxy, `/api/orchestrate` becomes `http://localhost:8000/orchestrate`.

### Step 3: ExtractionAgent Runs
Before any checks happen, all data is **normalized to a standard format**.
- Names become UPPERCASE with punctuation removed
- Dates are parsed from any format to YYYY-MM-DD
- DOB typos are corrected ("arpil" → "april" using word-boundary regex)
- Why normalize first? So every check works with clean data, not raw strings

### Step 4: Identity Checks Run (the core verification)
7 checks run, in this order:
1. Is the PAN format valid? (`ABCPK1234D` matches `[A-Z]{5}[0-9]{4}[A-Z]`)
2. Does DOB on PAN match DOB on Aadhaar? (after normalization)
3. Does gender on PAN match Aadhaar? (after mapping "1" → M, "मेल" → M, etc.)
4. Does Aadhaar last-4 on bureau match actual Aadhaar? (handles masked formats)
5. Does name on PAN match name on Aadhaar? (multi-layer fuzzy)
6. Does name on Bureau match PAN? (multi-layer fuzzy)
7. Does father name on PAN match Aadhaar? (strip S/O, SHRI etc. then fuzzy)

Each check is **wrapped in `heal_check()`** — if something explodes (e.g. null data, unexpected format), it doesn't crash the whole pipeline. Instead:
- The LLM analyzes what went wrong
- The check returns a soft_fail with explanation
- The pipeline continues

### Step 5: LLM Reasoning
If any checks failed, the AI reads all failures together and produces:
- `agent_note` — a 2-sentence summary
- `confidence` — HIGH/MEDIUM/LOW (from AI's perspective)
- `recommendation` — PROCEED/REVIEW/REJECT
- `reasoning` — one sentence explaining the decision

Why AI here? Because some failures matter together but not alone. Example: One soft name fail might be fine (just an abbreviation), but 3 soft fails together suggests something suspicious.

### Step 6: Address Analysis
The address agent looks at addresses from different sources (Aadhaar, PAN, bank statement, etc.) and asks: are these all the same place?

It uses a **knowledge graph** of Indian roads:
- "MG Road" = "Mahatma Gandhi Road" = "MG RD" — all aliases in the graph
- If both addresses mention the same road, it's a GRAPH_CONFIRMED_MATCH
- If one mentions "MG Road Bangalore" and other "Marine Drive Mumbai" — GRAPH_CONFIRMED_DIFFERENT (different cities!)
- If addresses aren't in the graph → falls back to fuzzy string matching + pincode comparison

Each document source gets a **trust score** based on type (Aadhaar = 90, bank statement = 75, self-declared = 15) and how old the document is (2024 doc is more trusted than 2018 doc).

### Step 7: Fraud Agent
Combines signals from identity checks + address analysis:
- DOB mismatch alone = +40 fraud score (biggest red flag)
- Multiple name mismatches = +25
- Conflicting addresses + identity issues = +30
- Pincode mismatch = +20
- Many soft fails = +15

Score ≥ 60 → HIGH RISK. Score ≥ 30 → MEDIUM RISK. LLM generates a fraud narrative explaining what pattern was detected.

### Step 8: Verdict Agent
Makes the final call:
- REJECT if fraud ≥ 60 OR identity is HARD BLOCK
- REVIEW if fraud ≥ 30, SOFT ISSUES, or CONFLICTING addresses
- PROCEED if everything looks clean

Then generates professional underwriter notes in 3 sections (Summary, Key Findings, Recommended Action).

### Step 9: Audit Logging
An in-memory audit entry (AUD-0001, AUD-0002...) is created. The full verification is also saved to SQLite for permanent history.

### Step 10: React Re-renders
The response flows back to the browser, React state is updated, and all 10 tabs now show their portion of the result.

---

## How Frontend Talks to Backend

```
React Component                   FastAPI
     │                               │
     │  fetch("/api/orchestrate",    │
     │    {method: "POST",           │
     │     body: JSON.stringify(..)} │
     │                               │
     │  ───────────────────────────► │
     │  (Vite proxy strips /api)     │
     │                               │  run_orchestrator()
     │                               │  all agents execute
     │                               │
     │  ◄─────────────────────────── │
     │  JSON response                │
     │  (all agent results combined) │
     │                               │
setResult(data)                       │
UI re-renders                         │
```

Every component that needs backend data calls its own endpoint. Components with independent data (like AuditTrail, MemoryDashboard) fetch their own APIs when they mount.

---

## How Fuzzy Matching Works

Imagine you're comparing "P. KUMAR" and "PRASHANT KUMAR".

**Raw fuzzy score** (rapidfuzz token_sort_ratio):
- Sorts tokens alphabetically before comparing: "KUMAR P" vs "KUMAR PRASHANT"
- Result: ~50% similarity (P ≠ PRASHANT)
- This alone would fail the check

**Transliteration layer**:
- Looks each token up in the TRANSLITERATION_GRAPH
- "P" is not in the graph, so stays as "P"
- Doesn't help here

**Initial detection**:
- is_initial_match("P KUMAR", "PRASHANT KUMAR") → True
- Because: first token "P" is a single char AND "PRASHANT" starts with "P" AND surnames match ("KUMAR" == "KUMAR")

**Threshold adjustment**:
- Default pass threshold = 85
- initial_leniency=True + initial_match=True → pass threshold drops by 10 (to 75), soft threshold drops by 15 (to 40)

**Final result**: 
- best_score ~50, which is above adj_soft (40) → soft_fail
- The LLM then explains: "P. Kumar and Prashant Kumar likely refer to the same person as the first name appears to be an initial abbreviation."

This is why transliteration names like "Prashanth" (South Indian) matching "Prashant" work — the transliteration graph maps one to the other before scoring.

---

## How the Self-Improving System Works

Think of it like a teacher watching students work, noticing patterns, and suggesting improvements.

**ObservationAgent** watches every verification run:
- It notices: "The date format DD/MM/YYYY was seen 5 times"
- It notices: "Names with initials caused 4 soft fails this week"
- It notices: "The typo 'januray' appeared 3 times"

When a pattern appears 3 or more times (PROPOSAL_THRESHOLD), the **RuleProposerAgent** creates a proposal:
- "DATE_FORMAT_HANDLER: DD/MM/YYYY appears frequently — add explicit handler"
- "TYPO_CORRECTION_RULE: 'januray' seen 3× — add to typo dictionary"

These proposals appear in the Self-Improving tab. A human underwriter (or admin) reviews them and either:
- **Approves** → system optionally auto-generates Python code for the fix
- **Rejects** → moved to rejected list

This closes the loop: the system learns from real data and proposes real improvements.

---

## How Memory Persistence Works

**The problem**: Python dicts disappear when the server restarts. If the observation agent was tracking patterns in a regular Python dict, you'd lose all learning every restart.

**The solution**: Two persistence layers:

**JSON files** (for agent state):
```
Every time ObservationAgent updates pattern_memory,
it calls memory_store.save("pattern_memory", mem)

This writes to /memory_data/pattern_memory.json.tmp
then calls os.replace(.tmp, .json)

Why the .tmp trick?
If the server crashes mid-write, the .tmp file exists
but the .json is still the old complete file.
os.replace is atomic — either the new file is there or it isn't.
No partial/corrupt writes.
```

**SQLite** (for queryable history):
```
Every verification → save_verification() → SQLite verifications table
Each check result → check_results table (FK to verification)
Every healing event → healing_events table
Every test session → test_sessions table

SQLite is a file-based database. It survives restarts.
It lets you query: "show me the last 50 verifications" or
"what check results did verification #47 have?"
```

---

## How Rules Are Generated

The Rule Engine is a live code generation system:

1. User types: "Father name on PAN must have at least 2 words"
2. LLM receives this as a prompt, along with the exact profile structure
3. LLM generates a Python function:
```python
def custom_check_father_name_words(profile):
    father_name = profile.get("pan", {}).get("father_name", "")
    words = father_name.strip().split()
    if len(words) >= 2:
        return {"check": "Father Name Word Count", "input_a": father_name,
                "input_b": "2+ words required", "result": "pass", ...}
    return {"check": ..., "result": "hard_fail", ...}
```
4. Frontend shows a preview of the code
5. User clicks "Add to Engine"
6. Function is saved to `custom_rules.json`
7. Every future verification runs this function via Python's `exec()`

**Smart merge logic**: If the rule mentions "father", "pan", "dob", etc., it tries to find an existing check with that name and upgrade its result rather than adding a duplicate row.

---

## How the Self-Healing System Protects the Pipeline

Every check in the orchestrator is wrapped:

```python
# Instead of:
result = check_pan_format(pan_number)

# The orchestrator does:
result = heal_check("PAN Format Validity", check_pan_format, profile, pan_number)
```

`heal_check` is a try/except wrapper. If `check_pan_format` throws any exception (null input, unexpected type, anything), instead of crashing:
1. The error is fingerprinted (MD5 hash of error type + message)
2. The LLM is asked: "what caused this? what should be fixed?"
3. The answer is logged to `healing_log.json` and SQLite
4. A soft_fail result is returned with the message "[Self-Healed] — explanation of issue"
5. The pipeline continues to the next check

The HealingPanel shows:
- Every healing event (timestamp, check name, error, root cause, fix)
- Known error patterns (same error hash seen multiple times)

This means the system never hard-crashes. Even if someone sends malformed data, all 7 checks complete and a partial verdict is produced.

---

## Why Confidence Score ≠ Verdict

The verdict is simple: hard_fail → HARD BLOCK, soft_fail → SOFT ISSUES, all pass → CLEAN.

But a confidence score is **how sure are we** within that verdict. Two CLEAN verdicts might have different confidence:
- 7/7 checks pass → 100% confidence (HIGH)
- 5 pass, 2 soft_fail but custom rule says pass → 75% (MEDIUM)

Critical checks (DOB, PAN format, Aadhaar last-4) are weighted 2× because a DOB mismatch is much more serious than a father name soft fail.

The score appears as a progress bar in the UI. Underwriters use it to prioritize REVIEW cases.

---

## How Address Graph Matching Works

Standard fuzzy matching fails on Indian addresses because:
- "MG Road" and "Mahatma Gandhi Road" have very low string similarity
- But they're the exact same road

The knowledge graph pre-defines:
```python
"MG ROAD PUNE": {
    "aliases": ["MAHATMA GANDHI ROAD PUNE", "M G ROAD PUNE", ...],
    "cities": ["PUNE"],
    "pincodes": ["411001"]
}
```

When comparing two addresses:
1. `graph_lookup(addr_a)` — does any known road name/alias appear in the address?
2. `graph_lookup(addr_b)` — same
3. If both found:
   - Same road? → GRAPH_CONFIRMED_MATCH (high confidence, skip fuzzy)
   - Different cities? → GRAPH_CONFIRMED_DIFFERENT (hard conflict!)
4. If neither found → fall back to token_sort_ratio fuzzy matching + pincode comparison

This prevents false conflicts (MG Road = Mahatma Gandhi Road) and catches real ones (MG Road Bangalore ≠ Marine Drive Mumbai).
