import sys
import os
sys.path.insert(0, r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai")
sys.path.insert(0, r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai\backend")

from celery import Celery
from services.github_service.cloner import clone_repo, delete_repo
from services.github_service.file_walker import walk_repo
from services.github_service.tech_detector import detect_tech_stack
from services.github_service.parsers import parse_file

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("codemind", broker=REDIS_URL, backend=REDIS_URL)


@celery_app.task(name="ingest_repo")
def ingest_repo(repo_id: str, github_url: str):
    try:
        print(f"Cloning {github_url}...")
        clone_path = clone_repo(github_url, repo_id)

        print("Walking files...")
        files = walk_repo(clone_path)

        print("Detecting tech stack...")
        tech_stack = detect_tech_stack(clone_path)

        print("Parsing files...")
        all_chunks = []
        for file in files:
            chunks = parse_file(
                content=file["content"],
                filepath=file["path"],
                extension=file["extension"]
            )
            all_chunks.extend(chunks)

        print(f"Done! Files: {len(files)}, Chunks: {len(all_chunks)}, Stack: {tech_stack}")

        return {
            "status": "success",
            "repo_id": repo_id,
            "files_count": len(files),
            "chunks_count": len(all_chunks),
            "tech_stack": tech_stack,
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "error": str(e)}
