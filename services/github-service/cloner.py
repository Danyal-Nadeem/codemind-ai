import os
import shutil
from git import Repo
from pathlib import Path

CLONE_BASE_DIR = "/tmp/codemind_repos"


def clone_repo(github_url: str, repo_id: str) -> str:
    clone_path = os.path.join(CLONE_BASE_DIR, repo_id)

    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)

    os.makedirs(CLONE_BASE_DIR, exist_ok=True)
    Repo.clone_from(github_url, clone_path)

    return clone_path


def delete_repo(repo_id: str):
    clone_path = os.path.join(CLONE_BASE_DIR, repo_id)
    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)
