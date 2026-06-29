from typing import List, Dict, AsyncGenerator
import os
import sys

sys.path.insert(0, r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai")

from services.ai_service.embeddings.embedder import embed_single
from services.ai_service.embeddings.retriever import search_similar
from services.ai_service.prompts.chat_prompt import CHAT_SYSTEM_PROMPT, CHAT_USER_TEMPLATE


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
    query_embedding = embed_single(question)
    chunks = search_similar(repo_id, query_embedding, top_k)
    context = format_context(chunks)

    answer = f"Based on the codebase:\n\n{context}"

    for word in answer.split(" "):
        yield word + " "


async def rag_chat_full(
    repo_id: str,
    question: str,
    chat_history: List[Dict] = [],
    top_k: int = 5,
) -> Dict:
    query_embedding = embed_single(question)
    chunks = search_similar(repo_id, query_embedding, top_k)
    context = format_context(chunks)

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
            for c in chunks
        ],
    }