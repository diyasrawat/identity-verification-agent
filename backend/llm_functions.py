import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_api_key = os.environ.get("OPENROUTER_API_KEY")
if not _api_key:
    raise EnvironmentError(
        "OPENROUTER_API_KEY is not set. Add it to backend/.env or export it in your terminal."
    )

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=_api_key,
)
MODEL = "openai/gpt-oss-120b:free"


def explain_soft_fail(check_name, input_a, input_b):
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=100,
        messages=[
            {
                "role": "system",
                "content": "You are an identity verification assistant for an Indian lending company. Be concise and factual.",
            },
            {
                "role": "user",
                "content": (
                    f"A soft mismatch was detected on a name check.\n"
                    f"Check: {check_name}\n"
                    f"Value A: {input_a}\n"
                    f"Value B: {input_b}\n"
                    f"In exactly ONE sentence, explain whether these likely refer to the same person and why. "
                    f"Be specific. No preamble."
                ),
            },
        ],
    )
    return response.choices[0].message.content


def explain_ask_ai(check, full_profile):
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=150,
        messages=[
            {
                "role": "system",
                "content": "You are an underwriting assistant at FlexiLoans, an Indian lending company. Be concise and direct.",
            },
            {
                "role": "user",
                "content": (
                    f"An identity check has failed.\n"
                    f"Full profile: {json.dumps(full_profile)}\n"
                    f"Check: {check['check']}, "
                    f"Input A: {check['input_a']}, "
                    f"Input B: {check['input_b']}, "
                    f"Severity: {check['result']}\n"
                    f"In 2-3 sentences: what does this mismatch mean, how serious is it, "
                    f"what should the underwriter do next? No preamble."
                ),
            },
        ],
    )
    return response.choices[0].message.content


async def agent_analyze(failed_summary: str, profile: dict) -> dict:
    prompt = f"""You are an identity verification agent for an Indian lending company.

You have completed automated checks on a loan applicant. Here are the failed checks:

{failed_summary}

Full applicant profile:
{json.dumps(profile, indent=2)}

As an intelligent agent, analyze these failures together (not in isolation) and respond in this exact JSON format:
{{
  "agent_note": "Your overall assessment in 2 sentences. Consider whether failures together suggest fraud, data entry error, or genuine mismatch.",
  "confidence": "HIGH or MEDIUM or LOW — your confidence that this is the same person",
  "recommendation": "PROCEED or REVIEW or REJECT",
  "reasoning": "One sentence explaining your recommendation"
}}

Respond with valid JSON only. No preamble."""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=300,
        messages=[
            {
                "role": "system",
                "content": "You are an identity verification agent. Always respond with valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    try:
        return json.loads(response.choices[0].message.content)
    except:
        return {
            "agent_note": response.choices[0].message.content,
            "confidence": "MEDIUM",
            "recommendation": "REVIEW",
            "reasoning": "Could not parse structured response",
        }


async def create_rule_code(rule_description: str) -> tuple[str, str]:
    import re as _re
    prompt = f"""You are a code-generation agent for an identity verification system at an Indian lending company.

The system has access to this applicant profile structure:
{{
  "pan": {{
    "number": "ABCPK1234D",
    "name": "Prashant Kumar",
    "dob": "1990-04-12",
    "gender": "M",
    "father_name": "Ramesh Kumar"
  }},
  "aadhaar": {{
    "last4": "1234",
    "name": "Prashant Kumar",
    "dob": "1990-04-12",
    "gender": "M",
    "father_name": "Ramesh Kumar"
  }},
  "bureau": {{
    "name": "Prashant Kumar",
    "dob": "1990-04-12",
    "pan_linked": "ABCPK1234D",
    "aadhaar_last4": "1234"
  }}
}}

The user wants to add this new verification rule:
"{rule_description}"

Generate a Python function that implements this rule.
The function must:
1. Be named: custom_check_[short_snake_case_name]
2. Accept one argument: profile (dict)
3. Return a dict with these exact keys:
   - check: str (human readable check name)
   - input_a: str (what was compared)
   - input_b: str (what it was compared against)
   - result: "pass" or "soft_fail" or "hard_fail"
   - reason: str (plain English explanation)
4. Use .get() for all dict access to avoid KeyErrors
5. Import nothing — use only built-in Python

Respond with ONLY the Python function code. No explanation, no markdown, no backticks. Just the raw function."""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=500,
        messages=[
            {
                "role": "system",
                "content": "You are a Python code generation agent. Output only raw Python function code, nothing else.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    generated_code = response.choices[0].message.content.strip()
    generated_code = generated_code.replace("```python", "").replace("```", "").strip()

    match = _re.search(r'def (custom_check_\w+)\(', generated_code)
    func_name = match.group(1) if match else "custom_check_unknown"

    return generated_code, func_name
