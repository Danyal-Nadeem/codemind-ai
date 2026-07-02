import sys
import os
import importlib.util
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery
from services.github_service.cloner import CLONE_BASE_DIR

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("codemind", broker=REDIS_URL, backend=REDIS_URL)

# Load graph-service modules via importlib (dash in folder name)
_base = pathlib.Path(__file__).parent.parent / "services" / "graph-service"

def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _base / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_builder = _load("builder")
_graph_builder = _load("graph_builder")


@celery_app.task(name="build_graph")
def build_graph(repo_id: str):
    """
    Celery task: Extract code graph from cloned repo and store it.
    Triggered after ingest_repo completes.
    """
    try:
        clone_path = os.path.join(CLONE_BASE_DIR, repo_id)
        if not os.path.exists(clone_path):
            return {"status": "error", "error": f"Clone path not found: {clone_path}"}

        print(f"[graph_task] Building graph for repo {repo_id} at {clone_path}")
        graph_data = _builder.build_graph_data(clone_path)
        print(f"[graph_task] Extracted {graph_data['node_count']} nodes, {graph_data['edge_count']} edges")

        result = _graph_builder.store_graph(repo_id, graph_data)
        print(f"[graph_task] Stored via backend: {result['backend']}")

        return {
            "status": "success",
            "repo_id": repo_id,
            "node_count": graph_data["node_count"],
            "edge_count": graph_data["edge_count"],
            "backend": result["backend"],
        }

    except Exception as e:
        import traceback
        print(f"[graph_task] Error: {e}")
        traceback.print_exc()
        return {"status": "error", "error": str(e)}
