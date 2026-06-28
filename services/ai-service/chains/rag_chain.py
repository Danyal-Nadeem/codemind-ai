from typing import List, Dict, AsyncGenerator
from openai import AsyncOpenAI
import os
from services.ai_service.embeddings.embedder import embed_single
from services.ai_service.embeddings.retriever import search_similar
from services.ai_service.prompts.chat_prompt import CHAT_SYSTEM_PROMPT, CHAT_USER_TEMPLATE

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

    user_message = CHAT_USER_TEMPLATE.format(
        context=context,
        question=question,
    )

    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        *chat_history,
        {"role": "user", "content": user_message},
    ]

    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True,
        temperature=0.1,
        max_tokens=1500,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


async def rag_chat_full(
    repo_id: str,
    question: str,
    chat_history: List[Dict] = [],
    top_k: int = 5,
) -> Dict:
    query_embedding = embed_single(question)
    chunks = search_similar(repo_id, query_embedding, top_k)
    context = format_context(chunks)

    user_message = CHAT_USER_TEMPLATE.format(
        context=context,
        question=question,
    )

    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        *chat_history,
        {"role": "user", "content": user_message},
    ]

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.1,
        max_tokens=1500,
    )

    answer = response.choices[0].message.content

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
