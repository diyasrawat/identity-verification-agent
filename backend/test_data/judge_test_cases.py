"""
10 named judge test cases that showcase the system's capabilities.
Each case has a descriptive name, the input, expected verdict, and why it's interesting.
"""

JUDGE_TEST_CASES = [
    {
        "name": "TC-01: Perfect Clean Match",
        "category": "judge_demo",
        "description": "All fields match perfectly — baseline clean case.",
        "expected_verdict": "CLEAN",
        "pan": {
            "number": "ABCPK1234D",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "aadhaar": {
            "last4": "1234",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "bureau": {
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "pan_linked": "ABCPK1234D",
            "aadhaar_last4": "1234"
        }
    },
    {
        "name": "TC-02: Initial Name Abbreviation",
        "category": "judge_demo",
        "description": "PAN uses 'P. Kumar' while Aadhaar has 'Prashant Kumar' — tests initial leniency.",
        "expected_verdict": "SOFT ISSUES — HUMAN REVIEW",
        "pan": {
            "number": "ABCPK1234D",
            "name": "P. Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "R. Kumar"
        },
        "aadhaar": {
            "last4": "1234",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "bureau": {
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "pan_linked": "ABCPK1234D",
            "aadhaar_last4": "1234"
        }
    },
    {
        "name": "TC-03: DOB Typo (arpil → april)",
        "category": "judge_demo",
        "description": "PAN DOB has typo 'arpil' — tests typo-correction in normalize_date.",
        "expected_verdict": "CLEAN",
        "pan": {
            "number": "ABCPK1234D",
            "name": "Prashant Kumar",
            "dob": "2004 arpil 6th",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "aadhaar": {
            "last4": "1234",
            "name": "Prashant Kumar",
            "dob": "2004/04/06",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "bureau": {
            "name": "Prashant Kumar",
            "dob": "2004-04-06",
            "pan_linked": "ABCPK1234D",
            "aadhaar_last4": "1234"
        }
    },
    {
        "name": "TC-04: Transliteration (Prashanth → Prashant)",
        "category": "judge_demo",
        "description": "South Indian name variant — Prashanth vs Prashant — tests transliteration graph.",
        "expected_verdict": "CLEAN",
        "pan": {
            "number": "ABCPK1234D",
            "name": "Prashanth Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "aadhaar": {
            "last4": "1234",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "bureau": {
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "pan_linked": "ABCPK1234D",
            "aadhaar_last4": "1234"
        }
    },
    {
        "name": "TC-05: Hard DOB Mismatch",
        "category": "judge_demo",
        "description": "DOB completely different across documents — hard block expected.",
        "expected_verdict": "HARD BLOCK",
        "pan": {
            "number": "ABCPK1234D",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "aadhaar": {
            "last4": "1234",
            "name": "Prashant Kumar",
            "dob": "1985-07-23",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "bureau": {
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "pan_linked": "ABCPK1234D",
            "aadhaar_last4": "1234"
        }
    },
    {
        "name": "TC-06: Gender Normalization (Male vs 1)",
        "category": "judge_demo",
        "description": "PAN has 'Male', Aadhaar has '1' — tests gender normalization graph.",
        "expected_verdict": "CLEAN",
        "pan": {
            "number": "ABCPK1234D",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "Male",
            "father_name": "Ramesh Kumar"
        },
        "aadhaar": {
            "last4": "1234",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "1",
            "father_name": "Ramesh Kumar"
        },
        "bureau": {
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "pan_linked": "ABCPK1234D",
            "aadhaar_last4": "1234"
        }
    },
    {
        "name": "TC-07: Masked Aadhaar (XXXX-XXXX-5678)",
        "category": "judge_demo",
        "description": "Bureau has masked Aadhaar 'XXXX-XXXX-5678' — tests last-4 extraction.",
        "expected_verdict": "CLEAN",
        "pan": {
            "number": "ABCPK1234D",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "aadhaar": {
            "last4": "5678",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "bureau": {
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "pan_linked": "ABCPK1234D",
            "aadhaar_last4": "XXXX-XXXX-5678"
        }
    },
    {
        "name": "TC-08: Mohammed Variant (Muhammed → Mohammad)",
        "category": "judge_demo",
        "description": "PAN has 'Muhammed Ali', Aadhaar has 'Mohammad Ali' — tests Mohammed transliteration.",
        "expected_verdict": "CLEAN",
        "pan": {
            "number": "ABCMA5678Z",
            "name": "Muhammed Ali",
            "dob": "1988-03-15",
            "gender": "M",
            "father_name": "Abdul Ali"
        },
        "aadhaar": {
            "last4": "9012",
            "name": "Mohammad Ali",
            "dob": "1988-03-15",
            "gender": "M",
            "father_name": "Abdul Ali"
        },
        "bureau": {
            "name": "Mohammad Ali",
            "dob": "1988-03-15",
            "pan_linked": "ABCMA5678Z",
            "aadhaar_last4": "9012"
        }
    },
    {
        "name": "TC-09: Father Name Prefix Stripped (S/O Ramesh)",
        "category": "judge_demo",
        "description": "Aadhaar father name has 'S/O Ramesh Kumar' prefix — tests prefix stripping.",
        "expected_verdict": "CLEAN",
        "pan": {
            "number": "ABCPK1234D",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "Ramesh Kumar"
        },
        "aadhaar": {
            "last4": "1234",
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "gender": "M",
            "father_name": "S/O Ramesh Kumar"
        },
        "bureau": {
            "name": "Prashant Kumar",
            "dob": "1990-04-06",
            "pan_linked": "ABCPK1234D",
            "aadhaar_last4": "1234"
        }
    },
    {
        "name": "TC-10: Completely Different Identity",
        "category": "judge_demo",
        "description": "Name, DOB, and Aadhaar last4 all mismatched — maximum hard block.",
        "expected_verdict": "HARD BLOCK",
        "pan": {
            "number": "XYZAB9999P",
            "name": "Rahul Sharma",
            "dob": "1992-11-20",
            "gender": "M",
            "father_name": "Vijay Sharma"
        },
        "aadhaar": {
            "last4": "0000",
            "name": "Priya Singh",
            "dob": "1995-05-10",
            "gender": "F",
            "father_name": "Mohan Singh"
        },
        "bureau": {
            "name": "Rahul Sharma",
            "dob": "1992-11-20",
            "pan_linked": "XYZAB9999P",
            "aadhaar_last4": "1111"
        }
    }
]
