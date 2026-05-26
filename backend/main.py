import re
from dotenv import load_dotenv
load_dotenv()

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
from agents.orchestrator import run_orchestrator
from agents.audit_agent import get_audit_log
from agents.observation_agent import observe_verification, get_pattern_memory
from agents.rule_proposer_agent import (
    analyze_and_propose, add_proposal, approve_proposal,
    reject_proposal, get_all_proposals, generate_rule_code_for_proposal,
)
from persistence import memory_store
from persistence.audit_db import (
    init_db, save_verification, save_test_session,
    get_verifications, get_verification_checks, get_test_sessions, get_db_stats,
)

init_db()

app = FastAPI(title="Identity Cross-Verification Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_custom_rules() -> list:
    data = memory_store.load("custom_rules")
    return data if isinstance(data, list) else []


def _save_custom_rules(rules: list):
    memory_store.save("custom_rules", rules)

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
    for rule in _load_custom_rules():
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

    pass_threshold = int(data.get("pass_threshold", 85))
    soft_threshold = int(data.get("soft_threshold", 55))
    initial_leniency = bool(data.get("initial_leniency", True))

    # Test session metadata (optional)
    test_case_name = data.get("test_case_name", "")
    test_category = data.get("test_category", "manual")
    session_id = data.get("session_id", "")

    raw_pan_dob = pan.get("dob", "")
    raw_aadhaar_dob = aadhaar.get("dob", "")

    checks = [
        check_pan_format(pan.get("number", "")),
        check_dob(raw_pan_dob, raw_aadhaar_dob),
        check_gender(pan.get("gender", ""), aadhaar.get("gender", "")),
        check_aadhaar_last4(bureau.get("aadhaar_last4", ""), aadhaar.get("last4", "")),
        check_name_fuzzy(pan.get("name", ""), aadhaar.get("name", ""), "PAN", "Aadhaar",
                         pass_threshold, soft_threshold, initial_leniency),
        check_name_fuzzy(bureau.get("name", ""), pan.get("name", ""), "Bureau", "PAN",
                         pass_threshold, soft_threshold, initial_leniency),
        check_father_name(pan.get("father_name", ""), aadhaar.get("father_name", ""),
                          pass_threshold, soft_threshold, initial_leniency),
    ]

    for check in checks:
        if check["result"] == "soft_fail" and check.get("reason") is None:
            check["reason"] = explain_soft_fail(
                check["check"], check["input_a"], check["input_b"]
            )

    run_custom_rules(checks, data)

    verdict = compute_overall_verdict(checks)
    confidence = compute_confidence_score(checks)

    # Persist test session if named
    if test_case_name or session_id:
        try:
            save_test_session(
                session_id=session_id,
                test_case_name=test_case_name,
                test_category=test_category,
                verdict=verdict,
                confidence=confidence,
                checks=checks,
                pass_threshold=pass_threshold,
                soft_threshold=soft_threshold,
                initial_leniency=initial_leniency,
            )
        except Exception:
            pass

    return {
        "checks": checks,
        "verdict": verdict,
        "confidence_score": confidence,
        "mode": "live_test",
        "thresholds_used": {
            "pass_threshold": pass_threshold,
            "soft_threshold": soft_threshold,
            "initial_leniency": initial_leniency,
        },
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
    rules = _load_custom_rules()
    rules = [r for r in rules if r["func_name"] != data["func_name"]]
    rules.append(data)
    _save_custom_rules(rules)
    return {"status": "saved", "total_rules": len(rules)}


@app.get("/rules/list")
async def list_rules():
    rules = _load_custom_rules()
    return {
        "rules": [
            {"func_name": r["func_name"], "rule_description": r["rule_description"]}
            for r in rules
        ]
    }


@app.delete("/rules/{func_name}")
async def delete_rule(func_name: str):
    rules = _load_custom_rules()
    rules = [r for r in rules if r["func_name"] != func_name]
    _save_custom_rules(rules)
    return {"status": "deleted", "total_rules": len(rules)}


# ── Orchestrator endpoint ──────────────────────────────────────────────────────

@app.post("/orchestrate")
async def orchestrate(data: dict):
    result = await run_orchestrator(data, custom_rules=_load_custom_rules())

    # Observe this run silently
    observation = observe_verification(
        data,
        result.get("checks", []),
        result.get("identity_verdict", "")
    )

    # Check if patterns warrant new proposals
    memory = get_pattern_memory()
    new_proposals = analyze_and_propose(memory)
    for proposal in new_proposals:
        add_proposal(proposal)

    # Persist this verification to SQLite
    try:
        save_verification(
            applicant_id=data.get("applicant_id", "unknown"),
            verdict=result.get("identity_verdict", ""),
            confidence=result.get("confidence_score", {}),
            checks=result.get("checks", []),
            mode="orchestrate",
            source_file=data.get("applicant_id"),
            pipeline_steps=result.get("pipeline_steps", []),
        )
    except Exception:
        pass

    result["observation"] = observation
    result["new_proposals_generated"] = len(new_proposals)

    return result


# ── Audit endpoint ─────────────────────────────────────────────────────────────

@app.get("/audit")
async def audit_log():
    return {"entries": get_audit_log()}


# ── Self-improving agent endpoints ─────────────────────────────────────────────

@app.get("/self-improve/memory")
async def get_memory():
    return get_pattern_memory()


@app.get("/self-improve/proposals")
async def get_proposals():
    return get_all_proposals()


@app.post("/self-improve/proposals/{proposal_id}/approve")
async def approve(proposal_id: str):
    proposal = approve_proposal(proposal_id)
    if proposal.get("auto_generate"):
        code = await generate_rule_code_for_proposal(proposal)
        proposal["generated_code"] = code
    return proposal


@app.post("/self-improve/proposals/{proposal_id}/reject")
async def reject(proposal_id: str):
    return reject_proposal(proposal_id)


@app.get("/healing/log")
async def get_healing():
    from agents.self_healing_agent import get_healing_log
    return get_healing_log()


@app.get("/evaluation/metrics")
async def get_metrics():
    import json, os as _os
    from evaluation.precision_recall import compute_precision_recall
    from agents.orchestrator import run_orchestrator

    actual_results = {}
    mock_dir = _os.path.join(_os.path.dirname(__file__), "mock_files")

    for filename in _os.listdir(mock_dir):
        if filename.endswith(".json"):
            with open(_os.path.join(mock_dir, filename)) as f:
                profile = json.load(f)
                result = await run_orchestrator(profile, [])
                actual_results[profile["applicant_id"]] = result

    return compute_precision_recall(actual_results)


@app.get("/self-improve/stats")
async def get_stats():
    memory = get_pattern_memory()
    proposals = get_all_proposals()
    return {
        "total_runs": memory["total_runs"],
        "patterns_discovered": len(memory["date_formats"]) + len(memory["name_patterns"]),
        "pending_proposals": proposals["total_pending"],
        "approved_proposals": proposals["total_approved"],
        "top_date_formats": sorted(
            memory["date_formats"].items(), key=lambda x: x[1], reverse=True
        )[:5],
        "top_name_patterns": sorted(
            memory["name_patterns"].items(), key=lambda x: x[1], reverse=True
        )[:5],
        "typos_caught": len(memory.get("typo_frequency", {}))
    }


# ── Memory & History endpoints ─────────────────────────────────────────────────

@app.get("/memory/stats")
async def memory_stats():
    json_stats = memory_store.get_stats()
    db_stats = get_db_stats()
    return {
        "json_files": json_stats,
        "sqlite": db_stats,
        "summary": {
            "total_verifications": db_stats["table_counts"].get("verifications", 0),
            "total_test_sessions": db_stats["table_counts"].get("test_sessions", 0),
            "total_healing_events": db_stats["table_counts"].get("healing_events", 0),
            "total_proposals": db_stats["table_counts"].get("proposals", 0),
        }
    }


@app.post("/memory/reset")
async def reset_memory(data: dict):
    key = data.get("key", "")
    if key in ["pattern_memory", "proposals", "healing_log", "custom_rules"]:
        memory_store.reset(key)
        return {"status": "reset", "key": key}
    return {"error": "Unknown key. Valid keys: pattern_memory, proposals, healing_log, custom_rules"}


@app.get("/history/verifications")
async def history_verifications(limit: int = 50):
    rows = get_verifications(limit)
    return {"verifications": rows, "count": len(rows)}


@app.get("/history/verifications/{verification_id}/checks")
async def history_checks(verification_id: int):
    checks = get_verification_checks(verification_id)
    return {"verification_id": verification_id, "checks": checks}


@app.get("/history/test-sessions")
async def history_test_sessions(limit: int = 100):
    sessions = get_test_sessions(limit)
    return {"sessions": sessions, "count": len(sessions)}


@app.get("/history/patterns")
async def history_patterns():
    return get_pattern_memory()


# ── Judge test cases endpoint ──────────────────────────────────────────────────

@app.post("/test/run-all-judge-cases")
async def run_all_judge_cases():
    from test_data.judge_test_cases import JUDGE_TEST_CASES
    import uuid

    session_id = f"judge-{uuid.uuid4().hex[:8]}"
    results = []

    for tc in JUDGE_TEST_CASES:
        pan = tc["pan"]
        aadhaar = tc["aadhaar"]
        bureau = tc["bureau"]

        checks = [
            check_pan_format(pan.get("number", "")),
            check_dob(pan.get("dob", ""), aadhaar.get("dob", "")),
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

        run_custom_rules(checks, tc)
        verdict = compute_overall_verdict(checks)
        confidence = compute_confidence_score(checks)
        expected = tc.get("expected_verdict", "")
        passed = verdict == expected

        try:
            save_test_session(
                session_id=session_id,
                test_case_name=tc["name"],
                test_category=tc["category"],
                verdict=verdict,
                confidence=confidence,
                checks=checks,
                pass_threshold=85,
                soft_threshold=55,
                initial_leniency=True,
            )
        except Exception:
            pass

        results.append({
            "name": tc["name"],
            "description": tc["description"],
            "expected_verdict": expected,
            "actual_verdict": verdict,
            "passed": passed,
            "confidence_score": confidence,
            "checks": checks,
        })

    total = len(results)
    correct = sum(1 for r in results if r["passed"])
    return {
        "session_id": session_id,
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total * 100, 1),
        "results": results,
    }
