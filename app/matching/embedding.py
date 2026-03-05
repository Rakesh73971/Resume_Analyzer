from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load once (important)
model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str):
    return model.encode(text)


def compute_similarity(vec1, vec2):
    return float(cosine_similarity([vec1], [vec2])[0][0])