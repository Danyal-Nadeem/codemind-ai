"""
retriever.py — Graph-aware retrieval: combines vector search results with
graph traversal to return richer context for RAG chain.
"""
import sys
import os
from typing import List, Dict

sys.path.insert(0, r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai")

from services.ai_service.embeddings.embedder import embed_single
from services.ai_service.embeddings.retriever import search_similar

# graph-service folder has a dash, so we use importlib
import importlib.util as _ilu
import pathlib as _pl
_gb_path = _pl.Path(r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai\services\graph-service\graph_builder.py")
_gb_spec = _ilu.spec_from_file_location("graph_builder", _gb_path)
_gb_mod = _ilu.module_from_spec(_gb_spec)
_gb_spec.loader.exec_module(_gb_mod)
query_graph = _gb_mod.query_graph


def extract_function_names(question: str) -> List[str]:
    """Naive extraction: find likely function/class names from question."""
    import re
    # Match CamelCase, snake_case, or quoted identifiers
    candidates = re.findall(r'\b([A-Z][a-zA-Z0-9]+|[a-z_][a-z_0-9]+(?:_[a-z_0-9]+)+)\b', question)
    # Filter out common stopwords
    stopwords = {"what", "how", "where", "when", "does", "the", "this", "that", "which"}
    return [c for c in candidates if c.lower() not in stopwords][:5]


def graph_aware_retrieve(
    repo_id: str,
    question: str,
    top_k: int = 5,
) -> Dict:
    """
    Returns combined context:
    - vector_chunks: semantic matches from Qdrant
    - graph_nodes: related code entities from the graph
    """
    # 1. Vector search (existing Week 3/4 system)
    query_embedding = embed_single(question)
    vector_chunks = search_similar(repo_id, query_embedding, top_k)

    # 2. Graph traversal for mentioned function/class names
    graph_nodes = []
    names = extract_function_names(question)
    seen = set()
    for name in names:
        related = query_graph(repo_id, name, depth=2)
        for node in related:
            key = node.get("name", "")
            if key and key not in seen:
                seen.add(key)
                graph_nodes.append(node)

    return {
        "vector_chunks": vector_chunks,
        "graph_nodes": graph_nodes[:15],  # cap to avoid context overflow
    }


def format_graph_context(graph_nodes: List[Dict]) -> str:
    """Format graph nodes into readable context text for the LLM."""
    if not graph_nodes:
        return ""
    lines = ["## Related Code Entities (Graph Context)"]
    for node in graph_nodes:
        lines.append(
            f"- [{node.get('type', 'node').upper()}] `{node.get('name')}` "
            f"in `{node.get('filepath', '')}:{node.get('line', '')}`"
        )
    return "\n".join(lines)
