import os
import re
import sys
from datetime import datetime
from openai import OpenAI
from rapidfuzz import fuzz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from knowledge.address_graph import graph_address_match, graph_lookup

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

ADDRESS_BASE_TRUST = {
    "aadhaar": 90,
    "gst": 80,
    "bank_statement": 75,
    "pan": 45,
    "utility_bill": 35,
    "self_declared": 15,
}

RECENCY_MULTIPLIER = {
    "this_year": 1.0,
    "1_2_years": 0.85,
    "2_3_years": 0.70,
    "3_plus_years": 0.50,
    "unknown": 0.75,
}


def compute_address_trust_score(source: str, doc_year: int = None) -> dict:
    current_year = datetime.now().year
    base = ADDRESS_BASE_TRUST.get(source, 20)

    if doc_year is None:
        recency_key = "unknown"
    else:
        age = current_year - int(doc_year)
        if age <= 1:
            recency_key = "this_year"
        elif age <= 2:
            recency_key = "1_2_years"
        elif age <= 3:
            recency_key = "2_3_years"
        else:
            recency_key = "3_plus_years"

    multiplier = RECENCY_MULTIPLIER[recency_key]
    final_score = round(base * multiplier)

    return {
        "source": source,
        "base_trust": base,
        "recency": recency_key,
        "multiplier": multiplier,
        "final_score": final_score,
        "reasoning": (
            f"{source.replace('_', ' ').title()} "
            f"(base: {base}) × recency factor "
            f"{recency_key.replace('_', ' ')} "
            f"({multiplier}) = {final_score}/100"
        ),
    }


def extract_pincode(address: str) -> str:
    match = re.search(r'\b\d{6}\b', address)
    return match.group(0) if match else ""


def normalize_address(address: str) -> str:
    address = address.upper().strip()
    expansions = {
        "MG ": "MAHATMA GANDHI ",
        "RD ": "ROAD ",
        "ST ": "STREET ",
        "NGR": "NAGAR",
        "SOC": "SOCIETY",
        "APPT": "APARTMENT",
        "APT": "APARTMENT",
        "HSG": "HOUSING",
    }
    for abbr, full in expansions.items():
        address = address.replace(abbr, full)
    address = re.sub(r'[^\w\s]', ' ', address)
    address = re.sub(r'\s+', ' ', address).strip()
    return address


def run_address_agent(addresses: dict, profile: dict, doc_dates: dict = None) -> dict:
    if doc_dates is None:
        doc_dates = {}

    if not addresses:
        return {
            "agent": "address",
            "status": "skipped",
            "verdict": "NO_ADDRESS_DATA",
            "canonical_address": None,
            "conflicts": [],
            "hard_conflicts": 0,
            "soft_conflicts": 0,
            "agent_analysis": "No address data provided.",
            "normalized_addresses": {},
            "pincodes": {},
            "pincode_groups": {},
            "trust_scores": {},
            "trust_reasoning": {},
            "doc_dates_used": doc_dates,
        }

    # Compute recency-aware trust scores
    trust_scores = {}
    trust_reasoning = {}
    for source in addresses.keys():
        year = doc_dates.get(source)
        score_data = compute_address_trust_score(source, year)
        trust_scores[source] = score_data["final_score"]
        trust_reasoning[source] = score_data["reasoning"]

    normalized = {src: normalize_address(addr) for src, addr in addresses.items()}
    pincodes = {src: extract_pincode(addr) for src, addr in addresses.items()}

    non_empty_pincodes = {k: v for k, v in pincodes.items() if v}
    unique_pincodes = set(non_empty_pincodes.values())

    pincode_groups = {}
    for src, pin in non_empty_pincodes.items():
        pincode_groups.setdefault(pin, []).append(src)

    sources = list(normalized.keys())
    conflicts = []

    for i in range(len(sources)):
        for j in range(i + 1, len(sources)):
            src_a, src_b = sources[i], sources[j]

            # Try knowledge graph first
            graph_result = graph_address_match(addresses[src_a], addresses[src_b])

            if graph_result["result"] == "GRAPH_CONFIRMED_MATCH":
                # Graph says same location — skip further checks for this pair
                continue
            elif graph_result["result"] == "GRAPH_CONFIRMED_DIFFERENT":
                conflicts.append({
                    "source_a": src_a,
                    "source_b": src_b,
                    "type": "GRAPH_CONFIRMED_DIFFERENT",
                    "severity": "hard",
                    "detail": graph_result["reasoning"],
                    "method": "knowledge_graph",
                })
            else:
                # Fall back to existing fuzzy + pincode logic
                score = fuzz.token_sort_ratio(normalized[src_a], normalized[src_b])
                pin_a = pincodes.get(src_a, "")
                pin_b = pincodes.get(src_b, "")

                if pin_a and pin_b and pin_a != pin_b:
                    conflicts.append({
                        "source_a": src_a,
                        "source_b": src_b,
                        "type": "PINCODE_MISMATCH",
                        "severity": "hard",
                        "detail": f"Pincode {pin_a} vs {pin_b}",
                    })
                elif score < 50:
                    conflicts.append({
                        "source_a": src_a,
                        "source_b": src_b,
                        "type": "ADDRESS_MISMATCH",
                        "severity": "soft",
                        "detail": f"Similarity: {score}%",
                    })

    canonical_source = max(
        [s for s in addresses if addresses[s]],
        key=lambda s: trust_scores.get(s, 0),
    )
    canonical_address = addresses[canonical_source]

    hard_conflicts = [c for c in conflicts if c["severity"] == "hard"]
    soft_conflicts = [c for c in conflicts if c["severity"] == "soft"]

    if hard_conflicts:
        address_verdict = "CONFLICTING"
    elif soft_conflicts:
        address_verdict = "LIKELY_SAME"
    elif len(unique_pincodes) <= 1:
        address_verdict = "CONSISTENT"
    else:
        address_verdict = "LIKELY_SAME"

    agent_analysis = None
    if hard_conflicts or len(soft_conflicts) > 2:
        addr_summary = "\n".join(
            f"- {src} (trust: {trust_scores.get(src, 0)}/100): {addr}"
            for src, addr in addresses.items()
        )
        conflict_summary = "\n".join(
            f"- {c['source_a']} vs {c['source_b']}: {c['type']} ({c['detail']})"
            for c in conflicts
        )
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b:free",
            max_tokens=200,
            messages=[
                {
                    "role": "system",
                    "content": "You are an address verification agent for an Indian lending company. Be concise and practical.",
                },
                {
                    "role": "user",
                    "content": (
                        f"Analyze these addresses for a loan applicant:\n\n{addr_summary}\n\n"
                        f"Conflicts detected:\n{conflict_summary}\n\n"
                        f"In 2-3 sentences: Are these the same location or genuinely different places? "
                        f"What does this mean for the loan application? What should the underwriter do?"
                    ),
                },
            ],
        )
        agent_analysis = response.choices[0].message.content
    else:
        agent_analysis = (
            f"Addresses are {address_verdict.lower().replace('_', ' ')}. "
            f"Canonical address identified from {canonical_source} (highest trust score: {trust_scores.get(canonical_source, 0)}/100). "
            f"No LLM analysis required."
        )

    return {
        "agent": "address",
        "status": "complete",
        "verdict": address_verdict,
        "canonical_address": canonical_address,
        "canonical_source": canonical_source,
        "normalized_addresses": normalized,
        "pincodes": pincodes,
        "pincode_groups": pincode_groups,
        "conflicts": conflicts,
        "hard_conflicts": len(hard_conflicts),
        "soft_conflicts": len(soft_conflicts),
        "agent_analysis": agent_analysis,
        "trust_scores": trust_scores,
        "trust_reasoning": trust_reasoning,
        "doc_dates_used": doc_dates,
        "graph_lookups": {src: graph_lookup(addr) for src, addr in addresses.items()},
        # keep legacy key for any existing consumers
        "trust_ranking": trust_scores,
    }
