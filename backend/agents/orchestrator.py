import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from checks import (
    check_pan_format,
    check_dob,
    check_gender,
    check_aadhaar_last4,
    check_name_fuzzy,
    check_father_name,
    compute_overall_verdict,
    compute_confidence_score,
)
from llm_functions import explain_soft_fail, agent_analyze

from agents.extraction_agent import run_extraction_agent
from agents.address_agent import run_address_agent
from agents.fraud_agent import run_fraud_agent
from agents.verdict_agent import run_verdict_agent
from agents.audit_agent import log_audit
from agents.self_healing_agent import heal_check, get_healing_log


async def run_orchestrator(profile: dict, custom_rules: list = []) -> dict:
    steps = []

    # Step 1: Extraction
    steps.append({"step": 1, "name": "Data Extraction & Normalization", "status": "running"})
    extraction_result = run_extraction_agent(profile)
    steps[-1]["status"] = "complete"
    steps[-1]["summary"] = f"{extraction_result['fields_normalized']} fields normalized"
    cleaned = extraction_result["cleaned_profile"]

    # Step 2: Identity Checks
    steps.append({"step": 2, "name": "Identity Cross-Check", "status": "running"})
    pan = cleaned.get("pan", {})
    aadhaar = cleaned.get("aadhaar", {})
    bureau = cleaned.get("bureau", {})

    checks = [
        heal_check("PAN Format Validity", check_pan_format, profile, pan.get("number", "")),
        heal_check("Date of Birth (PAN vs Aadhaar)", check_dob, profile, pan.get("dob", ""), aadhaar.get("dob", "")),
        heal_check("Gender (PAN vs Aadhaar)", check_gender, profile, pan.get("gender", ""), aadhaar.get("gender", "")),
        heal_check("Aadhaar Last 4 (Bureau vs Aadhaar)", check_aadhaar_last4, profile, bureau.get("aadhaar_last4", ""), aadhaar.get("last4", "")),
        heal_check("Name Match (PAN vs Aadhaar)", check_name_fuzzy, profile, pan.get("name", ""), aadhaar.get("name", ""), "PAN", "Aadhaar"),
        heal_check("Name Match (Bureau vs PAN)", check_name_fuzzy, profile, bureau.get("name", ""), pan.get("name", ""), "Bureau", "PAN"),
        heal_check("Father Name (PAN vs Aadhaar)", check_father_name, profile, pan.get("father_name", ""), aadhaar.get("father_name", "")),
    ]

    for check in checks:
        if check["result"] == "soft_fail" and check.get("reason") is None:
            check["reason"] = explain_soft_fail(
                check["check"], check["input_a"], check["input_b"]
            )

    # Apply custom rules
    RULE_MERGE_KEYWORDS = {
        "father": "Father Name", "dob": "Date of Birth", "date": "Date of Birth",
        "gender": "Gender", "pan": "PAN", "aadhaar": "Aadhaar",
        "bureau": "Bureau", "name": "Name",
    }
    for rule in custom_rules:
        try:
            exec_globals = {}
            exec(rule["generated_code"], exec_globals)
            func = exec_globals[rule["func_name"]]
            custom_result = func(profile)
            custom_result["is_custom"] = True
            rule_desc_lower = rule["rule_description"].lower()
            merged = False
            for keyword, check_prefix in RULE_MERGE_KEYWORDS.items():
                if keyword in rule_desc_lower:
                    for existing in checks:
                        if check_prefix.lower() in existing["check"].lower():
                            if custom_result["result"] != "pass" and existing["result"] == "pass":
                                existing["result"] = custom_result["result"]
                                existing["reason"] = f"[Custom rule override] {custom_result['reason']}"
                                existing["custom_override"] = True
                            merged = True
                            break
                    if merged:
                        break
            if not merged:
                checks.append(custom_result)
        except Exception as e:
            checks.append({
                "check": rule["rule_description"],
                "input_a": "Rule execution error",
                "input_b": str(e),
                "result": "soft_fail",
                "reason": f"Custom rule error: {str(e)}",
                "is_custom": True,
            })

    identity_verdict = compute_overall_verdict(checks)
    confidence_score = compute_confidence_score(checks)

    steps[-1]["status"] = "complete"
    hard_fails = len([c for c in checks if c["result"] == "hard_fail"])
    soft_fails = len([c for c in checks if c["result"] == "soft_fail"])
    steps[-1]["summary"] = f"Verdict: {identity_verdict} | {hard_fails} hard, {soft_fails} soft fails"

    identity_result = {
        "agent": "identity",
        "checks": checks,
        "verdict": identity_verdict,
        "hard_fails": hard_fails,
        "soft_fails": soft_fails,
    }

    # Step 3: Address Analysis
    steps.append({"step": 3, "name": "Address Verification", "status": "running"})
    addresses = cleaned.get("addresses", profile.get("addresses", {}))
    doc_dates = profile.get("doc_dates", {})
    address_result = run_address_agent(addresses, profile, doc_dates)
    steps[-1]["status"] = "complete"
    steps[-1]["summary"] = f"Verdict: {address_result['verdict']} | {address_result.get('hard_conflicts', 0)} hard conflicts"

    # Step 4: LLM Reasoning
    steps.append({"step": 4, "name": "LLM Reasoning Pass", "status": "running"})
    failed = [c for c in checks if c["result"] != "pass"]
    if failed:
        failed_summary = "\n".join([
            f"- {c['check']}: {c['input_a']} vs {c['input_b']} → {c['result']}"
            for c in failed
        ])
        reasoning_result = await agent_analyze(failed_summary, profile)
    else:
        reasoning_result = {
            "agent_note": "All checks passed. No anomalies detected.",
            "confidence": "HIGH",
            "recommendation": "PROCEED",
            "reasoning": "All deterministic checks passed with no mismatches.",
        }
    steps[-1]["status"] = "complete"
    steps[-1]["summary"] = f"Recommendation: {reasoning_result.get('recommendation', 'N/A')}"

    # Step 5: Fraud Detection
    steps.append({"step": 5, "name": "Fraud Signal Analysis", "status": "running"})
    fraud_result = run_fraud_agent(identity_result, address_result, profile)
    steps[-1]["status"] = "complete"
    steps[-1]["summary"] = f"Fraud Score: {fraud_result['fraud_score']}/100 ({fraud_result['risk_level']} RISK)"

    # Step 6: Final Verdict
    steps.append({"step": 6, "name": "Underwriter Verdict", "status": "running"})
    verdict_result = run_verdict_agent(identity_result, address_result, fraud_result, confidence_score, profile)
    steps[-1]["status"] = "complete"
    steps[-1]["summary"] = f"Final Decision: {verdict_result['final_verdict']}"

    full_result = {
        "applicant_id": profile.get("applicant_id", "UNKNOWN"),
        "pipeline_steps": steps,
        "extraction_result": extraction_result,
        "checks": checks,
        "identity_verdict": identity_verdict,
        "confidence_score": confidence_score,
        "reasoning_result": reasoning_result,
        "address_result": address_result,
        "fraud_result": fraud_result,
        "final_verdict": verdict_result,
        "agent_results": {
            "extraction": extraction_result,
            "identity": identity_result,
            "address": address_result,
            "reasoning": reasoning_result,
            "fraud": fraud_result,
            "verdict": verdict_result,
        },
        "rules_applied": len(custom_rules),
        "healing_log": get_healing_log(),
    }

    # Step 7: Audit Logging
    steps.append({"step": 7, "name": "Audit Logging", "status": "running"})
    audit_entry = log_audit(full_result, profile)
    steps[-1]["status"] = "complete"
    steps[-1]["summary"] = f"Audit ID: {audit_entry['audit_id']}"

    full_result["audit_entry"] = audit_entry
    full_result["pipeline_steps"] = steps

    return full_result
