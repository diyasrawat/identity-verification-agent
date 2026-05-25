import re
from rapidfuzz import fuzz


# ── ADD 1: Gender normalization graph ─────────────────────────────────────────

GENDER_GRAPH = {
    "M": ["M", "MALE", "1", "BOY", "MAN", "GENTS",
          "मेल", "पुरुष", "MASCULINE", "HE"],
    "F": ["F", "FEMALE", "2", "GIRL", "WOMAN",
          "LADIES", "महिला", "स्त्री", "FEMININE", "SHE"],
    "O": ["T", "TRANS", "TRANSGENDER", "OTHER", "3",
          "NONBINARY", "NON-BINARY"],
}


def normalize_gender(value: str) -> str:
    if not value:
        return "UNKNOWN"
    value_upper = str(value).upper().strip()
    for canonical, variants in GENDER_GRAPH.items():
        if value_upper in variants:
            return canonical
    return value_upper


# ── ADD 2: Aadhaar last-4 extraction ──────────────────────────────────────────

AADHAAR_MASKING_PATTERNS = [
    r'\d{4}$',
    r'[Xx\*]{4,8}[-\s]?(\d{4})',
    r'(\d{4})$',
]


def extract_aadhaar_last4(value: str) -> str:
    if not value:
        return ""
    digits = re.findall(r'\d', str(value))
    if len(digits) >= 4:
        return ''.join(digits[-4:])
    match = re.search(r'[Xx\*]{1,8}[-\s]?(\d{4})', str(value))
    if match:
        return match.group(1)
    return str(value).strip()


# ── ADD 3: PAN normalization ───────────────────────────────────────────────────

def normalize_pan(pan: str) -> str:
    if not pan:
        return ""
    pan = str(pan).upper().strip()
    pan = re.sub(r'[\s\-_]', '', pan)
    return pan


# ── ADD 4: Father name prefix stripping ───────────────────────────────────────

FATHER_PREFIX_GRAPH = [
    "LATE", "SH", "SHRI", "S/O", "D/O", "W/O",
    "C/O", "SON OF", "DAUGHTER OF", "WIFE OF",
    "F/O", "FATHER OF", "CARE OF",
]


def normalize_father_name(name: str) -> str:
    if not name:
        return ""
    name = normalize_name(name)
    tokens = name.split()
    while tokens and tokens[0] in FATHER_PREFIX_GRAPH:
        tokens = tokens[1:]
    return ' '.join(tokens)


# ── ADD 5: Transliteration graph ──────────────────────────────────────────────

TRANSLITERATION_GRAPH = {
    # South Indian name endings
    "PRASHANTH": "PRASHANT",
    "SIDDHARTH": "SIDDHARTHA",
    "SURESH": "SURESHA",
    "RAMESH": "RAMESHA",
    "PRAKASH": "PRAKASHA",
    "VENKATESH": "VENKATESHA",
    "RAJESH": "RAJESHA",
    # Common vowel variations
    "KUMAAR": "KUMAR",
    "RAJOO": "RAJU",
    "LAXMI": "LAKSHMI",
    "LAKSMI": "LAKSHMI",
    "BABU": "BABOO",
    # Common surname variants
    "SHARMA": "SARMA",
    "VERMA": "VARMA",
    "SINGH": "SING",
    "SINHA": "SINGH",
    "PANDEY": "PANDE",
    "MUKHERJEE": "MUKERJEE",
    "CHATTERJEE": "CHATERJEE",
    "BANNERJEE": "BANERJEE",
    # Mohammed variants — all normalize to MOHAMMAD
    "MOHAMMED": "MOHAMMAD",
    "MUHAMMED": "MOHAMMAD",
    "MOHAMAD": "MOHAMMAD",
    "MUHAMED": "MOHAMMAD",
    "MEHMED": "MOHAMMAD",
}


def apply_transliteration(name: str) -> str:
    name_upper = name.upper().strip()
    tokens = name_upper.split()
    normalized_tokens = []
    for token in tokens:
        canonical = TRANSLITERATION_GRAPH.get(token, token)
        # Reverse check: if this token appears as a value, keep it as-is
        for k, v in TRANSLITERATION_GRAPH.items():
            if v == token:
                canonical = v
                break
        normalized_tokens.append(canonical)
    return ' '.join(normalized_tokens)


def surnames_match(name_a: str, name_b: str) -> bool:
    tokens_a = name_a.upper().replace('.', '').split()
    tokens_b = name_b.upper().replace('.', '').split()
    if not tokens_a or not tokens_b:
        return False
    return fuzz.ratio(tokens_a[-1], tokens_b[-1]) >= 85


# ── Core normalization helpers ─────────────────────────────────────────────────

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
    except Exception:
        pass

    return date_str.strip()


def is_initial_match(name_a: str, name_b: str) -> bool:
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


# ── Check functions ────────────────────────────────────────────────────────────

def check_pan_format(pan_number: str) -> dict:
    normalized = normalize_pan(pan_number)
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
    valid = bool(re.match(pattern, normalized))
    return {
        "check": "PAN Format Validity",
        "input_a": pan_number,
        "input_b": f"Normalized: {normalized}",
        "result": "pass" if valid else "hard_fail",
        "reason": (
            f"PAN '{normalized}' is valid format."
            if valid else
            f"PAN '{normalized}' (normalized from '{pan_number}') "
            f"does not match required format AAAAA9999A."
        ),
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


def check_gender(gender_pan: str, gender_aadhaar: str) -> dict:
    norm_pan = normalize_gender(gender_pan)
    norm_aadhaar = normalize_gender(gender_aadhaar)

    if norm_pan == "UNKNOWN" or norm_aadhaar == "UNKNOWN":
        return {
            "check": "Gender Match",
            "input_a": f"PAN: {gender_pan} → {norm_pan}",
            "input_b": f"Aadhaar: {gender_aadhaar} → {norm_aadhaar}",
            "result": "soft_fail",
            "reason": (
                f"Gender value unrecognized — "
                f"PAN: '{gender_pan}', Aadhaar: '{gender_aadhaar}'. "
                f"Flagged for manual review."
            ),
        }

    if norm_pan == norm_aadhaar:
        return {
            "check": "Gender Match",
            "input_a": f"PAN: {gender_pan} → {norm_pan}",
            "input_b": f"Aadhaar: {gender_aadhaar} → {norm_aadhaar}",
            "result": "pass",
            "reason": f"Gender matches after normalization: both map to '{norm_pan}'.",
        }

    if "O" in [norm_pan, norm_aadhaar]:
        return {
            "check": "Gender Match",
            "input_a": f"PAN: {gender_pan} → {norm_pan}",
            "input_b": f"Aadhaar: {gender_aadhaar} → {norm_aadhaar}",
            "result": "soft_fail",
            "reason": "Gender shows 'Other/Transgender' in one document — flagged for human review.",
        }

    return {
        "check": "Gender Match",
        "input_a": f"PAN: {gender_pan} → {norm_pan}",
        "input_b": f"Aadhaar: {gender_aadhaar} → {norm_aadhaar}",
        "result": "hard_fail",
        "reason": (
            f"Gender mismatch after normalization — "
            f"PAN maps to '{norm_pan}', Aadhaar maps to '{norm_aadhaar}'. Hard block."
        ),
    }


def check_aadhaar_last4(bureau_last4: str, aadhaar_last4: str) -> dict:
    extracted_bureau = extract_aadhaar_last4(bureau_last4)
    extracted_aadhaar = extract_aadhaar_last4(aadhaar_last4)
    match = extracted_bureau == extracted_aadhaar
    return {
        "check": "Aadhaar Last-4 Consistency",
        "input_a": f"Bureau: {bureau_last4} → extracted: {extracted_bureau}",
        "input_b": f"Aadhaar: {aadhaar_last4} → extracted: {extracted_aadhaar}",
        "result": "pass" if match else "hard_fail",
        "reason": (
            f"Aadhaar last-4 consistent: {extracted_bureau}."
            if match else
            f"Aadhaar last-4 mismatch — Bureau: '{extracted_bureau}', Aadhaar: '{extracted_aadhaar}'."
        ),
    }


def check_name_fuzzy(name_a, name_b, label_a, label_b,
                     pass_threshold=85, soft_threshold=55,
                     initial_leniency=True):
    # Layer 1: Basic normalization
    norm_a = normalize_name(name_a)
    norm_b = normalize_name(name_b)

    # Layer 2: Transliteration normalization
    trans_a = apply_transliteration(norm_a)
    trans_b = apply_transliteration(norm_b)

    # Layer 3: Initial detection
    initial_match = is_initial_match(norm_a, norm_b)

    # Layer 4: Compute scores at each layer
    raw_score = fuzz.token_sort_ratio(norm_a, norm_b)
    trans_score = fuzz.token_sort_ratio(trans_a, trans_b)

    # Take best score across layers
    best_score = max(raw_score, trans_score)
    was_transliterated = trans_score > raw_score

    # Layer 5: Adjust thresholds based on graph findings
    adj_pass = pass_threshold
    adj_soft = soft_threshold

    if initial_leniency and initial_match:
        adj_pass -= 10
        adj_soft -= 15

    if was_transliterated:
        adj_soft -= 10

    # Layer 6: Verdict
    if initial_leniency and initial_match and surnames_match(norm_a, norm_b):
        result = "soft_fail"
        reason = None  # LLM explains
    elif best_score >= adj_pass:
        result = "pass"
        reason = (
            f"Names match"
            f"{' after transliteration' if was_transliterated else ''}"
            f" ({round(best_score)}% similarity)."
        )
    elif best_score >= adj_soft:
        result = "soft_fail"
        reason = None
    else:
        result = "hard_fail"
        reason = (
            f"Names too different — '{name_a}' vs '{name_b}' "
            f"({round(best_score)}% similarity). "
            f"{'Transliteration attempted but still failed. ' if was_transliterated else ''}"
            f"Hard block."
        )

    return {
        "check": f"Name Match ({label_a} vs {label_b})",
        "input_a": f"{label_a}: {name_a}",
        "input_b": f"{label_b}: {name_b}",
        "result": result,
        "reason": reason,
        "fuzzy_score": round(best_score),
        "raw_score": round(raw_score),
        "transliteration_applied": was_transliterated,
        "initial_match_detected": initial_match,
        "thresholds_used": {"pass": adj_pass, "soft": adj_soft},
    }


def check_father_name(fname_pan, fname_aadhaar,
                      pass_threshold=85, soft_threshold=55,
                      initial_leniency=True):
    # Strip prefixes before fuzzy matching
    clean_pan = normalize_father_name(fname_pan)
    clean_aadhaar = normalize_father_name(fname_aadhaar)
    result = check_name_fuzzy(clean_pan, clean_aadhaar, "PAN", "Aadhaar",
                               pass_threshold, soft_threshold, initial_leniency)
    result["check"] = "Father Name (PAN vs Aadhaar)"
    return result


def compute_overall_verdict(checks):
    results = [c["result"] for c in checks]
    if "hard_fail" in results:
        return "HARD BLOCK"
    if "soft_fail" in results:
        return "SOFT ISSUES — HUMAN REVIEW"
    return "CLEAN"


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
