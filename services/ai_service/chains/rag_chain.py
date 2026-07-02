from typing import List, Dict, AsyncGenerator
import os
import sys
import importlib.util
import pathlib

sys.path.insert(0, r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai")

from services.ai_service.embeddings.embedder import embed_single
from services.ai_service.prompts.chat_prompt import CHAT_SYSTEM_PROMPT, CHAT_USER_TEMPLATE

# Load graph-service retriever dynamically due to dash in directory name
_base_dir = pathlib.Path(r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai")
_retriever_path = _base_dir / "services" / "graph-service" / "retriever.py"
_spec = importlib.util.spec_from_file_location("graph_retriever", _retriever_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

graph_aware_retrieve = _mod.graph_aware_retrieve
format_graph_context = _mod.format_graph_context


def format_context(chunks: List[Dict]) -> str:
    context_parts = []
    for chunk in chunks:
        citation = f"[{chunk['filepath']}:{chunk['start_line']}-{chunk['end_line']}]"
        context_parts.append(f"{citation}\n{chunk['text']}")
    return "\n\n---\n\n".join(context_parts)


async def rag_chat(
    repo_id: str,
    question: str,
    chat_history: List[Dict] = [],
    top_k: int = 5,
) -> AsyncGenerator[str, None]:
    # Graph-aware retrieve
    retrieve_res = graph_aware_retrieve(repo_id, question, top_k)
    vector_chunks = retrieve_res["vector_chunks"]
    graph_nodes = retrieve_res["graph_nodes"]

    vector_context = format_context(vector_chunks)
    graph_context = format_graph_context(graph_nodes)

    context = vector_context
    if graph_context:
        context += "\n\n" + graph_context

    answer = f"Based on the codebase:\n\n{context}"

    for word in answer.split(" "):
        yield word + " "


async def rag_chat_full(
    repo_id: str,
    question: str,
    chat_history: List[Dict] = [],
    top_k: int = 5,
) -> Dict:
    # Graph-aware retrieve
    retrieve_res = graph_aware_retrieve(repo_id, question, top_k)
    vector_chunks = retrieve_res["vector_chunks"]
    graph_nodes = retrieve_res["graph_nodes"]

    vector_context = format_context(vector_chunks)
    graph_context = format_graph_context(graph_nodes)

    context = vector_context
    if graph_context:
        context += "\n\n" + graph_context

    answer = f"Based on the codebase, here are the relevant sections:\n\n{context}"

    return {
        "answer": answer,
        "sources": [
            {
                "filepath": c["filepath"],
                "start_line": c["start_line"],
                "end_line": c["end_line"],
                "score": c["score"],
            }
            for c in vector_chunks
        ],
    }