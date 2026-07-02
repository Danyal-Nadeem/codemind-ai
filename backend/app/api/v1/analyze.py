from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.repository import Repository, RepoStatus
from pydantic import BaseModel
import sys
import os

# Services path add karo
sys.path.insert(0, r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai")

from services.github_service.cloner import clone_repo
from services.github_service.file_walker import walk_repo
from services.github_service.tech_detector import detect_tech_stack
from services.github_service.parsers import parse_file
from services.ai_service.embeddings.chunker import chunk_parsed_code
from services.ai_service.embeddings.embedder import embed_texts
from services.ai_service.embeddings.indexer import index_chunks

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeResult(BaseModel):
    repo_id: str
    status: str
    files_count: int = 0
    chunks_count: int = 0
    tech_stack: list = []


@router.post("/{repo_id}", response_model=AnalyzeResult)
async def analyze_repo(
    repo_id: str,
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

    repo.status = RepoStatus.processing
    await db.commit()

    try:
        clone_path = clone_repo(repo.github_url, repo_id)
        files = walk_repo(clone_path)
        tech_stack = detect_tech_stack(clone_path)

        all_chunks = []
        for file in files:
            chunks = parse_file(
                content=file["content"],
                filepath=file["path"],
                extension=file["extension"]
            )
            all_chunks.extend(chunks)

        # Chunker -> embedder -> indexer
        chunks = chunk_parsed_code(all_chunks)
        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)
        indexed_count = index_chunks(repo_id, chunks, embeddings)

        # Build and store Code Graph
        try:
            import importlib.util
            import pathlib
            _base_graph = pathlib.Path(r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai\services\graph-service")
            
            # Load graph-service modules
            _spec_b = importlib.util.spec_from_file_location("builder", _base_graph / "builder.py")
            _mod_b = importlib.util.module_from_spec(_spec_b)
            _spec_b.loader.exec_module(_mod_b)
            
            _spec_gb = importlib.util.spec_from_file_location("graph_builder", _base_graph / "graph_builder.py")
            _mod_gb = importlib.util.module_from_spec(_spec_gb)
            _spec_gb.loader.exec_module(_mod_gb)
            
            graph_data = _mod_b.build_graph_data(clone_path)
            _mod_gb.store_graph(repo_id, graph_data)
            print(f"[analyze] Successfully stored code graph for {repo_id}")
        except Exception as ge:
            print(f"[analyze] Graph extraction failed: {ge}")

        repo.status = RepoStatus.ready
        await db.commit()

        return AnalyzeResult(
            repo_id=repo_id,
            status="ready",
            files_count=len(files),
            chunks_count=indexed_count,
            tech_stack=tech_stack,
        )

    except Exception as e:
        repo.status = RepoStatus.failed
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))