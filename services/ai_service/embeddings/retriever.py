from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Filter
import os

COLLECTION_NAME = "codemind_vectors"

from services.ai_service.embeddings.indexer import get_client


def search_similar(
    repo_id: str,
    query_embedding: List[float],
    top_k: int = 5,
) -> List[Dict]:
    client = get_client()
    collection_name = f"{COLLECTION_NAME}_{repo_id}"

    try:
        results = client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            limit=top_k,
            with_payload=True,
        ).points
    except Exception:
        return []

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