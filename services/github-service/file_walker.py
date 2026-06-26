import os
from pathlib import Path
from typing import List, Dict

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".next",
    "dist", "build", ".venv", "venv", ".env"
}

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".go", ".rs", ".cpp", ".c", ".cs"
}


def walk_repo(repo_path: str) -> List[Dict]:
    files = []

    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for filename in filenames:
            filepath = os.path.join(root, filename)
            ext = Path(filename).suffix.lower()

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            relative_path = os.path.relpath(filepath, repo_path)

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                files.append({
                    "path": relative_path.replace("\\", "/"),
                    "extension": ext,
                    "size": len(content),
                    "lines": content.count("\n") + 1,
                    "content": content,
                })
            except Exception:
                continue

    return files
