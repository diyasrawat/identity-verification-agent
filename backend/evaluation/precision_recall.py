GROUND_TRUTH = {
    "FL-001": {
        "expected_verdict": "CLEAN",
        "expected_check_results": {
            "PAN Format": "pass",
            "Date of Birth": "pass",
            "Gender": "pass",
            "Aadhaar Last 4": "pass",
            "Name Match (PAN vs Aadhaar)": "pass",
            "Name Match (Bureau vs PAN)": "pass",
            "Father Name": "pass",
        },
        "planted_issues": []
    },
    "FL-002": {
        "expected_verdict": "SOFT ISSUES — HUMAN REVIEW",
        "expected_check_results": {
            "PAN Format": "pass",
            "Date of Birth": "pass",
            "Gender": "pass",
            "Aadhaar Last 4": "pass",
            "Name Match (PAN vs Aadhaar)": "soft_fail",
            "Name Match (Bureau vs PAN)": "pass",
            "Father Name": "soft_fail",
        },
        "planted_issues": [
            "Name abbreviation: P. Kumar vs Prashant Kumar",
            "Father abbreviation: R. Kumar vs Ramesh Kumar"
        ]
    },
    "FL-003": {
        "expected_verdict": "HARD BLOCK",
        "expected_check_results": {
            "PAN Format": "pass",
            "Date of Birth": "hard_fail",
            "Gender": "pass",
            "Aadhaar Last 4": "pass",
            "Name Match (PAN vs Aadhaar)": "pass",
            "Name Match (Bureau vs PAN)": "pass",
            "Father Name": "pass",
        },
        "planted_issues": [
            "DOB mismatch: 1990-04-12 vs 1985-07-23"
        ]
    }
}


def _find_check(checks: list, check_key: str):
    """Find a check by partial name match."""
    for c in checks:
        if check_key.lower() in c.get("check", "").lower():
            return c
    return None


def compute_precision_recall(actual_results: dict) -> dict:
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0

    per_file_accuracy = {}

    for file_id, ground in GROUND_TRUTH.items():
        if file_id not in actual_results:
            continue

        actual = actual_results[file_id]
        actual_verdict = actual.get("identity_verdict") or actual.get("verdict", "")

        file_stats = {
            "expected_verdict": ground["expected_verdict"],
            "actual_verdict": actual_verdict,
            "verdict_correct": ground["expected_verdict"] == actual_verdict,
            "planted_issues": ground["planted_issues"],
            "check_accuracy": []
        }

        for check_key, expected_result in ground["expected_check_results"].items():
            actual_check = _find_check(actual.get("checks", []), check_key)

            if actual_check:
                actual_result = actual_check.get("result", "")
                is_fail = expected_result != "pass"
                predicted_fail = actual_result != "pass"

                if is_fail and predicted_fail:
                    true_positives += 1
                elif not is_fail and not predicted_fail:
                    true_negatives += 1
                elif not is_fail and predicted_fail:
                    false_positives += 1
                elif is_fail and not predicted_fail:
                    false_negatives += 1

                file_stats["check_accuracy"].append({
                    "check": check_key,
                    "expected": expected_result,
                    "actual": actual_result,
                    "correct": expected_result == actual_result
                })

        per_file_accuracy[file_id] = file_stats

    total = true_positives + false_positives + false_negatives + true_negatives

    precision = true_positives / max(true_positives + false_positives, 1)
    recall = true_positives / max(true_positives + false_negatives, 1)
    f1 = 2 * precision * recall / max(precision + recall, 0.001)
    accuracy = (true_positives + true_negatives) / max(total, 1)

    return {
        "precision": round(precision * 100, 1),
        "recall": round(recall * 100, 1),
        "f1_score": round(f1 * 100, 1),
        "accuracy": round(accuracy * 100, 1),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
        "per_file": per_file_accuracy,
        "interpretation": {
            "precision": f"{round(precision * 100, 1)}% of flagged issues were real issues",
            "recall": f"{round(recall * 100, 1)}% of actual issues were caught",
            "f1": f"Overall F1 score: {round(f1 * 100, 1)}% — balance of precision and recall"
        }
    }
