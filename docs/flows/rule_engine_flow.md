# Rule Engine Flow

## Overview

The Rule Engine allows anyone to add new verification checks by writing plain English descriptions. The LLM converts these to executable Python functions that run on every future verification.

---

## Complete Rule Engine Flow

```
USER OPENS RULES TAB
         │
         ▼
RuleEngine.jsx mounts
GET /rules/list → fetches activeRules
         │
         ▼
User types rule description:
"Gender on PAN and Aadhaar must match exactly"
         │
         ▼
User clicks "Generate Rule"
         │
         ▼
POST /rules/create
  Body: { "rule_description": "Gender on PAN and Aadhaar must match exactly" }
         │
         ▼
main.py: create_rule(data) → create_rule_code(rule_description)
         │
         ▼
llm_functions.create_rule_code():
  Sends to LLM:
  ┌──────────────────────────────────────────────────────────────────┐
  │ Profile structure:                                               │
  │ {pan: {number, name, dob, gender, father_name},                 │
  │  aadhaar: {last4, name, dob, gender, father_name},              │
  │  bureau: {name, dob, pan_linked, aadhaar_last4}}                │
  │                                                                  │
  │ Rule: "Gender on PAN and Aadhaar must match exactly"            │
  │                                                                  │
  │ Requirements:                                                    │
  │  - Function name: custom_check_[short_snake_case]               │
  │  - Accepts: profile (dict)                                       │
  │  - Returns: {check, input_a, input_b, result, reason}           │
  │  - Use .get() for all dict access                                │
  │  - No imports                                                    │
  └──────────────────────────────────────────────────────────────────┘
         │
         ▼
LLM generates:
  def custom_check_gender_match_exact(profile):
      pan_gender = profile.get("pan", {}).get("gender", "")
      aadhaar_gender = profile.get("aadhaar", {}).get("gender", "")
      if pan_gender.upper() == aadhaar_gender.upper():
          return {
              "check": "Gender Match (Exact Custom Rule)",
              "input_a": f"PAN: {pan_gender}",
              "input_b": f"Aadhaar: {aadhaar_gender}",
              "result": "pass",
              "reason": f"Gender matches: {pan_gender}"
          }
      return {
          "check": "Gender Match (Exact Custom Rule)",
          "input_a": f"PAN: {pan_gender}",
          "input_b": f"Aadhaar: {aadhaar_gender}",
          "result": "hard_fail",
          "reason": f"Gender mismatch: PAN={pan_gender}, Aadhaar={aadhaar_gender}"
      }
         │
         ▼
Backend strips markdown fences (```python) if present
Extracts func_name via: re.search(r'def (custom_check_\w+)\(', code)
         │
         ▼
Response to frontend:
  {
    "rule_description": "Gender on PAN and Aadhaar must match exactly",
    "func_name": "custom_check_gender_match_exact",
    "generated_code": "def custom_check_gender_match_exact(profile):\n...",
    "status": "generated"
  }
         │
         ▼
RuleEngine.jsx shows code preview:
  ┌─────────────────────────────────────┐
  │ Rule: custom_check_gender_match_exact│
  │                                     │
  │ def custom_check_gender_match_exact │
  │ (profile):                          │
  │     pan_gender = profile.get(...)   │
  │     ...                             │
  └─────────────────────────────────────┘
  [Add to Engine]    [Regenerate]
         │
User clicks "Add to Engine"
         │
         ▼
POST /rules/save
  Body: {rule_description, func_name, generated_code, status: "generated"}
         │
         ▼
main.py: save_rule(data)
  → _load_custom_rules() from custom_rules.json
  → deduplicate by func_name
  → append new rule
  → _save_custom_rules(rules) to custom_rules.json
         │
         ▼
GET /rules/list refresh → activeRules updates
Rule appears in "Active Custom Rules" list with ACTIVE badge
```

---

## How Rules Run on Every Verification

```
POST /orchestrate or /verify-live
         │
         ▼
_load_custom_rules() → reads custom_rules.json
         │
         ▼
run_custom_rules(checks, profile):
  For each rule:
    1. exec_globals = {}
    2. exec(rule["generated_code"], exec_globals)
       (runs the def statement, adds function to exec_globals)
    3. func = exec_globals[rule["func_name"]]
    4. custom_result = func(profile)
    5. custom_result["is_custom"] = True

    Merge or append logic:
    ┌─────────────────────────────────────────────────────────┐
    │ rule_desc_lower = rule["rule_description"].lower()      │
    │                                                         │
    │ For each keyword in RULE_MERGE_KEYWORDS:                │
    │   "father" → "Father Name"                              │
    │   "dob"    → "Date of Birth"                            │
    │   "gender" → "Gender"                                   │
    │   "pan"    → "PAN"                                      │
    │   "name"   → "Name"                                     │
    │   etc.                                                  │
    │                                                         │
    │ If keyword in rule description:                         │
    │   Find existing check with matching prefix              │
    │   If custom says fail AND existing says pass:           │
    │     Override: existing.result = custom_result.result    │
    │     Prefix reason: "[Custom rule override] ..."         │
    │     Set custom_override = True                          │
    │   merged = True                                         │
    │   break                                                 │
    │                                                         │
    │ If not merged:                                          │
    │   checks.append(custom_result)                          │
    └─────────────────────────────────────────────────────────┘
```

---

## Merge Examples

### Example 1: Override a passing check (downgrade)
```
Built-in check: Gender Match → pass (result = "pass")
Custom rule:    "Gender must match exactly" → hard_fail

Result: The Gender Match check gets upgraded to hard_fail
        reason becomes "[Custom rule override] Gender mismatch..."
        The custom rule description is NOT added as a duplicate row
```

### Example 2: No merge (new independent check)
```
Custom rule: "Aadhaar last-4 must be all numeric"
Keyword "aadhaar" → looks for existing "Aadhaar" check
Found: "Aadhaar Last-4 Consistency" → already exists
But custom result is "pass" → no override needed
merged = True, no append

If custom result was "fail" and existing was "pass" → override would happen
```

### Example 3: Completely new check (no keyword match)
```
Custom rule: "PAN number must have sequential chars in position 5-8"
No keyword → "pan" IS a keyword, tries to find existing "PAN" check
Found "PAN Format Validity" → checks if custom says fail + existing says pass
If no match at all or no existing check found → checks.append(custom_result)
New row added to the check table
```

---

## Example: Active Custom Rules JSON

```json
[
  {
    "rule_description": "Gender on PAN and Aadhaar must match exactly",
    "func_name": "custom_check_gender_match_exact",
    "generated_code": "def custom_check_gender_match_exact(profile):\n    pan_gender = profile.get(\"pan\", {}).get(\"gender\", \"\")\n    aadhaar_gender = profile.get(\"aadhaar\", {}).get(\"gender\", \"\")\n    if pan_gender.upper() == aadhaar_gender.upper():\n        return {\"check\": \"Gender Match (Custom)\", \"input_a\": f\"PAN: {pan_gender}\", \"input_b\": f\"Aadhaar: {aadhaar_gender}\", \"result\": \"pass\", \"reason\": f\"Gender matches: {pan_gender}\"}\n    return {\"check\": \"Gender Match (Custom)\", \"input_a\": f\"PAN: {pan_gender}\", \"input_b\": f\"Aadhaar: {aadhaar_gender}\", \"result\": \"hard_fail\", \"reason\": f\"Gender mismatch\"}",
    "status": "generated"
  }
]
```

---

## Security Note

Custom rules are executed via Python's `exec()` with no sandbox:
```python
exec_globals = {}
exec(rule["generated_code"], exec_globals)
```

The `exec_globals` dict acts as an isolated namespace (the rule can't access the parent scope), but it can still import modules, read files, or make network calls if the generated code does so.

In the current hackathon implementation, this is acceptable because:
- Rules are generated by the LLM with explicit instructions to "import nothing"
- Rules are manually previewed by a human before being added
- Only trusted users can add rules

In production, this should be replaced with a restricted exec environment or a sandboxed execution container.
