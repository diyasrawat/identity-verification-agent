import re
from rapidfuzz import fuzz


def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.upper().strip()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name


def normalize_date(date_str: str) -> str:
    if not date_str:
        return ""

    from datetime import datetime

    date_str = str(date_str).strip()

    formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%Y-%d-%m", "%Y/%d/%m",
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
        "%m-%d-%Y", "%m/%d/%Y", "%m.%d.%Y",
        "%d-%m-%y", "%d/%m/%y", "%m-%d-%y", "%m/%d/%y",
        "%y-%m-%d", "%y/%m/%d",
        "%d %B %Y", "%B %d %Y", "%d %B, %Y", "%B %d, %Y",
        "%Y %B %d", "%Y %d %B",
        "%d %b %Y", "%b %d %Y", "%d %b, %Y", "%b %d, %Y", "%Y %b %d",
    ]

    cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str, flags=re.IGNORECASE)

    typo_map = {
        "arpil": "april", "apirl": "april", "apri": "april",
        "januray": "january", "janury": "january",
        "feburary": "february", "febuary": "february",
        "marh": "march", "mrach": "march",
        "auguest": "august", "auguts": "august",
        "septembar": "september", "septmber": "september",
        "octuber": "october", "octobr": "october",
        "novembar": "november", "novembe": "november",
        "decembar": "december", "decmber": "december",
    }
    cleaned_lower = cleaned.lower()
    for typo, correct in typo_map.items():
        cleaned_lower = cleaned_lower.replace(typo, correct)
    cleaned = cleaned_lower

    for date_input in [cleaned, date_str.lower()]:
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_input.strip(), fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

    try:
        from dateutil import parser as dateparser
        parsed = dateparser.parse(cleaned, dayfirst=True)
        if parsed:
            return parsed.strftime("%Y-%m-%d")
    except:
        pass

    return date_str.strip()


def is_initial_match(name_a: str, name_b: str) -> bool:
    """Return True if one name is an initial abbreviation of the other.
    e.g. 'P KUMAR' vs 'PRASHANT KUMAR' → True (last name matches, first is initial)
    e.g. 'R PANDEY' vs 'RAMESH KUMAR' → False (last names differ)
    """
    tokens_a = name_a.upper().replace('.', '').split()
    tokens_b = name_b.upper().replace('.', '').split()

    if not tokens_a or not tokens_b:
        return False

    if tokens_a[-1] != tokens_b[-1]:
        return False

    short = tokens_a if len(tokens_a) <= len(tokens_b) else tokens_b
    long  = tokens_b if len(tokens_a) <= len(tokens_b) else tokens_a

    if len(short[0]) == 1 and long[0].startswith(short[0]):
        return True

    return False


def check_pan_format(pan_number):
    pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
    passed = bool(re.match(pattern, str(pan_number).upper()))
    return {
        "check": "PAN Format",
        "input_a": pan_number,
        "input_b": None,
        "result": "pass" if passed else "hard_fail",
        "reason": None if passed else f"PAN '{pan_number}' does not match required format AAAAA9999A",
    }


def check_dob(dob_a: str, dob_b: str, label_a="PAN", label_b="Aadhaar") -> dict:
    norm_a = normalize_date(dob_a)
    norm_b = normalize_date(dob_b)
    match = norm_a == norm_b
    return {
        "check": f"Date of Birth ({label_a} vs {label_b})",
        "input_a": f"{label_a}: '{dob_a}' → normalized: '{norm_a}'",
        "input_b": f"{label_b}: '{dob_b}' → normalized: '{norm_b}'",
        "result": "pass" if match else "hard_fail",
        "reason": (
            f"DOB matches after normalization: both are {norm_a}."
            if match else
            f"DOB mismatch after normalization — {label_a}: '{norm_a}', {label_b}: '{norm_b}'. Hard block."
        ),
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
    norm_a = normalize_name(name_a)
    norm_b = normalize_name(name_b)
    score = fuzz.token_sort_ratio(norm_a, norm_b)

    # Initial abbreviation pattern takes priority
    if is_initial_match(norm_a, norm_b):
        return {
            "check": f"Name Match ({label_a} vs {label_b})",
            "input_a": f"{label_a}: {name_a}",
            "input_b": f"{label_b}: {name_b}",
            "result": "soft_fail",
            "reason": None,  # LLM will explain
            "fuzzy_score": round(score),
        }

    if score >= 85:
        result = "pass"
        reason = f"Names match with {round(score)}% similarity."
    elif score >= 55:
        result = "soft_fail"
        reason = None  # LLM explains
    else:
        result = "hard_fail"
        reason = (
            f"Names too different — '{name_a}' vs '{name_b}' "
            f"(similarity: {round(score)}%). "
            f"Last names may differ — this is a hard block."
        )

    return {
        "check": f"Name Match ({label_a} vs {label_b})",
        "input_a": f"{label_a}: {name_a}",
        "input_b": f"{label_b}: {name_b}",
        "result": result,
        "reason": reason,
        "fuzzy_score": round(score),
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
