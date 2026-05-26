# Verification Flow — Complete Lifecycle

## End-to-End Verification Flow

```
USER CLICKS FILE BUTTON
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  BROWSER: App.jsx                                       │
│  1. fetch("/mock_files/file1_clean.json")               │
│  2. setProfile(data)                                    │
│  3. fetch("/api/orchestrate", {                         │
│       method: "POST",                                   │
│       body: JSON.stringify(profileData)                 │
│     })                                                  │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP POST
                          │ /api/orchestrate
                          │ (Vite proxy strips /api)
                          ▼
┌─────────────────────────────────────────────────────────┐
│  FASTAPI: main.py @app.post("/orchestrate")             │
│  1. Loads custom rules from custom_rules.json           │
│  2. Calls run_orchestrator(data, custom_rules)          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  ORCHESTRATOR: agents/orchestrator.py                   │
│                                                         │
│  STEP 1 — ExtractionAgent                               │
│  ├── normalize_name(pan.name)                           │
│  ├── normalize_date(pan.dob)  ← typo correction         │
│  ├── normalize_date(aadhaar.dob)                        │
│  ├── uppercase PAN number, gender fields                │
│  └── logs changes: [{field, raw, normalized}]           │
│  Result: cleaned_profile + extraction_log               │
│                                                         │
│  STEP 2 — IdentityAgent (inline, 7 checks)              │
│  Each check wrapped in heal_check():                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ check_pan_format(pan.number)                    │   │
│  │  ├── normalize_pan(number)                      │   │
│  │  └── regex ^[A-Z]{5}[0-9]{4}[A-Z]$             │   │
│  │                                                 │   │
│  │ check_dob(pan.dob, aadhaar.dob)                 │   │
│  │  ├── normalize_date(pan.dob)                    │   │
│  │  ├── normalize_date(aadhaar.dob)                │   │
│  │  └── exact string comparison                   │   │
│  │                                                 │   │
│  │ check_gender(pan.gender, aadhaar.gender)        │   │
│  │  ├── normalize_gender("1") → "M"                │   │
│  │  └── canonical comparison M/F/O                │   │
│  │                                                 │   │
│  │ check_aadhaar_last4(bureau.last4, aadhaar.last4)│   │
│  │  ├── extract_aadhaar_last4("XXXX-XXXX-5678")   │   │
│  │  └── exact 4-digit comparison                  │   │
│  │                                                 │   │
│  │ check_name_fuzzy(pan.name, aadhaar.name)        │   │
│  │  ├── normalize_name on both                    │   │
│  │  ├── apply_transliteration on both             │   │
│  │  ├── is_initial_match detection               │   │
│  │  ├── fuzz.token_sort_ratio (raw + trans)       │   │
│  │  └── threshold comparison + verdict            │   │
│  │                                                 │   │
│  │ check_name_fuzzy(bureau.name, pan.name)         │   │
│  │  └── same multi-layer fuzzy                   │   │
│  │                                                 │   │
│  │ check_father_name(pan.father, aadhaar.father)   │   │
│  │  ├── normalize_father_name (strips S/O etc.)   │   │
│  │  └── check_name_fuzzy on cleaned names         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  + run_custom_rules(checks, profile)                    │
│    → exec() each saved custom rule function             │
│    → merge or append results                            │
│                                                         │
│  → identity_verdict = compute_overall_verdict(checks)   │
│  → confidence_score = compute_confidence_score(checks)  │
│                                                         │
│  For each soft_fail with no reason:                     │
│    explain_soft_fail(check_name, a, b)                  │
│    → LLM generates 1-sentence explanation               │
│                                                         │
│  STEP 3 — AddressAgent                                  │
│  ├── graph_lookup(each address)                         │
│  ├── graph_address_match(pair-wise)                     │
│  ├── fallback: fuzz.token_sort_ratio + pincode          │
│  ├── compute_address_trust_score(source, year)          │
│  └── LLM analysis if hard_conflicts > 0                 │
│                                                         │
│  STEP 4 — LLM Reasoning                                 │
│  ├── If failures exist: agent_analyze(failed_summary)   │
│  └── If all pass: static "All checks passed" result     │
│                                                         │
│  STEP 5 — FraudAgent                                    │
│  ├── Score 5 fraud signals                              │
│  └── LLM fraud narrative if score ≥ 30                  │
│                                                         │
│  STEP 6 — VerdictAgent                                  │
│  ├── Determine PROCEED/REVIEW/REJECT                    │
│  └── LLM underwriter notes (3 sections)                 │
│                                                         │
│  STEP 7 — AuditAgent                                    │
│  └── log_audit(result) → AUD-XXXX in memory             │
│                                                         │
│  Returns: full_result dict                              │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  FASTAPI: main.py (after orchestrate returns)           │
│  1. observe_verification() → updates pattern_memory.json│
│  2. analyze_and_propose() → may create proposals         │
│  3. save_verification() → writes to SQLite              │
│  4. Returns full_result + observation + proposal count  │
└─────────────────────────┬───────────────────────────────┘
                          │ JSON response
                          ▼
┌─────────────────────────────────────────────────────────┐
│  BROWSER: App.jsx                                       │
│  setResult(responseJson)                                │
│  setLoading(false)                                      │
│  React re-renders all tab content                       │
└─────────────────────────────────────────────────────────┘
```

---

## Verdict Decision Tree

```
Run 7 checks (+ custom rules)
         │
         ├── Any hard_fail?
         │         │
         │        YES ──────────────────► HARD BLOCK
         │         │
         │        NO
         │         │
         ├── Any soft_fail?
         │         │
         │        YES ──────────────────► SOFT ISSUES — HUMAN REVIEW
         │         │
         │        NO
         │         │
         └────────────────────────────► CLEAN
```

---

## Confidence Score Calculation

```
For each check:
   score = {pass: 100, soft_fail: 40, hard_fail: 0}[result]
   weight = 2 if check is critical else 1
   (critical = "Date of Birth", "PAN Format", "Aadhaar Last" in name)

final = round((Σ score×weight) / (Σ 100×weight) × 100)

Example — 7 checks all pass:
   5 normal checks: 5 × 100 × 1 = 500 / 5×100 = 100%
   2 critical checks: 2 × 100 × 2 = 400 / 2×100×2 = 100%
   Final: (500+400) / (500+400) × 100 = 100%

Example — DOB fails (critical), 6 others pass:
   5 normal pass: 500 / 500
   1 critical fail: 0 / 200
   1 other critical pass: 200 / 200
   Final: (500+0+200) / (500+200+200) × 100 = 700/900 × 100 ≈ 78%
   → MEDIUM CONFIDENCE (yellow)
```

---

## Data Model: Profile Input

```json
{
  "applicant_id": "FL-001",
  "pan": {
    "number":      "ABCPK1234D",   // PAN card number
    "name":        "Prashant Kumar", // Name on PAN
    "dob":         "1990-04-12",    // Date of birth (any format)
    "gender":      "M",             // M/F/Male/Female/1/2/मेल etc.
    "father_name": "Ramesh Kumar"   // Father's name (S/O prefix OK)
  },
  "aadhaar": {
    "last4":       "1234",          // Aadhaar last 4 digits
    "name":        "Prashant Kumar",
    "dob":         "1990-04-12",
    "gender":      "M",
    "father_name": "Ramesh Kumar"
  },
  "bureau": {
    "name":         "Prashant Kumar",
    "dob":          "1990-04-12",
    "pan_linked":   "ABCPK1234D",   // PAN linked in bureau
    "aadhaar_last4":"1234"           // Aadhaar last 4 in bureau
  },
  "addresses": {                    // Optional
    "aadhaar":        "12, MG Road, Pune 411001",
    "pan":            "12 MG Road, Pune",
    "bank_statement": "12, Mahatma Gandhi Road, Pune 411001",
    "gst":            "Plot 12, MG Road, Pune 411001",
    "self_declared":  "12 MG Road Pune 411001"
  },
  "doc_dates": {                    // Optional — year of each document
    "aadhaar":        2024,
    "pan":            2019,
    "bank_statement": 2026,
    "gst":            2025,
    "self_declared":  2026
  }
}
```

---

## Date Normalization: How 30+ Formats Become YYYY-MM-DD

```
Input: "2004 arpil 6th"
         │
Step 1: Strip ordinal suffixes
   re.sub(r'(\d+)(st|nd|rd|th)', r'\1', ...) → "2004 arpil 6"
         │
Step 2: Typo correction (word-boundary regex)
   "arpil" → re.sub(r'\barpil\b', 'april', ...) → "2004 april 6"
         │
Step 3: Try 25 format patterns
   "%Y %B %d" → datetime.strptime("2004 april 6", "%Y %B %d")
   → datetime(2004, 4, 6)
   → strftime("%Y-%m-%d") → "2004-04-06"
         │
Step 4: If all patterns fail → python-dateutil.parser.parse()
   (handles many exotic formats as fallback)
         │
Step 5: If dateutil also fails → return raw string unchanged

Typo map covers: arpil, apirl, januray, janury, feburary, febuary,
                  marh, mrach, auguest, auguts, septembar, septmber,
                  octuber, octobr, novembar, novembe, decembar, decmber
```
