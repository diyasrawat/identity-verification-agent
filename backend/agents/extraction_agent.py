import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from checks import normalize_name, normalize_date


def run_extraction_agent(profile: dict) -> dict:
    extraction_log = []
    cleaned = {}

    pan_raw = profile.get("pan", {})
    aadhaar_raw = profile.get("aadhaar", {})
    bureau_raw = profile.get("bureau", {})

    cleaned["pan"] = {
        "number": pan_raw.get("number", "").upper().strip(),
        "name": normalize_name(pan_raw.get("name", "")),
        "dob": normalize_date(pan_raw.get("dob", "")),
        "gender": pan_raw.get("gender", "").upper().strip(),
        "father_name": normalize_name(pan_raw.get("father_name", "")),
    }

    cleaned["aadhaar"] = {
        "last4": aadhaar_raw.get("last4", "").strip(),
        "name": normalize_name(aadhaar_raw.get("name", "")),
        "dob": normalize_date(aadhaar_raw.get("dob", "")),
        "gender": aadhaar_raw.get("gender", "").upper().strip(),
        "father_name": normalize_name(aadhaar_raw.get("father_name", "")),
    }

    cleaned["bureau"] = {
        "name": normalize_name(bureau_raw.get("name", "")),
        "dob": normalize_date(bureau_raw.get("dob", "")),
        "pan_linked": bureau_raw.get("pan_linked", "").upper().strip(),
        "aadhaar_last4": bureau_raw.get("aadhaar_last4", "").strip(),
    }

    cleaned["addresses"] = profile.get("addresses", {})
    cleaned["applicant_id"] = profile.get("applicant_id", "UNKNOWN")

    # Log normalized fields
    for field, raw_val, norm_val, action in [
        ("pan.name", pan_raw.get("name", ""), cleaned["pan"]["name"], "normalized"),
        ("pan.dob", pan_raw.get("dob", ""), cleaned["pan"]["dob"], "date_normalized"),
        ("aadhaar.name", aadhaar_raw.get("name", ""), cleaned["aadhaar"]["name"], "normalized"),
        ("aadhaar.dob", aadhaar_raw.get("dob", ""), cleaned["aadhaar"]["dob"], "date_normalized"),
    ]:
        if raw_val != norm_val:
            extraction_log.append({
                "field": field,
                "raw": raw_val,
                "normalized": norm_val,
                "action": action,
            })

    return {
        "agent": "extraction",
        "status": "complete",
        "cleaned_profile": cleaned,
        "extraction_log": extraction_log,
        "fields_normalized": len(extraction_log),
    }
