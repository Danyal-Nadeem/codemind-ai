from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.schemas.repository import RepoCreate, RepoResponse

router = APIRouter(prefix="/repos", tags=["repos"])


def extract_repo_name(url: str) -> str:
    return url.rstrip("/").split("/")[-1].replace(".git", "")


@router.post("", response_model=RepoResponse, status_code=201)
async def create_repo(
    payload: RepoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = Repository(
        user_id=current_user.id,
        github_url=payload.github_url,
        name=extract_repo_name(payload.github_url),
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    return repo


@router.get("", response_model=list[RepoResponse])
async def list_repos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Repository).where(Repository.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{repo_id}", response_model=RepoResponse)
async def get_repo(
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
    return repo


@router.get("/{repo_id}/scan")
async def scan_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import importlib
    import os
    import sys
    
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.user_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    sys.path.insert(0, r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai")
    from services.github_service.cloner import clone_repo, CLONE_BASE_DIR
    
    clone_path = os.path.join(CLONE_BASE_DIR, repo_id)
    if not os.path.exists(clone_path):
        try:
            clone_path = clone_repo(repo.github_url, repo_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to clone repository: {str(e)}")
            
    try:
        scanner_module = importlib.import_module("services.scanner-service.scanner")
        scan_results = scanner_module.scan_repo_full(clone_path)
        return scan_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan execution failed: {str(e)}")
