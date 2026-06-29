from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct
)
import uuid
import os

COLLECTION_NAME = "codemind_vectors"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2

# In-memory Qdrant client (no Docker needed)
_client = None

def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(":memory:")
    return _client


def create_collection(repo_id: str):
    client = get_client()
    collection_name = f"{COLLECTION_NAME}_{repo_id}"

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
    return collection_name


def index_chunks(repo_id: str, chunks: List[Dict], embeddings: List[List[float]]):
    client = get_client()
    collection_name = create_collection(repo_id)

    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "filepath": chunk["filepath"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "chunk_type": chunk.get("chunk_type", "unknown"),
                    "name": chunk.get("name", ""),
                    "repo_id": repo_id,
                },
            )
        )

    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=collection_name,
            points=points[i:i + batch_size],
        )

    return len(points)