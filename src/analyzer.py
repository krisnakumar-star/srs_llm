VAGUE_WORDS = [
    "quickly",
    "efficiently",
    "good",
    "easy",
    "user-friendly",
    "secure"
]

MEASUREMENT_WORDS = [
    "seconds",
    "milliseconds",
    "minutes",
    "%",
    "percent",
    "mb",
    "gb",
    "maximum",
    "minimum",
    "within"
]


def analyze_requirement(requirement):
    text = requirement.lower()
    issues = []

    # 1. CLARITY
    clarity_issues = []

    for word in VAGUE_WORDS:
        if word in text:
            clarity_issues.append(
                f"The term '{word}' is vague or subjective."
            )

    if clarity_issues:
        clarity = {
            "label": "FAIL",
            "issues": clarity_issues
        }
    else:
        clarity = {
            "label": "PASS",
            "issues": []
        }

    # 2. COMPLETENESS
    completeness_issues = []

    if any(word in text for word in VAGUE_WORDS):
        completeness_issues.append(
            "The requirement may be missing measurable details."
        )

    if "shall" not in text:
        completeness_issues.append(
            "The requirement does not explicitly define the required system behavior."
        )

    if completeness_issues:
        completeness = {
            "label": "NEEDS_REVIEW",
            "issues": completeness_issues
        }
    else:
        completeness = {
            "label": "PASS",
            "issues": []
        }

    # 3. UNAMBIGUITY
    ambiguity_issues = []

    for word in VAGUE_WORDS:
        if word in text:
            ambiguity_issues.append(
                f"'{word}' can have multiple interpretations."
            )

    if ambiguity_issues:
        unambiguity = {
            "label": "FAIL",
            "issues": ambiguity_issues
        }
    else:
        unambiguity = {
            "label": "PASS",
            "issues": []
        }

    # 4. VERIFIABILITY / TESTABILITY
    verifiability_issues = []

    has_measurement = any(
        word in text for word in MEASUREMENT_WORDS
    )

    if any(word in text for word in VAGUE_WORDS) and not has_measurement:
        verifiability_issues.append(
            "The requirement does not contain an objective measurable criterion."
        )

    if verifiability_issues:
        verifiability = {
            "label": "FAIL",
            "issues": verifiability_issues
        }
    else:
        verifiability = {
            "label": "PASS",
            "issues": []
        }

    return {
        "clarity": clarity,
        "completeness": completeness,
        "unambiguity": unambiguity,
        "verifiability": verifiability
    }


# -----------------------------
# Main program
# -----------------------------

requirement = input("Enter a software requirement: ")

result = analyze_requirement(requirement)

print("\nRequirement Analysis")
print("=" * 50)

for dimension, analysis in result.items():

    print(f"\n{dimension.upper()}")
    print(f"Status: {analysis['label']}")

    if analysis["issues"]:
        for issue in analysis["issues"]:
            print(f"  ⚠ {issue}")
    else:
        print("  ✓ No obvious issue detected.")