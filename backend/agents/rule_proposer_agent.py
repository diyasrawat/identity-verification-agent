from datetime import datetime
from openai import OpenAI
import os
from persistence import memory_store
from persistence.audit_db import save_proposal

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY")
)

PROPOSAL_THRESHOLD = 3


def _load_proposals() -> dict:
    data = memory_store.load("proposals")
    if not isinstance(data, dict):
        data = {}
    for key in ["pending", "approved", "rejected"]:
        if key not in data:
            data[key] = []
    return data


def _save_proposals(data: dict):
    memory_store.save("proposals", data)


def analyze_and_propose(pattern_memory: dict) -> list:
    proposals_data = _load_proposals()
    all_existing = proposals_data["pending"] + proposals_data["approved"]
    proposals = []

    for fmt, count in pattern_memory["date_formats"].items():
        if count >= PROPOSAL_THRESHOLD and fmt not in ["YYYY-MM-DD", "empty", "UNKNOWN_FORMAT"]:
            if not any(p.get("trigger_pattern") == fmt for p in all_existing):
                proposals.append({
                    "type": "DATE_FORMAT_HANDLER",
                    "trigger_pattern": fmt,
                    "observation": f"Date format '{fmt}' seen {count} times across {pattern_memory['total_runs']} runs",
                    "proposed_action": f"Add explicit handler for {fmt} format in normalize_date()",
                    "priority": "HIGH" if count > 5 else "MEDIUM",
                    "auto_generate": True
                })

    initial_count = pattern_memory["name_patterns"].get("INITIAL_FIRST_NAME", 0)
    if initial_count >= PROPOSAL_THRESHOLD:
        if not any(p.get("trigger_pattern") == "INITIAL_FIRST_NAME" for p in all_existing):
            proposals.append({
                "type": "NAME_THRESHOLD_ADJUSTMENT",
                "trigger_pattern": "INITIAL_FIRST_NAME",
                "observation": f"Initial name pattern (e.g. 'P. Kumar') seen {initial_count} times. These consistently cause soft fails that get approved.",
                "proposed_action": "Lower soft-fail threshold for single initial patterns from 55% to 45% when last name matches",
                "priority": "MEDIUM",
                "auto_generate": True
            })

    for pattern, count in pattern_memory.get("typo_frequency", {}).items():
        typo = pattern.replace("typo:", "")
        if count >= PROPOSAL_THRESHOLD:
            if not any(p.get("trigger_pattern") == pattern for p in all_existing):
                proposals.append({
                    "type": "TYPO_CORRECTION_RULE",
                    "trigger_pattern": pattern,
                    "observation": f"Typo '{typo}' seen {count} times in input data",
                    "proposed_action": f"Add '{typo}' to the typo correction dictionary in normalize_date()",
                    "priority": "HIGH",
                    "auto_generate": True
                })

    for check_name, count in pattern_memory["hard_fail_patterns"].items():
        if count >= PROPOSAL_THRESHOLD * 2:
            key = f"hard_fail:{check_name}"
            if not any(p.get("trigger_pattern") == key for p in all_existing):
                proposals.append({
                    "type": "SYSTEMATIC_HARD_FAIL",
                    "trigger_pattern": key,
                    "observation": f"'{check_name}' is hard failing {count} times — possible systematic data issue",
                    "proposed_action": f"Review if '{check_name}' threshold should be relaxed or if data source has quality issues",
                    "priority": "HIGH",
                    "auto_generate": False
                })

    return proposals


async def generate_rule_code_for_proposal(proposal: dict) -> str:
    response = client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",
        max_tokens=600,
        messages=[
            {"role": "system", "content": "You are a code generation agent for an identity verification system. Generate only raw Python code, no markdown."},
            {"role": "user", "content": f"""Generate a Python improvement for this self-identified pattern:

Type: {proposal['type']}
Observation: {proposal['observation']}
Proposed Action: {proposal['proposed_action']}

Output format — a Python dict describing the change:
{{
  "change_type": "typo_map_entry" | "format_addition" | "new_function",
  "description": "what this change does",
  "code": "the actual code/value to add",
  "location": "which file and where to add it"
}}

Respond with valid Python dict only."""}
        ]
    )
    return response.choices[0].message.content


def add_proposal(proposal: dict) -> dict:
    data = _load_proposals()
    total = len(data["pending"]) + len(data["approved"]) + len(data["rejected"])
    proposal["id"] = f"PROP-{total + 1:04d}"
    proposal["status"] = "pending"
    proposal["created_at"] = datetime.now().isoformat()
    data["pending"].append(proposal)
    _save_proposals(data)
    try:
        save_proposal(proposal)
    except Exception:
        pass
    return proposal


def approve_proposal(proposal_id: str) -> dict:
    data = _load_proposals()
    for p in data["pending"]:
        if p["id"] == proposal_id:
            p["status"] = "approved"
            p["approved_at"] = datetime.now().isoformat()
            data["pending"].remove(p)
            data["approved"].append(p)
            _save_proposals(data)
            try:
                save_proposal(p)
            except Exception:
                pass
            return p
    return {"error": "Proposal not found"}


def reject_proposal(proposal_id: str) -> dict:
    data = _load_proposals()
    for p in data["pending"]:
        if p["id"] == proposal_id:
            p["status"] = "rejected"
            p["rejected_at"] = datetime.now().isoformat()
            data["pending"].remove(p)
            data["rejected"].append(p)
            _save_proposals(data)
            return p
    return {"error": "Proposal not found"}


def get_all_proposals() -> dict:
    data = _load_proposals()
    return {
        "pending": data["pending"],
        "approved": data["approved"],
        "rejected": data["rejected"],
        "total_pending": len(data["pending"]),
        "total_approved": len(data["approved"]),
    }
