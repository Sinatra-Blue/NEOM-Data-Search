from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed(q):
    return model.encode([q], normalize_embeddings=True).astype("float32")
