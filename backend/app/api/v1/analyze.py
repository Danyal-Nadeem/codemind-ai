from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.repository import Repository, RepoStatus
from pydantic import BaseModel
import httpx
import os

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
        from services.github_service.cloner import clone_repo
        from services.github_service.file_walker import walk_repo
        from services.github_service.tech_detector import detect_tech_stack
        from services.github_service.parsers import parse_file
        import sys
        sys.path.insert(0, "/app")

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

        repo.status = RepoStatus.ready
        await db.commit()

        return AnalyzeResult(
            repo_id=repo_id,
            status="ready",
            files_count=len(files),
            chunks_count=len(all_chunks),
            tech_stack=tech_stack,
        )

    except Exception as e:
        repo.status = RepoStatus.failed
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))
