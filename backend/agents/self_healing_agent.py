from openai import OpenAI
import os
import traceback
import json
from datetime import datetime
from persistence import memory_store
from persistence.audit_db import save_healing_event

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY")
)


def _load_healing() -> dict:
    data = memory_store.load("healing_log")
    if not isinstance(data, dict):
        data = {}
    if "events" not in data:
        data["events"] = []
    if "known_errors" not in data:
        data["known_errors"] = {}
    return data


def create_error_signature(error: Exception, context: dict) -> str:
    import hashlib
    sig = f"{type(error).__name__}:{str(error)[:50]}"
    return hashlib.md5(sig.encode()).hexdigest()[:8]


def analyze_error_with_llm(error: Exception, failed_check: str, input_data: dict) -> dict:
    error_trace = traceback.format_exc()
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b:free",
        max_tokens=400,
        messages=[
            {"role": "system", "content": "You are a self-healing agent for an identity verification system. Analyze errors and propose specific fixes. Be concise and technical."},
            {"role": "user", "content": f"""A verification check failed with an error.

Failed Check: {failed_check}
Error Type: {type(error).__name__}
Error Message: {str(error)}
Input Data: {str(input_data)[:500]}

Error Traceback:
{error_trace[:800]}

Respond with a JSON object:
{{
  "root_cause": "one sentence — what caused this error",
  "error_category": "FORMAT_ERROR|NULL_VALUE|TYPE_MISMATCH|ENCODING|THRESHOLD|UNKNOWN",
  "affected_field": "which field caused the problem",
  "proposed_fix": "specific code change or logic update needed",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "auto_fixable": true or false,
  "fix_code": "if auto_fixable, the exact Python snippet to fix it"
}}

JSON only, no markdown."""}
        ]
    )
    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {
            "root_cause": str(error),
            "error_category": "UNKNOWN",
            "affected_field": "unknown",
            "proposed_fix": "Manual investigation required",
            "severity": "HIGH",
            "auto_fixable": False,
            "fix_code": None
        }


def heal_check(check_name: str, check_func, profile: dict, *args) -> dict:
    try:
        return check_func(*args)
    except Exception as e:
        sig = create_error_signature(e, {"check": check_name})
        analysis = analyze_error_with_llm(e, check_name, {"args": str(args)[:200]})

        healing_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_signature": sig,
            "check_name": check_name,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "analysis": analysis,
            "healed": True,
            "fallback_used": "safe_default"
        }

        data = _load_healing()
        data["events"] = data.get("events", [])[-99:] + [healing_entry]
        if sig not in data["known_errors"]:
            data["known_errors"][sig] = {"count": 0, "analysis": analysis, "check_name": check_name}
        data["known_errors"][sig]["count"] += 1
        memory_store.save("healing_log", data)

        try:
            save_healing_event(
                check_name=check_name,
                error_type=type(e).__name__,
                error_message=str(e),
                root_cause=analysis.get("root_cause", ""),
                proposed_fix=analysis.get("proposed_fix", ""),
                auto_fixable=bool(analysis.get("auto_fixable", False)),
            )
        except Exception:
            pass

        return {
            "check": check_name,
            "input_a": str(args[0]) if args else "unknown",
            "input_b": str(args[1]) if len(args) > 1 else "unknown",
            "result": "soft_fail",
            "reason": (
                f"[Self-Healed] Check encountered an error: {analysis['root_cause']}. "
                f"Proposed fix: {analysis['proposed_fix']}. Flagged for review."
            ),
            "healed": True,
            "error_signature": sig,
            "severity": analysis["severity"]
        }


def get_healing_log() -> dict:
    data = _load_healing()
    return {
        "total_healed": len(data.get("events", [])),
        "unique_error_patterns": len(data.get("known_errors", {})),
        "healing_log": data.get("events", [])[-20:],
        "known_errors": [
            {
                "signature": sig,
                "check_name": d["check_name"],
                "count": d["count"],
                "root_cause": d["analysis"]["root_cause"],
                "proposed_fix": d["analysis"]["proposed_fix"],
                "auto_fixable": d["analysis"]["auto_fixable"],
                "severity": d["analysis"]["severity"]
            }
            for sig, d in data.get("known_errors", {}).items()
        ]
    }
