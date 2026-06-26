import os
import json
from typing import List


def detect_tech_stack(repo_path: str) -> List[str]:
    stack = []

    if os.path.exists(os.path.join(repo_path, "package.json")):
        stack.append("JavaScript/Node.js")
        try:
            with open(os.path.join(repo_path, "package.json")) as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "next" in deps:
                    stack.append("Next.js")
                if "react" in deps:
                    stack.append("React")
                if "express" in deps:
                    stack.append("Express.js")
                if "typescript" in deps or "@types/node" in deps:
                    stack.append("TypeScript")
        except Exception:
            pass

    if os.path.exists(os.path.join(repo_path, "requirements.txt")):
        stack.append("Python")
        try:
            with open(os.path.join(repo_path, "requirements.txt")) as f:
                content = f.read().lower()
                if "fastapi" in content:
                    stack.append("FastAPI")
                if "django" in content:
                    stack.append("Django")
                if "flask" in content:
                    stack.append("Flask")
                if "torch" in content or "tensorflow" in content:
                    stack.append("ML/AI")
        except Exception:
            pass

    if os.path.exists(os.path.join(repo_path, "go.mod")):
        stack.append("Go")

    if os.path.exists(os.path.join(repo_path, "Cargo.toml")):
        stack.append("Rust")

    if os.path.exists(os.path.join(repo_path, "pom.xml")):
        stack.append("Java/Maven")

    if os.path.exists(os.path.join(repo_path, "docker-compose.yml")) or \
       os.path.exists(os.path.join(repo_path, "Dockerfile")):
        stack.append("Docker")

    return list(set(stack))
