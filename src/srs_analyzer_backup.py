import json

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------
# Semantic model
# ---------------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# ---------------------------------
# Quality analysis rules
# ---------------------------------

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


# ---------------------------------
# Quality Analyzer
# ---------------------------------

def analyze_quality(requirement):

    text = requirement.lower()

    result = {
        "correctness": [],
        "completeness": [],
        "consistency": [],
        "clarity": [],
        "unambiguity": [],
        "verifiability": [],
        "feasibility": [],
        "traceability": []
    }

    # ---------------------------------
    # Correctness
    # ---------------------------------

    if not text.endswith("."):

        result["correctness"].append(
            "The requirement may not be properly formulated."
        )

    # ---------------------------------
    # Consistency
    # ---------------------------------

    if "user" in text and "customer" in text:

        result["consistency"].append(
            "The requirement uses both 'user' and 'customer' terminology."
        )

    # ---------------------------------
    # Clarity
    # ---------------------------------

    for word in VAGUE_WORDS:

        if word in text:

            result["clarity"].append(
                f"Vague or subjective term: '{word}'"
            )

    # ---------------------------------
    # Completeness
    # ---------------------------------

    if any(word in text for word in VAGUE_WORDS):

        result["completeness"].append(
            "The requirement may be missing measurable details."
        )

    if "shall" not in text and "must" not in text:

        result["completeness"].append(
            "The requirement may not explicitly define the required behavior."
        )

    # ---------------------------------
    # Unambiguity
    # ---------------------------------

    for word in VAGUE_WORDS:

        if word in text:

            result["unambiguity"].append(
                f"'{word}' may have multiple interpretations."
            )

    # ---------------------------------
    # Verifiability
    # ---------------------------------

    has_measurement = any(
        word in text for word in MEASUREMENT_WORDS
    )

    if any(word in text for word in VAGUE_WORDS) and not has_measurement:

        result["verifiability"].append(
            "No objective measurable criterion was found."
        )

    # ---------------------------------
    # Feasibility
    # ---------------------------------

    if (
        "1 millisecond" in text
        or "0 milliseconds" in text
        or "1000000 requests" in text
    ):

        result["feasibility"].append(
            "The specified performance target may require feasibility review."
        )

    # ---------------------------------
    # Traceability
    # ---------------------------------

    result["traceability"].append(
        "No source, business objective, or linked artifact is available for traceability analysis."
    )

    return result


# ---------------------------------
# Semantic Similarity Analyzer
# ---------------------------------

def find_similar_requirements(requirements, threshold=0.60):

    embeddings = model.encode(requirements)

    similarity_matrix = cosine_similarity(embeddings)

    relationships = []

    for i in range(len(requirements)):

        for j in range(i + 1, len(requirements)):

            score = float(similarity_matrix[i][j])

            if score >= threshold:

                if score >= 0.80:
                    classification = "POSSIBLE_DUPLICATE"
                else:
                    classification = "RELATED"

                relationships.append({

                    "requirement_1_id": f"R{i + 1:03}",

                    "requirement_2_id": f"R{j + 1:03}",

                    "similarity": round(score, 4),

                    "classification": classification

                })

    return relationships


# ---------------------------------
# Load Requirements from JSON
# ---------------------------------

with open(
    "data/requirements.json",
    "r",
    encoding="utf-8"
) as file:

    data = json.load(file)


requirements = [
    item["requirement"]
    for item in data
]


# ---------------------------------
# Display Quality Analysis
# ---------------------------------

print("\nQUALITY ANALYSIS")
print("=" * 60)

for index, requirement in enumerate(requirements):

    requirement_id = f"R{index + 1:03}"

    print(f"\n{requirement_id}")

    print("Requirement:")
    print(requirement)

    result = analyze_quality(requirement)

    for dimension, issues in result.items():

        if issues:

            if any(
                "Vague" in issue
                or "multiple interpretations" in issue
                for issue in issues
            ):
                status = "FAIL"
            else:
                status = "NEEDS_REVIEW"

            print(f"{dimension.upper()}: {status}")

            for issue in issues:
                print(f"  ⚠ {issue}")

        else:

            print(f"{dimension.upper()}: PASS")


# ---------------------------------
# Display Semantic Similarity
# ---------------------------------

print("\n\nSEMANTIC SIMILARITY")
print("=" * 60)

relationships = find_similar_requirements(
    requirements
)

if relationships:

    for relationship in relationships:

        print("\nRequirement Pair:")

        print(
            f"{relationship['requirement_1_id']} ↔ "
            f"{relationship['requirement_2_id']}"
        )

        print(
            "Similarity:",
            relationship["similarity"]
        )

        print(
            "Classification:",
            relationship["classification"]
        )

else:

    print(
        "\nNo potentially related requirements found."
    )