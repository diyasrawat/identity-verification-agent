import os
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)
MODEL = "anthropic/claude-haiku-4-5"


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
