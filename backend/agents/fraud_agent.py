import os
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)


def run_fraud_agent(identity_result: dict, address_result: dict, profile: dict) -> dict:
    checks = identity_result.get("checks", [])
    hard_fails = [c for c in checks if c.get("result") == "hard_fail"]
    soft_fails = [c for c in checks if c.get("result") == "soft_fail"]

    addr_verdict = address_result.get("verdict", "CONSISTENT")
    addr_conflicts = address_result.get("conflicts", [])

    fraud_signals = []
    fraud_score = 0

    # Signal 1: DOB hard fail
    dob_fail = any(
        "Date of Birth" in c.get("check", "") and c.get("result") == "hard_fail"
        for c in checks
    )
    if dob_fail:
        fraud_signals.append({
            "signal": "DOB_HARD_MISMATCH",
            "weight": 40,
            "detail": "Date of birth mismatch across documents — strongest fraud indicator",
        })
        fraud_score += 40

    # Signal 2: Multiple name fails
    name_fails = [c for c in checks if "Name" in c.get("check", "") and c.get("result") != "pass"]
    if len(name_fails) >= 2:
        fraud_signals.append({
            "signal": "MULTIPLE_NAME_MISMATCHES",
            "weight": 25,
            "detail": f"{len(name_fails)} name checks failed — pattern suggests identity substitution",
        })
        fraud_score += 25

    # Signal 3: Address + identity cluster
    if addr_verdict == "CONFLICTING" and (hard_fails or len(soft_fails) >= 2):
        fraud_signals.append({
            "signal": "ADDRESS_IDENTITY_CLUSTER",
            "weight": 30,
            "detail": "Address conflict combined with identity mismatches — strongest combined fraud pattern",
        })
        fraud_score += 30

    # Signal 4: Pincode mismatch
    pincode_conflicts = [c for c in addr_conflicts if c.get("type") == "PINCODE_MISMATCH"]
    if pincode_conflicts:
        fraud_signals.append({
            "signal": "PINCODE_MISMATCH",
            "weight": 20,
            "detail": f"{len(pincode_conflicts)} pincode mismatch(es) — genuinely different locations",
        })
        fraud_score += 20

    # Signal 5: High soft fail count
    if len(soft_fails) >= 3:
        fraud_signals.append({
            "signal": "HIGH_SOFT_FAIL_COUNT",
            "weight": 15,
            "detail": f"{len(soft_fails)} soft fails — could be data entry errors or coordinated manipulation",
        })
        fraud_score += 15

    fraud_score = min(fraud_score, 100)

    if fraud_score >= 60:
        risk_level, risk_color = "HIGH", "red"
    elif fraud_score >= 30:
        risk_level, risk_color = "MEDIUM", "yellow"
    else:
        risk_level, risk_color = "LOW", "green"

    fraud_narrative = None
    if fraud_score >= 30:
        signals_text = "\n".join(
            f"- {s['signal']} (weight: {s['weight']}): {s['detail']}"
            for s in fraud_signals
        )
        response = client.chat.completions.create(
            model="anthropic/claude-haiku-4-5",
            max_tokens=200,
            messages=[
                {
                    "role": "system",
                    "content": "You are a fraud detection agent for an Indian lending company. Be direct and specific.",
                },
                {
                    "role": "user",
                    "content": (
                        f"Fraud signals detected for loan applicant {profile.get('applicant_id', 'UNKNOWN')}:\n\n"
                        f"{signals_text}\n\n"
                        f"Fraud risk score: {fraud_score}/100 ({risk_level} RISK)\n\n"
                        f"In 2 sentences: What fraud pattern does this most likely represent? "
                        f"What specific action should the underwriter take immediately?"
                    ),
                },
            ],
        )
        fraud_narrative = response.choices[0].message.content
    else:
        fraud_narrative = "No significant fraud signals detected. Minor variations consistent with data entry differences."

    return {
        "agent": "fraud",
        "status": "complete",
        "fraud_score": fraud_score,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "fraud_signals": fraud_signals,
        "fraud_narrative": fraud_narrative,
    }
