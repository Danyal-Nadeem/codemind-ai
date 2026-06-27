from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.repository import Repository
from pydantic import BaseModel
from typing import List
import sys
import os

router = APIRouter(prefix="/search", tags=["search"])


class SearchResult(BaseModel):
    filepath: str
    start_line: int
    end_line: int
    chunk_type: str
    name: str
    score: float
    text: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]


@router.get("/{repo_id}", response_model=SearchResponse)
async def search_repo(
    repo_id: str,
    q: str = Query(..., description="Search query"),
    top_k: int = Query(5, description="Number of results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.user_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        sys.path.insert(0, "/app")
        from services.ai_service.embeddings.embedder import embed_single
        from services.ai_service.embeddings.retriever import search_similar

        query_embedding = embed_single(q)
        results = search_similar(repo_id, query_embedding, top_k)

        return SearchResponse(
            query=q,
            results=[SearchResult(**r) for r in results],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
