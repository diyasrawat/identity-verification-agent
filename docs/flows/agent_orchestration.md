# Agent Orchestration Flow

## Overview

The orchestrator (`agents/orchestrator.py`) is the conductor of the pipeline. It calls each agent in sequence, passing outputs from earlier steps to later ones. The 7-step pipeline always runs in order and always completes (thanks to self-healing).

---

## Pipeline Step Dependency Graph

```
Profile Input
    │
    ▼
[1] ExtractionAgent ──────────────────────────────────────────────
    Output: cleaned_profile (normalized data)
    │
    └─────────────────────────────────────────┐
                                              ▼
[2] IdentityAgent                     Uses cleaned_profile.pan/aadhaar/bureau
    Output: checks[], identity_verdict, confidence_score
    │
    ├────────────────────────────────────────┐
    │                                        │
    ▼                                        ▼
[3] AddressAgent                      [4] LLM Reasoning
    Uses profile.addresses                Uses checks[] from step 2
    Uses profile.doc_dates                (only runs on failures)
    Output: address_result                Output: reasoning_result
    │                                        │
    └─────────────────┬──────────────────────┘
                      ▼
[5] FraudAgent
    Uses: identity_result (step 2), address_result (step 3)
    Uses: profile.applicant_id
    Output: fraud_result
    │
    ▼
[6] VerdictAgent
    Uses: identity_result (step 2), address_result (step 3),
          fraud_result (step 5), confidence_score (step 2)
    Output: verdict_result (PROCEED/REVIEW/REJECT + notes)
    │
    ▼
[7] AuditAgent
    Uses: full_result dict, profile
    Output: audit_entry (AUD-XXXX)
    │
    ▼
Return full_result
```

---

## Each Agent: Inputs and Outputs

### Agent 1: ExtractionAgent
```
File: agents/extraction_agent.py
Function: run_extraction_agent(profile)

Input:  Raw profile dict with pan{}, aadhaar{}, bureau{}

Processing:
  • normalize_name() on: pan.name, pan.father_name,
                         aadhaar.name, aadhaar.father_name,
                         bureau.name
  • normalize_date() on: pan.dob, aadhaar.dob, bureau.dob
  • .upper().strip() on: pan.number, pan.gender, aadhaar.gender
  • .strip() on: aadhaar.last4, bureau.aadhaar_last4
  • Logs any field where raw != normalized

Output: {
  agent: "extraction",
  status: "complete",
  cleaned_profile: {pan:{}, aadhaar:{}, bureau:{}, addresses:{}, applicant_id},
  extraction_log: [{field, raw, normalized, action}, ...],
  fields_normalized: 3
}
```

### Agent 2: IdentityAgent (inline in orchestrator)
```
Not a separate file — implemented directly in orchestrator.py

Input:  cleaned_profile from step 1
        custom_rules list (from custom_rules.json)

Processing:
  Each of 7 check functions, wrapped in heal_check():
    heal_check(check_name, check_func, profile, *args)
    ↓
    try: return check_func(*args)
    except: return soft_fail with LLM analysis

  For soft_fails with no reason:
    explain_soft_fail(name, a, b) → 1-sentence LLM explanation

  Custom rules: exec() each function, merge or append results

Output:
  checks[] — 7+ check result objects
  identity_verdict — "CLEAN" | "SOFT ISSUES — HUMAN REVIEW" | "HARD BLOCK"
  confidence_score — {score, label, color}
```

### Agent 3: AddressAgent
```
File: agents/address_agent.py
Function: run_address_agent(addresses, profile, doc_dates)

Input:  addresses dict (source → address string)
        profile (for applicant_id)
        doc_dates (source → year)

If no addresses:
  Returns status: "skipped", verdict: "NO_ADDRESS_DATA"

Processing:
  1. compute_address_trust_score(source, year) for each source
  2. normalize_address() each address (expand abbreviations)
  3. extract_pincode() each address
  4. For each pair:
     a. graph_address_match(addr_a, addr_b)
        → GRAPH_CONFIRMED_MATCH: skip fuzzy (treat as same)
        → GRAPH_CONFIRMED_DIFFERENT: add hard conflict
        → GRAPH_PARTIAL/UNKNOWN: fall back to:
     b. fuzzy token_sort_ratio + pincode check
  5. canonical_source = highest trust score
  6. If hard conflicts or many soft conflicts: LLM analysis

Output: {
  agent: "address",
  verdict: "CONSISTENT"|"LIKELY_SAME"|"CONFLICTING"|"NO_ADDRESS_DATA",
  canonical_address, canonical_source,
  conflicts[], hard_conflicts (count), soft_conflicts (count),
  trust_scores {source: score},
  normalized_addresses, pincodes, pincode_groups,
  agent_analysis (LLM text or static),
  graph_lookups {source: {found, canonical_road, ...}}
}
```

### Agent 4: LLM Reasoning (inline in orchestrator)
```
Not a separate file — uses llm_functions.agent_analyze()

Input:  failed checks list (checks where result != "pass")
        profile dict

If no failures:
  Returns static: {agent_note: "All checks passed...",
                   confidence: "HIGH", recommendation: "PROCEED"}

If failures exist:
  Builds failed_summary string with all failures
  Calls agent_analyze(failed_summary, profile)
  LLM returns JSON with: agent_note, confidence, recommendation, reasoning

Output: {
  agent_note: string,
  confidence: "HIGH"|"MEDIUM"|"LOW",
  recommendation: "PROCEED"|"REVIEW"|"REJECT",
  reasoning: string
}
```

### Agent 5: FraudAgent
```
File: agents/fraud_agent.py
Function: run_fraud_agent(identity_result, address_result, profile)

Input:  identity_result (checks[], verdict)
        address_result (verdict, conflicts[])
        profile dict

Processing:
  Scores 5 fraud signals:
  1. DOB hard fail → +40
  2. ≥2 name checks failed → +25
  3. Conflicting addr + (hard_fail OR ≥2 soft_fail) → +30
  4. Pincode mismatch conflict exists → +20
  5. ≥3 soft fails → +15
  Cap at 100

  If score ≥ 30: LLM generates fraud narrative

Output: {
  agent: "fraud",
  fraud_score: 0-100,
  risk_level: "LOW"|"MEDIUM"|"HIGH",
  risk_color: "green"|"yellow"|"red",
  fraud_signals: [{signal, weight, detail}, ...],
  fraud_narrative: string
}
```

### Agent 6: VerdictAgent
```
File: agents/verdict_agent.py
Function: run_verdict_agent(identity_result, address_result,
                            fraud_result, confidence_score, profile)

Input:  all previous agent results

Processing:
  Determine final_verdict:
    fraud_score >= 60 OR identity == HARD BLOCK → REJECT
    fraud_score >= 30 OR identity == SOFT ISSUES
      OR address == CONFLICTING → REVIEW
    Otherwise → PROCEED

  Always calls LLM for underwriter_notes:
    Provides: applicant_id, final_verdict, identity_verdict,
              address_verdict, fraud level, failed checks summary,
              address + fraud analysis
    LLM writes 3-section professional notes

Output: {
  agent: "verdict",
  final_verdict: "PROCEED"|"REVIEW"|"REJECT",
  verdict_color: "green"|"yellow"|"red",
  underwriter_notes: string (3 sections),
  decision_factors: {identity_verdict, address_verdict,
                     fraud_score, confidence_score}
}
```

### Agent 7: AuditAgent
```
File: agents/audit_agent.py
Function: log_audit(orchestration_result, profile)

Input:  full orchestration result dict
        original profile dict

Processing:
  Creates AUD-XXXX entry from result data
  Appends to in-memory audit_store list

Output: {
  audit_id: "AUD-0001",
  timestamp: ISO string,
  applicant_id,
  agents_run: ["extraction", "identity", ...],
  final_verdict,
  fraud_score,
  confidence_score,
  identity_verdict,
  address_verdict,
  checks_run,
  hard_fails,
  soft_fails,
  rules_applied
}

Note: This is SESSION ONLY (in-memory list).
      SQLite persistence is handled in main.py AFTER orchestrate returns.
```

---

## Custom Rules Integration

Custom rules run as part of step 2, after the 7 built-in checks:

```python
RULE_MERGE_KEYWORDS = {
    "father": "Father Name",
    "dob": "Date of Birth",
    "date": "Date of Birth",
    "gender": "Gender",
    "pan": "PAN",
    "aadhaar": "Aadhaar",
    "bureau": "Bureau",
    "name": "Name",
}

for rule in custom_rules:
    exec_globals = {}
    exec(rule["generated_code"], exec_globals)
    func = exec_globals[rule["func_name"]]
    custom_result = func(profile)
    custom_result["is_custom"] = True

    # Try to merge into existing check
    for keyword, check_prefix in RULE_MERGE_KEYWORDS.items():
        if keyword in rule_description_lower:
            for existing in checks:
                if check_prefix.lower() in existing["check"].lower():
                    # Override if custom says fail but existing says pass
                    if custom_result["result"] != "pass" and existing["result"] == "pass":
                        existing["result"] = custom_result["result"]
                        existing["reason"] = f"[Custom rule override] ..."
                    merged = True
                    break

    if not merged:
        checks.append(custom_result)  # New independent check
```

---

## self_healing_agent Integration

`heal_check()` wraps every check call in the orchestrator:

```python
# orchestrator.py line 43-48:
checks = [
    heal_check("PAN Format Validity",           check_pan_format,    profile, pan.number),
    heal_check("Date of Birth (PAN vs Aadhaar)",check_dob,           profile, pan.dob, aadhaar.dob),
    heal_check("Gender (PAN vs Aadhaar)",        check_gender,        profile, pan.gender, aadhaar.gender),
    heal_check("Aadhaar Last 4",                 check_aadhaar_last4, profile, bureau.last4, aadhaar.last4),
    heal_check("Name Match (PAN vs Aadhaar)",    check_name_fuzzy,    profile, pan.name, aadhaar.name, "PAN", "Aadhaar"),
    heal_check("Name Match (Bureau vs PAN)",     check_name_fuzzy,    profile, bureau.name, pan.name, "Bureau", "PAN"),
    heal_check("Father Name",                    check_father_name,   profile, pan.father_name, aadhaar.father_name),
]
```

If any check raises an exception → heal_check catches it, logs it, returns safe soft_fail → pipeline continues.

---

## Pipeline Timing

```
ExtractionAgent:  <5ms (pure Python normalization)
IdentityAgent:    <10ms (all deterministic, 1-3 LLM calls for soft_fails)
AddressAgent:     <5ms deterministic + 0-200ms if LLM fires (on hard conflicts)
LLM Reasoning:    100-300ms (if failures) or 0ms (if all pass)
FraudAgent:       <5ms scoring + 0-200ms LLM narrative (if score ≥ 30)
VerdictAgent:     100-300ms (always calls LLM for underwriter notes)
AuditAgent:       <1ms (in-memory append)

Total clean file:    ~300-600ms (1-2 LLM calls)
Total soft issue:    ~600ms-1.2s (2-4 LLM calls)
Total hard block:    ~400-800ms (fewer LLM calls — some skip)
```
