from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.repository import Repository
import os
import sys
import importlib.util
import pathlib

router = APIRouter(prefix="/repos", tags=["graph"])

# Load graph-service modules (dash in folder name requires importlib)
_base = pathlib.Path(r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai\services\graph-service")

def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _base / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@router.get("/{repo_id}/graph")
async def get_graph(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GET /api/v1/repos/{repo_id}/graph
    Returns the full code graph (nodes + edges) for visualization.
    Triggers graph build if not already built.
    """
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
        _builder = _load("builder")
        _graph_builder = _load("graph_builder")

        # Build and store
        graph_data = _builder.build_graph_data(clone_path)
        _graph_builder.store_graph(repo_id, graph_data)

        # Return full graph for frontend visualization
        full_graph = _graph_builder.get_full_graph(repo_id)
        return {
            "repo_id": repo_id,
            "node_count": graph_data["node_count"],
            "edge_count": graph_data["edge_count"],
            "nodes": full_graph["nodes"],
            "edges": full_graph["edges"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph build failed: {str(e)}")


@router.get("/{repo_id}/graph/search")
async def search_graph(
    repo_id: str,
    q: str = Query(..., description="Function or class name to search"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GET /api/v1/repos/{repo_id}/graph/search?q=functionName
    Returns related nodes within 2 hops of the queried function/class.
    """
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
        _graph_builder = _load("graph_builder")
        related_nodes = _graph_builder.query_graph(repo_id, q, depth=2)
        return {
            "query": q,
            "related_nodes": related_nodes,
            "count": len(related_nodes),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph search failed: {str(e)}")
