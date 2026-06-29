import os
import shutil
import stat
from git import Repo
from pathlib import Path

CLONE_BASE_DIR = "/tmp/codemind_repos"


def force_rmtree(path: str):
    if not os.path.exists(path):
        return
    def _onerror(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    shutil.rmtree(path, onerror=_onerror)


def clone_repo(github_url: str, repo_id: str) -> str:
    clone_path = os.path.join(CLONE_BASE_DIR, repo_id)

    if os.path.exists(clone_path):
        force_rmtree(clone_path)

    os.makedirs(CLONE_BASE_DIR, exist_ok=True)
    Repo.clone_from(github_url, clone_path)

    return clone_path


def delete_repo(repo_id: str):
    clone_path = os.path.join(CLONE_BASE_DIR, repo_id)
    if os.path.exists(clone_path):
        force_rmtree(clone_path)
