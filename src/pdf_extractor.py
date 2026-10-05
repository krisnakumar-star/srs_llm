import pymupdf

pdf_path = "data/srs/online shopping system.pdf"

doc = pymupdf.open(pdf_path)

print("Total pages:", len(doc))

for page_number, page in enumerate(doc):
    text = page.get_text()

    print("\n" + "=" * 60)
    print("PAGE", page_number + 1)
    print("=" * 60)

    print(text[:1000])