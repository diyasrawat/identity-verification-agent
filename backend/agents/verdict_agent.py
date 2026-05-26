import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)


def run_verdict_agent(
    identity_result: dict,
    address_result: dict,
    fraud_result: dict,
    confidence_score: dict,
    profile: dict,
) -> dict:
    fraud_score = fraud_result.get("fraud_score", 0)
    identity_verdict = identity_result.get("verdict", "CLEAN")
    address_verdict = address_result.get("verdict", "CONSISTENT")
    conf_score = confidence_score.get("score", 100)

    if fraud_score >= 60 or identity_verdict == "HARD BLOCK":
        final_verdict, verdict_color = "REJECT", "red"
    elif (
        fraud_score >= 30
        or identity_verdict == "SOFT ISSUES — HUMAN REVIEW"
        or address_verdict == "CONFLICTING"
    ):
        final_verdict, verdict_color = "REVIEW", "yellow"
    else:
        final_verdict, verdict_color = "PROCEED", "green"

    checks = identity_result.get("checks", [])
    failed_checks = [c for c in checks if c.get("result") != "pass"]

    failed_summary = (
        "\n".join(
            f"- {c['check']}: {c['result']} — {c.get('reason', '')}"
            for c in failed_checks
        )
        if failed_checks
        else "All identity checks passed."
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b:free",
        max_tokens=300,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior underwriting agent at FlexiLoans. "
                    "Write clear, professional underwriter notes. Be specific."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Write underwriter notes for this loan file.\n\n"
                    f"Applicant: {profile.get('applicant_id', 'UNKNOWN')}\n"
                    f"Final Decision: {final_verdict}\n"
                    f"Identity Verdict: {identity_verdict}\n"
                    f"Address Verdict: {address_verdict}\n"
                    f"Fraud Risk: {fraud_result.get('risk_level')} ({fraud_score}/100)\n"
                    f"Confidence Score: {conf_score}%\n\n"
                    f"Failed Checks:\n{failed_summary}\n\n"
                    f"Address Analysis: {address_result.get('agent_analysis', 'N/A')}\n"
                    f"Fraud Analysis: {fraud_result.get('fraud_narrative', 'N/A')}\n\n"
                    f"Write professional underwriter notes in 3 parts:\n"
                    f"1. SUMMARY (1 sentence): Overall assessment\n"
                    f"2. KEY FINDINGS (2-3 bullet points): Most important issues\n"
                    f"3. RECOMMENDED ACTION (1 sentence): What to do next\n\n"
                    f"Use professional lending terminology."
                ),
            },
        ],
    )

    return {
        "agent": "verdict",
        "status": "complete",
        "final_verdict": final_verdict,
        "verdict_color": verdict_color,
        "underwriter_notes": response.choices[0].message.content,
        "decision_factors": {
            "identity_verdict": identity_verdict,
            "address_verdict": address_verdict,
            "fraud_score": fraud_score,
            "confidence_score": conf_score,
        },
    }
