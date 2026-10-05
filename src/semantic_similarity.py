from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Load a pre-trained sentence embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


sentence1 = "The system shall process requests quickly."

sentence2 = "The application must provide a fast response."

sentence3 = "The system shall allow users to reset their password."


# Convert sentences into embeddings
embeddings = model.encode([
    sentence1,
    sentence2,
    sentence3
])


# Compare sentence 1 with sentence 2
similarity_1_2 = cosine_similarity(
    [embeddings[0]],
    [embeddings[1]]
)[0][0]


# Compare sentence 1 with sentence 3
similarity_1_3 = cosine_similarity(
    [embeddings[0]],
    [embeddings[2]]
)[0][0]


print("Sentence 1:")
print(sentence1)

print("\nSentence 2:")
print(sentence2)

print("\nSentence 3:")
print(sentence3)

print("\nSemantic Similarity")
print("-" * 40)

print(f"Sentence 1 vs Sentence 2: {similarity_1_2:.4f}")
print(f"Sentence 1 vs Sentence 3: {similarity_1_3:.4f}")