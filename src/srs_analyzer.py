"""
SRS Analyzer
------------
Reusable rule-based and semantic analysis functions.

This file does NOT start the API.
This file does NOT call llama-cli.
This file can safely be imported by FastAPI.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# SEMANTIC MODEL
# ============================================================

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ============================================================
# RULE CONFIGURATION
# ============================================================

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

    "within",
    "less than",
    "greater than",
    "at least",
    "at most"
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def contains_vague_word(text: str):

    return [
        word
        for word in VAGUE_WORDS
        if word in text
    ]


def contains_measurement(text: str):

    return any(
        word in text
        for word in MEASUREMENT_WORDS
    )


def has_action(text: str):

    action_words = [
        "shall",
        "must",
        "should",
        "will",
        "can",
        "may",

        "allow",
        "allows",
        "enable",
        "enables",

        "send",
        "sends",
        "sent",

        "store",
        "stores",
        "save",
        "saves",

        "create",
        "creates",

        "delete",
        "deletes",

        "update",
        "updates",

        "display",
        "displays",
        "show",
        "shows",

        "register",
        "login",
        "log",
        "purchase",
        "order",
        "cancel",

        "receive",
        "receives",

        "generate",
        "generates",

        "process",
        "processes"
    ]

    return any(
        word in text
        for word in action_words
    )


# ============================================================
# CONTRADICTION DETECTION
# ============================================================

def find_contradictions(text: str):

    contradictions = []

    contradiction_pairs = [

        (
            "must be registered",
            "must not be registered"
        ),

        (
            "must be logged in",
            "must not be logged in"
        ),

        (
            "shall be enabled",
            "shall not be enabled"
        ),

        (
            "shall be disabled",
            "shall not be disabled"
        ),

        (
            "allow",
            "not allow"
        ),

        (
            "allows",
            "does not allow"
        ),

        (
            "must",
            "must not"
        ),

        (
            "shall",
            "shall not"
        )
    ]

    for positive, negative in contradiction_pairs:

        if positive in text and negative in text:

            contradictions.append(
                f"Potential contradiction between "
                f"'{positive}' and '{negative}'."
            )

    return contradictions


# ============================================================
# BASIC WORDING CHECKS
# ============================================================

def find_wording_issues(text: str):

    issues = []

    wording_patterns = {

        "will sent":
            "The phrase 'will sent' may need correction to 'will send'.",

        "data base":
            "The term 'data base' should normally be written as 'database'.",

        "email-address":
            "The term 'email-address' could be written as 'email address'.",

        "customer’s email":
            "The requirement should clearly identify the intended email destination."
    }

    for pattern, message in wording_patterns.items():

        if pattern in text:

            issues.append(message)

    return issues


# ============================================================
# RULE-BASED QUALITY ANALYZER
# ============================================================

def analyze_quality(
    requirement: str,
    metadata: dict | None = None
):

    if metadata is None:
        metadata = {}

    text = requirement.lower().strip()

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


    # ========================================================
    # CORRECTNESS
    # ========================================================

    if not text.endswith("."):

        result["correctness"].append(
            "The requirement does not end with a period."
        )


    # ========================================================
    # CONSISTENCY
    # ========================================================

    contradictions = find_contradictions(text)

    result["consistency"].extend(
        contradictions
    )


    # ========================================================
    # CLARITY
    # ========================================================

    vague_words = contains_vague_word(text)

    for word in vague_words:

        result["clarity"].append(
            f"Vague or subjective term: '{word}'."
        )


    wording_issues = find_wording_issues(text)

    result["clarity"].extend(
        wording_issues
    )


    # ========================================================
    # COMPLETENESS
    # ========================================================

    # Vague quality/performance terms may require
    # measurable criteria.

    if vague_words:

        result["completeness"].append(
            "The requirement may be missing "
            "measurable details for its vague wording."
        )


    # Do NOT require shall/must/should.
    #
    # Functional requirements can be written using
    # normal action statements such as:
    #
    # "The system will send..."
    #
    # "The user receives..."
    #
    # Therefore absence of a requirement keyword
    # is not automatically a completeness problem.


    # ========================================================
    # UNAMBIGUITY
    # ========================================================

    for word in vague_words:

        result["unambiguity"].append(
            f"'{word}' may have multiple interpretations."
        )


    # Actual contradictions can also make a requirement
    # ambiguous.

    for issue in contradictions:

        result["unambiguity"].append(
            issue
        )


    # ========================================================
    # VERIFIABILITY
    # ========================================================

    has_measurement = contains_measurement(text)

    if vague_words and not has_measurement:

        result["verifiability"].append(
            "No objective measurable criterion "
            "was found for the vague wording."
        )


    # A functional action is normally testable.
    #
    # Example:
    #
    # "The system will send a bill to the customer."
    #
    # can be tested by placing an order and checking
    # whether the bill was sent.


    # ========================================================
    # FEASIBILITY
    # ========================================================

    extreme_targets = [

        "1 millisecond",
        "0 milliseconds",
        "1000000 requests",
        "10000000 requests"
    ]

    for target in extreme_targets:

        if target in text:

            result["feasibility"].append(
                f"The performance target '{target}' "
                "may require feasibility review."
            )


    # ========================================================
    # TRACEABILITY
    # ========================================================

    if (
        metadata.get("source")
        and metadata.get("section_number")
    ):

        result["traceability"].append(
            "Requirement is traceable to its "
            "source document and SRS section."
        )

    else:

        result["traceability"].append(
            "Requirement source or SRS section "
            "information is missing."
        )


    return result


# ============================================================
# CONVERT RULE RESULT TO STATUS
# ============================================================

def rule_status(
    dimension: str,
    issues: list[str]
):

    if not issues:

        return "PASS"


    # --------------------------------------------------------
    # Traceability
    # --------------------------------------------------------

    if dimension == "traceability":

        if "traceable" in issues[0].lower():

            return "PASS"

        return "NEEDS_REVIEW"


    # --------------------------------------------------------
    # All detected rule issues currently require review.
    # --------------------------------------------------------

    return "NEEDS_REVIEW"


# ============================================================
# STRUCTURED RULE ANALYSIS
# ============================================================

def get_structured_rule_analysis(
    requirement: str,
    metadata: dict | None = None
):

    raw_result = analyze_quality(
        requirement,
        metadata
    )

    structured = {}

    for dimension, issues in raw_result.items():

        structured[dimension] = {

            "status": rule_status(
                dimension,
                issues
            ),

            "issues": issues
        }

    return structured


# ============================================================
# SEMANTIC SIMILARITY
# ============================================================

def find_similar_requirements(
    requirements,
    threshold=0.60
):

    if len(requirements) < 2:

        return []


    texts = [

        item["requirement"]

        for item in requirements
    ]


    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    )


    similarity_matrix = cosine_similarity(
        embeddings
    )


    relationships = []


    for i in range(
        len(requirements)
    ):

        for j in range(
            i + 1,
            len(requirements)
        ):

            score = float(
                similarity_matrix[i][j]
            )


            if score >= threshold:

                if score >= 0.80:

                    classification = (
                        "POSSIBLE_DUPLICATE"
                    )

                else:

                    classification = "RELATED"


                relationships.append({

                    "requirement_1_id":
                        requirements[i][
                            "requirement_id"
                        ],

                    "requirement_2_id":
                        requirements[j][
                            "requirement_id"
                        ],

                    "similarity":
                        round(score, 4),

                    "classification":
                        classification
                })


    return relationships