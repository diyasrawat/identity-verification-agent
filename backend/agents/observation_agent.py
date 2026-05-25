from datetime import datetime
from collections import defaultdict
import re
from persistence import memory_store


def _load_memory() -> dict:
    data = memory_store.load("pattern_memory")
    # Ensure all required keys exist
    for key in ["date_formats", "name_patterns", "address_patterns",
                "soft_fail_patterns", "hard_fail_patterns", "override_patterns"]:
        if key not in data:
            data[key] = {}
    if "total_runs" not in data:
        data["total_runs"] = 0
    if "observations" not in data:
        data["observations"] = []
    return data


def detect_date_format(date_str: str) -> str:
    if not date_str:
        return "empty"

    patterns = [
        (r'^\d{4}-\d{2}-\d{2}$', 'YYYY-MM-DD'),
        (r'^\d{4}/\d{2}/\d{2}$', 'YYYY/MM/DD'),
        (r'^\d{2}-\d{2}-\d{4}$', 'DD-MM-YYYY'),
        (r'^\d{2}/\d{2}/\d{4}$', 'DD/MM/YYYY'),
        (r'.*\d+(st|nd|rd|th).*', 'ORDINAL_SUFFIX'),
        (r'.*[a-zA-Z]{3,}.*\d{4}', 'MONTH_NAME'),
        (r'^\d{2}-\d{2}-\d{2}$', 'SHORT_YEAR'),
        (r'^\d{4}\s+\w+\s+\d+', 'YYYY_MONTHNAME_DD'),
    ]

    for pattern, label in patterns:
        if re.match(pattern, str(date_str).strip(), re.IGNORECASE):
            return label
    return "UNKNOWN_FORMAT"


def detect_name_pattern(name: str) -> str:
    if not name:
        return "empty"
    tokens = name.strip().split()
    if not tokens:
        return "empty"
    if len(tokens[0].replace('.', '')) == 1:
        return "INITIAL_FIRST_NAME"
    initials = [t for t in tokens if len(t.replace('.', '')) == 1]
    if len(initials) > 1:
        return "MULTIPLE_INITIALS"
    if len(tokens) == 1:
        return "SINGLE_WORD"
    return "FULL_NAME"


def detect_typos(text: str) -> list:
    known_typos = {
        "arpil": "april", "apirl": "april",
        "januray": "january", "feburary": "february",
        "marh": "march", "septembar": "september",
        "octuber": "october", "novembar": "november",
        "decembar": "december"
    }
    found = []
    text_lower = text.lower()
    for typo, correct in known_typos.items():
        if typo in text_lower:
            found.append({"typo": typo, "correct": correct, "field": text})
    return found


def observe_verification(profile: dict, checks: list, verdict: str) -> dict:
    mem = _load_memory()
    mem["total_runs"] += 1

    observation = {
        "timestamp": datetime.now().isoformat(),
        "applicant_id": profile.get("applicant_id"),
        "verdict": verdict,
        "patterns_found": [],
        "typos_found": [],
        "format_anomalies": []
    }

    pan_dob = profile.get("pan", {}).get("dob", "")
    aadhaar_dob = profile.get("aadhaar", {}).get("dob", "")

    pan_fmt = detect_date_format(pan_dob)
    aadhaar_fmt = detect_date_format(aadhaar_dob)

    mem["date_formats"][pan_fmt] = mem["date_formats"].get(pan_fmt, 0) + 1
    mem["date_formats"][aadhaar_fmt] = mem["date_formats"].get(aadhaar_fmt, 0) + 1

    if pan_fmt != "YYYY-MM-DD":
        observation["format_anomalies"].append({"field": "pan.dob", "raw": pan_dob, "format": pan_fmt})

    pan_name = profile.get("pan", {}).get("name", "")
    pan_name_pattern = detect_name_pattern(pan_name)
    mem["name_patterns"][pan_name_pattern] = mem["name_patterns"].get(pan_name_pattern, 0) + 1

    observation["patterns_found"].append({"field": "pan.name", "pattern": pan_name_pattern, "value": pan_name})

    all_text_fields = [
        pan_dob, aadhaar_dob, pan_name,
        profile.get("aadhaar", {}).get("name", ""),
        profile.get("pan", {}).get("father_name", ""),
        profile.get("aadhaar", {}).get("father_name", "")
    ]

    for field_text in all_text_fields:
        typos = detect_typos(str(field_text))
        observation["typos_found"].extend(typos)
        for typo in typos:
            key = f"typo:{typo['typo']}"
            mem["soft_fail_patterns"][key] = mem["soft_fail_patterns"].get(key, 0) + 1

    for check in checks:
        if check.get("result") == "soft_fail":
            pattern = detect_name_pattern(check.get("input_a", "").split(":")[-1].strip())
            mem["soft_fail_patterns"][pattern] = mem["soft_fail_patterns"].get(pattern, 0) + 1
        elif check.get("result") == "hard_fail":
            key = check.get("check", "unknown")
            mem["hard_fail_patterns"][key] = mem["hard_fail_patterns"].get(key, 0) + 1

    mem["observations"] = mem.get("observations", [])[-49:] + [observation]
    mem["last_updated"] = datetime.now().isoformat()
    memory_store.save("pattern_memory", mem)
    return observation


def get_pattern_memory() -> dict:
    mem = _load_memory()
    return {
        "total_runs": mem["total_runs"],
        "date_formats": mem["date_formats"],
        "name_patterns": mem["name_patterns"],
        "soft_fail_patterns": mem["soft_fail_patterns"],
        "hard_fail_patterns": mem["hard_fail_patterns"],
        "recent_observations": mem.get("observations", [])[-10:],
        "typo_frequency": {
            k: v for k, v in mem["soft_fail_patterns"].items()
            if k.startswith("typo:")
        }
    }
