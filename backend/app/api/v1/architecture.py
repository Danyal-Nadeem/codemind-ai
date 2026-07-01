from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.repository import Repository
import os
import sys

router = APIRouter(prefix="/repos", tags=["architecture"])

@router.get("/{repo_id}/architecture")
async def get_architecture(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Retrieve repository and check ownership
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.user_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get clone path
    sys.path.insert(0, r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai")
    from services.github_service.cloner import clone_repo, CLONE_BASE_DIR
    
    clone_path = os.path.join(CLONE_BASE_DIR, repo_id)
    if not os.path.exists(clone_path):
        try:
            clone_path = clone_repo(repo.github_url, repo_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to clone repository: {str(e)}")

    # Import generator
    from services.ai_service.chains.arch_generator import generate_architecture_data
    try:
        data = generate_architecture_data(clone_path, repo_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate architecture: {str(e)}")
