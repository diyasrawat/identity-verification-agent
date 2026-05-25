import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from checks import (
    check_pan_format,
    check_dob,
    check_gender,
    check_aadhaar_last4,
    check_name_fuzzy,
    check_father_name,
    compute_overall_verdict,
    normalize_date,
)
from llm_functions import explain_soft_fail, explain_ask_ai, agent_analyze, create_rule_code

app = FastAPI(title="Identity Cross-Verification Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

custom_rules_store = []

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


def run_custom_rules(checks: list, profile: dict):
    for rule in custom_rules_store:
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
                            if (custom_result["result"] != "pass"
                                    and existing["result"] == "pass"):
                                existing["result"] = custom_result["result"]
                                existing["reason"] = (
                                    f"[Custom rule override] {custom_result['reason']}"
                                )
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


def compute_confidence_score(checks: list) -> dict:
    total = len(checks)
    if total == 0:
        return {"score": 0, "label": "NO DATA", "color": "gray"}

    weights = {"pass": 100, "soft_fail": 40, "hard_fail": 0}
    critical_prefixes = ["Date of Birth", "PAN Format", "Aadhaar Last"]

    weighted_sum = 0
    weight_total = 0

    for check in checks:
        result = check.get("result", "hard_fail")
        score = weights.get(result, 0)
        is_critical = any(p in check.get("check", "") for p in critical_prefixes)
        w = 2 if is_critical else 1
        weighted_sum += score * w
        weight_total += 100 * w

    final_score = round((weighted_sum / weight_total) * 100)

    if final_score >= 85:
        label, color = "HIGH CONFIDENCE", "green"
    elif final_score >= 55:
        label, color = "MEDIUM CONFIDENCE", "yellow"
    else:
        label, color = "LOW CONFIDENCE", "red"

    return {"score": final_score, "label": label, "color": color}


class VerifyRequest(BaseModel):
    applicant_id: str
    pan: dict
    aadhaar: dict
    bureau: dict


class ExplainRequest(BaseModel):
    check: dict
    full_profile: dict


async def agent_reasoning_pass(checks: list, profile: dict) -> dict:
    failed = [c for c in checks if c["result"] != "pass"]
    if not failed:
        return {
            "agent_note": "All checks passed. No anomalies detected.",
            "confidence": "HIGH",
            "recommendation": "PROCEED",
            "reasoning": "All deterministic checks passed with no mismatches.",
        }

    failed_summary = "\n".join([
        f"- {c['check']}: {c['input_a']} vs {c['input_b']} → {c['result']}"
        for c in failed
    ])
    return await agent_analyze(failed_summary, profile)


@app.post("/verify")
async def verify(profile: VerifyRequest):
    pan = profile.pan
    aadhaar = profile.aadhaar
    bureau = profile.bureau

    checks = [
        check_pan_format(pan["number"]),
        check_dob(pan["dob"], aadhaar["dob"]),
        check_gender(pan["gender"], aadhaar["gender"]),
        check_aadhaar_last4(bureau["aadhaar_last4"], aadhaar["last4"]),
        check_name_fuzzy(pan["name"], aadhaar["name"], "PAN", "Aadhaar"),
        check_name_fuzzy(bureau["name"], pan["name"], "Bureau", "PAN"),
        check_father_name(pan["father_name"], aadhaar["father_name"]),
    ]

    for check in checks:
        if check["result"] == "soft_fail" and check.get("reason") is None:
            check["reason"] = explain_soft_fail(
                check["check"], check["input_a"], check["input_b"]
            )

    profile_dict = profile.model_dump()
    run_custom_rules(checks, profile_dict)

    verdict = compute_overall_verdict(checks)
    confidence = compute_confidence_score(checks)
    agent_result = await agent_reasoning_pass(checks, profile_dict)

    return {
        "applicant_id": profile.applicant_id,
        "checks": checks,
        "verdict": verdict,
        "confidence_score": confidence,
        "agent_note": agent_result.get("agent_note"),
        "confidence": agent_result.get("confidence"),
        "recommendation": agent_result.get("recommendation"),
        "reasoning": agent_result.get("reasoning"),
    }


@app.post("/explain")
def explain(body: ExplainRequest):
    explanation = explain_ask_ai(body.check, body.full_profile)
    return {"explanation": explanation}


@app.post("/verify-live")
async def verify_live(data: dict):
    pan = data.get("pan", {})
    aadhaar = data.get("aadhaar", {})
    bureau = data.get("bureau", {})

    raw_pan_dob = pan.get("dob", "")
    raw_aadhaar_dob = aadhaar.get("dob", "")

    checks = [
        check_pan_format(pan.get("number", "")),
        check_dob(raw_pan_dob, raw_aadhaar_dob),
        check_gender(pan.get("gender", ""), aadhaar.get("gender", "")),
        check_aadhaar_last4(bureau.get("aadhaar_last4", ""), aadhaar.get("last4", "")),
        check_name_fuzzy(pan.get("name", ""), aadhaar.get("name", ""), "PAN", "Aadhaar"),
        check_name_fuzzy(bureau.get("name", ""), pan.get("name", ""), "Bureau", "PAN"),
        check_father_name(pan.get("father_name", ""), aadhaar.get("father_name", "")),
    ]

    for check in checks:
        if check["result"] == "soft_fail" and check.get("reason") is None:
            check["reason"] = explain_soft_fail(
                check["check"], check["input_a"], check["input_b"]
            )

    run_custom_rules(checks, data)

    verdict = compute_overall_verdict(checks)
    confidence = compute_confidence_score(checks)

    return {
        "checks": checks,
        "verdict": verdict,
        "confidence_score": confidence,
        "mode": "live_test",
    }


# ── Rule Engine endpoints ──────────────────────────────────────────────────────

@app.post("/rules/create")
async def create_rule(data: dict):
    rule_description = data.get("rule_description", "")
    generated_code, func_name = await create_rule_code(rule_description)
    return {
        "rule_description": rule_description,
        "func_name": func_name,
        "generated_code": generated_code,
        "status": "generated",
    }


@app.post("/rules/save")
async def save_rule(data: dict):
    global custom_rules_store
    custom_rules_store = [r for r in custom_rules_store if r["func_name"] != data["func_name"]]
    custom_rules_store.append(data)
    return {"status": "saved", "total_rules": len(custom_rules_store)}


@app.get("/rules/list")
async def list_rules():
    return {
        "rules": [
            {"func_name": r["func_name"], "rule_description": r["rule_description"]}
            for r in custom_rules_store
        ]
    }


@app.delete("/rules/{func_name}")
async def delete_rule(func_name: str):
    global custom_rules_store
    custom_rules_store = [r for r in custom_rules_store if r["func_name"] != func_name]
    return {"status": "deleted", "total_rules": len(custom_rules_store)}
