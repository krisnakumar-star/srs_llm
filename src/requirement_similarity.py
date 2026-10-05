from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


model = SentenceTransformer("all-MiniLM-L6-v2")


requirements = [
    "The system shall allow users to reset their password.",
    "Users must be able to recover their account password.",
    "The system shall allow customers to track their orders.",
    "The application shall display the current order status."
]


embeddings = model.encode(requirements)

similarity_matrix = cosine_similarity(embeddings)


print("\nRequirement Similarity Analysis")
print("=" * 60)

for i in range(len(requirements)):
    for j in range(i + 1, len(requirements)):

        score = similarity_matrix[i][j]

        print(f"\nR{i + 1} ↔ R{j + 1}")
        print(f"Similarity: {score:.4f}")

        if score >= 0.60:
            print("⚠ Potentially related requirements")
        else:
            print("✓ No strong similarity detected")