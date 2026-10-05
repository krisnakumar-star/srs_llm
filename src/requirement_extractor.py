import pymupdf
import re
import json
import os


# PDF location
pdf_path = "data/srs/online shopping system.pdf"

# Output location
output_path = "data/extracted/online_shopping_requirements.json"


# Open PDF
doc = pymupdf.open(pdf_path)


# Extract text from all pages
full_text = ""

for page in doc:
    full_text += page.get_text() + "\n"


print("PDF text extracted.")
print("Characters:", len(full_text))


# Clean extracted requirement text
def clean_requirement(text):
    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Put spaces around line breaks
    text = text.replace("\n", " ")

    # Remove repeated spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()

pattern = r"3\.1\.(\d+)\s+([^\n]+)"

matches = list(re.finditer(pattern, full_text))


print("\nRequirements found:", len(matches))


# Store extracted requirements
requirements = []


# Extract each requirement
for index, match in enumerate(matches):

    requirement_number = match.group(1)
    title = match.group(2).strip()

    start = match.end()

    if index + 1 < len(matches):

        end = matches[index + 1].start()

    else:

        next_section = re.search(
            r"\n\s*3\.2\s+Non-Functional Requirements",
            full_text[start:]
        )

        if next_section:
            end = start + next_section.start()
        else:
            end = len(full_text)

    requirement_text = clean_requirement(
        full_text[start:end]
    )


    requirement = {
        "requirement_id": f"R{index + 1:03}",
        "section_number": f"3.1.{requirement_number}",
        "title": title,
        "source": "online shopping system.pdf",
        "requirement": requirement_text
    }

    requirements.append(requirement)


# Create output folder if it doesn't exist
os.makedirs(
    os.path.dirname(output_path),
    exist_ok=True
)


# Save requirements to JSON
with open(
    output_path,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        requirements,
        file,
        indent=4,
        ensure_ascii=False
    )


print("\nRequirements saved successfully.")

print("Output:", output_path)