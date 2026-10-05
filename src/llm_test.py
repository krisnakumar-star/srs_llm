import subprocess


# ---------------------------------
# Qwen model
# ---------------------------------

model_path = r".\models\qwen2.5-1.5b-instruct-q4_k_m.gguf"


# ---------------------------------
# Real requirement from R001
# ---------------------------------

requirement = (
    "If customer wants to buy the product then he/she must be registered, "
    "unregistered user can’t go to the shopping cart."
)


# ---------------------------------
# Prompt
# ---------------------------------

prompt = f"""
You are a software requirements quality checker.

Analyze ONLY this requirement:

{requirement}

Evaluate these four dimensions:

1. CLARITY
2. COMPLETENESS
3. CONSISTENCY
4. VERIFIABILITY

IMPORTANT:

- Do not invent missing information.
- If information is missing, use NEEDS_REVIEW.
- Identify vague, unclear, incomplete, or inconsistent wording.
- Check whether the requirement can be objectively tested.
- Pay attention to inconsistent terminology such as "customer" and "user".

Return exactly:

CLARITY: <PASS or NEEDS_REVIEW or FAIL>
Reason: <short reason>

COMPLETENESS: <PASS or NEEDS_REVIEW or FAIL>
Reason: <short reason>

CONSISTENCY: <PASS or NEEDS_REVIEW or FAIL>
Reason: <short reason>

VERIFIABILITY: <PASS or NEEDS_REVIEW or FAIL>
Reason: <short reason>

MAIN ISSUES:
- <issue>
- <issue>

RECOMMENDATION:
<short recommendation>

Do not discuss architecture, hardware, implementation, or scalability.
"""


# ---------------------------------
# Run Qwen
# ---------------------------------

print("Starting Qwen...")
print("Please wait...\n")


subprocess.run(
    [
        "llama-cli",
        "-m",
        model_path,
        "-p",
        prompt,
        "-n",
        "250"
    ]
)


print("\nQwen test finished.")