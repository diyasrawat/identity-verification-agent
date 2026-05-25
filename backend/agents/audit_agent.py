from datetime import datetime

audit_store = []


def log_audit(orchestration_result: dict, profile: dict) -> dict:
    checks = orchestration_result.get("checks", [])
    entry = {
        "audit_id": f"AUD-{len(audit_store)+1:04d}",
        "timestamp": datetime.now().isoformat(),
        "applicant_id": profile.get("applicant_id", "UNKNOWN"),
        "agents_run": [
            r.get("agent")
            for r in orchestration_result.get("agent_results", {}).values()
            if isinstance(r, dict) and r.get("agent")
        ],
        "final_verdict": orchestration_result.get("final_verdict", {}).get("final_verdict"),
        "fraud_score": orchestration_result.get("fraud_result", {}).get("fraud_score"),
        "confidence_score": orchestration_result.get("confidence_score", {}).get("score"),
        "identity_verdict": orchestration_result.get("identity_verdict"),
        "address_verdict": orchestration_result.get("address_result", {}).get("verdict"),
        "checks_run": len(checks),
        "hard_fails": len([c for c in checks if c.get("result") == "hard_fail"]),
        "soft_fails": len([c for c in checks if c.get("result") == "soft_fail"]),
        "rules_applied": orchestration_result.get("rules_applied", 0),
    }
    audit_store.append(entry)
    return entry


def get_audit_log() -> list:
    return audit_store
