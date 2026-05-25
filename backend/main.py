from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

from checks import (
    check_pan_format,
    check_dob,
    check_gender,
    check_aadhaar_last4,
    check_name_fuzzy,
    check_father_name,
    compute_overall_verdict,
)
from llm_functions import explain_soft_fail, explain_ask_ai

app = FastAPI(title="Identity Cross-Verification Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class VerifyRequest(BaseModel):
    applicant_id: str
    pan: dict
    aadhaar: dict
    bureau: dict


class ExplainRequest(BaseModel):
    check: dict
    full_profile: dict


@app.post("/verify")
def verify(profile: VerifyRequest):
    pan = profile.pan
    aadhaar = profile.aadhaar
    bureau = profile.bureau

    checks = [
        check_pan_format(pan["number"]),
        check_dob(pan["dob"], aadhaar["dob"]),
        check_gender(pan["gender"], aadhaar["gender"]),
        check_aadhaar_last4(bureau["aadhaar_last4"], aadhaar["last4"]),
        check_name_fuzzy(pan["name"], aadhaar["name"], "PAN", "Aadhaar"),
        check_name_fuzzy(bureau["name"], pan["name"], "Bureau", "PAN"),
        check_father_name(pan["father_name"], aadhaar["father_name"]),
    ]

    for check in checks:
        if check["result"] == "soft_fail":
            check["reason"] = explain_soft_fail(
                check["check"], check["input_a"], check["input_b"]
            )

    verdict = compute_overall_verdict(checks)

    return {
        "applicant_id": profile.applicant_id,
        "checks": checks,
        "verdict": verdict,
    }


@app.post("/explain")
def explain(body: ExplainRequest):
    explanation = explain_ask_ai(body.check, body.full_profile)
    return {"explanation": explanation}
