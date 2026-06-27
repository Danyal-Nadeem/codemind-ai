from typing import List, Dict
from qdrant_client import QdrantClient
import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "codemind_vectors"


def get_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def search_similar(
    repo_id: str,
    query_embedding: List[float],
    top_k: int = 5,
) -> List[Dict]:
    client = get_client()
    collection_name = f"{COLLECTION_NAME}_{repo_id}"

    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "text": hit.payload["text"],
            "filepath": hit.payload["filepath"],
            "start_line": hit.payload["start_line"],
            "end_line": hit.payload["end_line"],
            "chunk_type": hit.payload.get("chunk_type", ""),
            "name": hit.payload.get("name", ""),
            "score": hit.score,
        }
        for hit in results
    ]
