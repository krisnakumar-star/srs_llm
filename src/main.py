import os
import re
import requests

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from src.srs_analyzer import (
    get_structured_rule_analysis,
    find_similar_requirements
)


load_dotenv()

SRS_API_KEY = os.getenv("SRS_API_KEY")

QWEN_API_URL = os.getenv(
    "QWEN_API_URL",
    "http://127.0.0.1:8080/v1/chat/completions"
)


app = FastAPI(
    title="SRS LLM API",
    description="AI-powered Software Requirement Analysis and Validation API",
    version="1.0.0"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class RequirementRequest(BaseModel):
    requirement: str
    source: str = ""
    section_number: str = ""


class BatchRequirementRequest(BaseModel):
    requirements: list[str]


class SimilarityRequest(BaseModel):
    requirements: list[dict]
    threshold: float = 0.60


# ============================================================
# API KEY
# ============================================================

def verify_api_key(x_api_key: str | None):

    if not SRS_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="SRS_API_KEY is not configured."
        )

    if x_api_key != SRS_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key."
        )


# ============================================================
# BASIC ENDPOINTS
# ============================================================

@app.get("/")
def home():

    return {
        "message": "SRS LLM API is running",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
def health():

    qwen_status = "offline"

    try:

        response = requests.get(
            "http://127.0.0.1:8080/v1/models",
            timeout=5
        )

        if response.status_code == 200:
            qwen_status = "online"

    except requests.RequestException:
        qwen_status = "offline"

    return {
        "api": "online",
        "qwen": qwen_status
    }


# ============================================================
# QWEN RESPONSE PARSING
# ============================================================

def extract_dimension(text: str, dimension: str):

    pattern = (
        rf"{dimension}\s*:\s*"
        rf"(PASS|NEEDS_REVIEW|FAIL)"
        rf"\s*\n\s*Reason\s*:\s*"
        rf"(.*?)"
        rf"(?=\n\s*[A-Z]+\s*:|\n\s*MAIN ISSUE:|\n\s*RECOMMENDATION:|$)"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not match:

        return {
            "status": "PASS",
            "reason": ""
        }

    return {
        "status": match.group(1).upper(),
        "reason": match.group(2).strip()
    }


def extract_text_section(text: str, section_name: str):

    pattern = (
        rf"{re.escape(section_name)}\s*:"
        rf"\s*(.*?)"
        rf"(?=\n\s*RECOMMENDATION:|$)"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not match:
        return ""

    return match.group(1).strip()


# ============================================================
# QWEN ANALYSIS
# ============================================================

def run_qwen_analysis(requirement: str):

    prompt = f"""
You are an expert software requirements quality analyst.

Analyze ONLY the following software requirement:

{requirement}

Evaluate ONLY these four dimensions:

1. CLARITY
2. COMPLETENESS
3. CONSISTENCY
4. VERIFIABILITY

IMPORTANT RULES:

- Analyze only the requirement provided.
- Do not invent missing facts.
- Do not assume information that is not written.
- Do not introduce issues unrelated to the requirement.
- Do not require architecture details.
- Do not require hardware details.
- Do not require programming languages.
- Do not require deployment details.
- Do not require scalability details.
- Do not require implementation technologies.
- Do not explain how developers should implement the requirement.
- Evaluate what the requirement specifies, not how it should be implemented.

VAGUE WORDS:

Words such as:
"quickly"
"efficiently"
"easy"
"good"
"user-friendly"

should normally require review when no objective criterion is provided.

MEASURABLE REQUIREMENTS:

If a requirement contains an objective measurable threshold such as:
"within 2 seconds"
"at least 95%"
"less than 5 minutes"

do not mark it as incomplete merely because implementation details are missing.

NORMAL SOFTWARE TERMS:

Terms such as:
customer
user
login
payment
product
shopping cart
email
database

are normal software/domain terms.

Do NOT mark them ambiguous merely because they are present.

CONSISTENCY:

Do NOT mark consistency as NEEDS_REVIEW merely because both
"user" and "customer" appear.

Only mark consistency as NEEDS_REVIEW when the requirement itself
clearly uses conflicting terminology, conflicting behavior, or
contradictory conditions.

SEQUENCE:

A sequence such as:

"After payment, the system sends an email."

is NOT automatically a consistency problem.

COMPLETENESS:

Do not require the requirement to describe the entire system.

Judge completeness only according to the specific behavior stated
in the requirement.

VERIFIABILITY:

A requirement is verifiable when its stated behavior can reasonably
be tested or checked.

Do not require every requirement to contain a numerical threshold.
Only require measurable criteria when the requirement uses vague
performance or quality wording.

RECOMMENDATION:

Give a recommendation ONLY about issues actually identified in
this requirement.

Never introduce an unrelated issue.

Return EXACTLY this format:

CLARITY: <PASS or NEEDS_REVIEW or FAIL>
Reason: <one short reason>

COMPLETENESS: <PASS or NEEDS_REVIEW or FAIL>
Reason: <one short reason>

CONSISTENCY: <PASS or NEEDS_REVIEW or FAIL>
Reason: <one short reason>

VERIFIABILITY: <PASS or NEEDS_REVIEW or FAIL>
Reason: <one short reason>

MAIN ISSUE:
<one short sentence>

RECOMMENDATION:
<one short sentence>
"""

    try:

        response = requests.post(
            QWEN_API_URL,
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a strict software requirements "
                            "quality analyst. Follow the requested "
                            "format exactly."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 300
            },
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        choices = result.get("choices", [])

        if not choices:

            raise HTTPException(
                status_code=500,
                detail="Qwen returned no choices."
            )

        raw_text = (
            choices[0]
            .get("message", {})
            .get("content", "")
        )

        if not raw_text:

            raise HTTPException(
                status_code=500,
                detail="Qwen returned empty analysis."
            )

        structured = {

            "clarity": extract_dimension(
                raw_text,
                "CLARITY"
            ),

            "completeness": extract_dimension(
                raw_text,
                "COMPLETENESS"
            ),

            "consistency": extract_dimension(
                raw_text,
                "CONSISTENCY"
            ),

            "verifiability": extract_dimension(
                raw_text,
                "VERIFIABILITY"
            ),

            "main_issue": extract_text_section(
                raw_text,
                "MAIN ISSUE"
            ),

            "recommendation": extract_text_section(
                raw_text,
                "RECOMMENDATION"
            )
        }

        return {
            "structured": structured,
            "raw": raw_text
        }

    except requests.exceptions.ConnectionError:

        raise HTTPException(
            status_code=503,
            detail=(
                "Could not connect to Qwen. "
                "Start llama-server on port 8080."
            )
        )

    except requests.exceptions.Timeout:

        raise HTTPException(
            status_code=504,
            detail="Qwen took too long to respond."
        )

    except requests.exceptions.RequestException as error:

        raise HTTPException(
            status_code=500,
            detail=f"Qwen API error: {str(error)}"
        )


# ============================================================
# FINAL ANALYSIS FUSION
# ============================================================

def fuse_dimension(rule_result, qwen_result):

    rule_status = rule_result["status"]

    # Rule engine is authoritative.
    # Qwen provides supporting explanation only.

    if rule_status == "FAIL":

        return {
            "status": "FAIL",
            "source": "RULE + LLM",
            "rule_reason": rule_result["issues"],
            "llm_reason": qwen_result.get("reason", "")
        }

    if rule_status == "NEEDS_REVIEW":

        return {
            "status": "NEEDS_REVIEW",
            "source": "RULE + LLM",
            "rule_reason": rule_result["issues"],
            "llm_reason": qwen_result.get("reason", "")
        }

    return {
        "status": "PASS",
        "source": "RULE + LLM",
        "rule_reason": rule_result["issues"],
        "llm_reason": qwen_result.get("reason", "")
    }


# ============================================================
# FINAL ANALYSIS
# ============================================================

def create_final_analysis(rule_analysis, qwen_analysis):

    dimensions = [
        "correctness",
        "completeness",
        "consistency",
        "clarity",
        "unambiguity",
        "verifiability",
        "feasibility",
        "traceability"
    ]

    final_dimensions = {}

    for dimension in dimensions:

        rule_dimension = rule_analysis.get(
            dimension,
            {
                "status": "PASS",
                "issues": []
            }
        )

        qwen_dimension = qwen_analysis.get(
            dimension,
            {
                "status": "PASS",
                "reason": ""
            }
        )

        final_dimensions[dimension] = fuse_dimension(
            rule_dimension,
            qwen_dimension
        )

    statuses = [
        item["status"]
        for item in final_dimensions.values()
    ]

    if "FAIL" in statuses:

        overall_status = "FAIL"

    elif "NEEDS_REVIEW" in statuses:

        overall_status = "NEEDS_REVIEW"

    else:

        overall_status = "PASS"

    issues = []

    for dimension in dimensions:

        dimension_result = final_dimensions[dimension]

        if dimension_result["status"] != "PASS":

            issues.extend(
                dimension_result["rule_reason"]
            )

    if issues:

        main_issue = " ".join(
            dict.fromkeys(issues)
        )

        recommendation = (
            "Review the identified issues and revise "
            "the requirement to make the affected "
            "quality attributes clearer and testable."
        )

    else:

        main_issue = "No major quality issues were detected."

        recommendation = (
            "The requirement can be accepted for further review."
        )

    return {

        "overall_status": overall_status,

        "dimensions": final_dimensions,

        "main_issue": main_issue,

        "recommendation": recommendation
    }


# ============================================================
# ANALYZE SINGLE REQUIREMENT
# ============================================================

@app.post("/analyze")
def analyze(
    request: RequirementRequest,
    x_api_key: str | None = Header(default=None)
):

    verify_api_key(x_api_key)

    requirement = request.requirement.strip()

    if not requirement:

        raise HTTPException(
            status_code=400,
            detail="Requirement cannot be empty."
        )

    rule_analysis = get_structured_rule_analysis(
        requirement,
        {
            "source": request.source,
            "section_number": request.section_number
        }
    )

    qwen_response = run_qwen_analysis(
        requirement
    )

    qwen_analysis = qwen_response["structured"]

    final_analysis = create_final_analysis(
        rule_analysis,
        qwen_analysis
    )

    return {

        "requirement": requirement,

        "analysis": final_analysis,

        "rule_based": rule_analysis,

        "llm_analysis": qwen_analysis
    }


# ============================================================
# ANALYZE MULTIPLE REQUIREMENTS
# ============================================================

@app.post("/analyze-batch")
def analyze_batch(
    request: BatchRequirementRequest,
    x_api_key: str | None = Header(default=None)
):

    verify_api_key(x_api_key)

    if not request.requirements:

        raise HTTPException(
            status_code=400,
            detail="Requirements list cannot be empty."
        )

    results = []

    for index, requirement in enumerate(
        request.requirements,
        start=1
    ):

        requirement = requirement.strip()

        if not requirement:
            continue

        rule_analysis = get_structured_rule_analysis(
            requirement
        )

        qwen_response = run_qwen_analysis(
            requirement
        )

        qwen_analysis = qwen_response["structured"]

        final_analysis = create_final_analysis(
            rule_analysis,
            qwen_analysis
        )

        results.append({

            "requirement_id": f"R{index:03d}",

            "requirement": requirement,

            "analysis": final_analysis,

            "rule_based": rule_analysis,

            "llm_analysis": qwen_analysis
        })

    return {

        "total_requirements": len(results),

        "results": results
    }


# ============================================================
# SEMANTIC SIMILARITY
# ============================================================

@app.post("/similarity")
def similarity(
    request: SimilarityRequest,
    x_api_key: str | None = Header(default=None)
):

    verify_api_key(x_api_key)

    if len(request.requirements) < 2:

        raise HTTPException(
            status_code=400,
            detail="At least two requirements are required."
        )

    relationships = find_similar_requirements(
        request.requirements,
        request.threshold
    )

    return {

        "threshold": request.threshold,

        "relationships": relationships
    }