from typing import List
from sentence_transformers import SentenceTransformer
import os

model = SentenceTransformer('all-MiniLM-L6-v2')

EMBEDDING_DIM = 384


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    batch_size = 100
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = model.encode(batch, convert_to_numpy=True).tolist()
        all_embeddings.extend(embeddings)

    return all_embeddings


def embed_single(text: str) -> List[float]:
    return model.encode([text], convert_to_numpy=True)[0].tolist()