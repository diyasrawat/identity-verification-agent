import re
from rapidfuzz import fuzz


def check_pan_format(pan_number):
    pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
    passed = bool(re.match(pattern, pan_number))
    return {
        "check": "PAN Format",
        "input_a": pan_number,
        "input_b": None,
        "result": "pass" if passed else "hard_fail",
        "reason": None if passed else f"PAN '{pan_number}' does not match required format AAAAA9999A",
    }


def check_dob(dob_pan, dob_aadhaar):
    passed = dob_pan == dob_aadhaar
    return {
        "check": "DOB (PAN vs Aadhaar)",
        "input_a": dob_pan,
        "input_b": dob_aadhaar,
        "result": "pass" if passed else "hard_fail",
        "reason": None if passed else f"DOB mismatch: PAN has '{dob_pan}', Aadhaar has '{dob_aadhaar}'",
    }


def check_gender(gender_pan, gender_aadhaar):
    passed = gender_pan == gender_aadhaar
    return {
        "check": "Gender (PAN vs Aadhaar)",
        "input_a": gender_pan,
        "input_b": gender_aadhaar,
        "result": "pass" if passed else "hard_fail",
        "reason": None if passed else f"Gender mismatch: PAN has '{gender_pan}', Aadhaar has '{gender_aadhaar}'",
    }


def check_aadhaar_last4(bureau_last4, aadhaar_last4):
    passed = str(bureau_last4) == str(aadhaar_last4)
    return {
        "check": "Aadhaar Last 4 (Bureau vs Aadhaar)",
        "input_a": bureau_last4,
        "input_b": aadhaar_last4,
        "result": "pass" if passed else "hard_fail",
        "reason": None if passed else f"Aadhaar last-4 mismatch: Bureau has '{bureau_last4}', Aadhaar has '{aadhaar_last4}'",
    }


def check_name_fuzzy(name_a, name_b, label_a, label_b):
    score = fuzz.token_sort_ratio(name_a.lower(), name_b.lower())

    if score >= 85:
        result = "pass"
        reason = None
    elif score >= 70:
        result = "soft_fail"
        reason = None  # LLM will fill later
    else:
        result = "hard_fail"
        reason = f"Name mismatch too large: {label_a} has '{name_a}', {label_b} has '{name_b}' (score: {score})"

    return {
        "check": f"Name ({label_a} vs {label_b})",
        "input_a": name_a,
        "input_b": name_b,
        "result": result,
        "reason": reason,
        "fuzzy_score": score,
    }


def check_father_name(fname_pan, fname_aadhaar):
    result = check_name_fuzzy(fname_pan, fname_aadhaar, "PAN", "Aadhaar")
    result["check"] = "Father Name (PAN vs Aadhaar)"
    return result


def compute_overall_verdict(checks):
    results = [c["result"] for c in checks]
    if "hard_fail" in results:
        return "HARD BLOCK"
    if "soft_fail" in results:
        return "SOFT ISSUES — HUMAN REVIEW"
    return "CLEAN"
