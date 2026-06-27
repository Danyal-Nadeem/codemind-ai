import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery
from services.github_service.cloner import clone_repo
from services.github_service.file_walker import walk_repo
from services.github_service.parsers import parse_file
from services.ai_service.embeddings.chunker import chunk_parsed_code
from services.ai_service.embeddings.embedder import embed_texts
from services.ai_service.embeddings.indexer import index_chunks

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("codemind", broker=REDIS_URL, backend=REDIS_URL)


@celery_app.task(name="embed_repo")
def embed_repo(repo_id: str, github_url: str):
    try:
        print(f"Cloning {github_url}...")
        clone_path = clone_repo(github_url, repo_id)

        print("Walking files...")
        files = walk_repo(clone_path)

        print("Parsing files...")
        all_parsed = []
        for file in files:
            parsed = parse_file(
                content=file["content"],
                filepath=file["path"],
                extension=file["extension"]
            )
            all_parsed.extend(parsed)

        print("Chunking...")
        chunks = chunk_parsed_code(all_parsed)

        print(f"Embedding {len(chunks)} chunks...")
        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)

        print("Indexing to Qdrant...")
        count = index_chunks(repo_id, chunks, embeddings)

        print(f"Done! Indexed {count} chunks")
        return {"status": "success", "indexed": count}

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "error": str(e)}
