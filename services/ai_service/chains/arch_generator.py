import os
import sys
import json
import httpx
from typing import Dict, List
from openai import OpenAI

# Add project root to path
sys.path.insert(0, r"C:\Users\danya\OneDrive\Desktop\PROJECTS\codemind-ai")

from services.github_service.tech_detector import detect_tech_stack
from services.ai_service.embeddings.indexer import get_client
from services.ai_service.prompts.arch_prompt import ARCH_SYSTEM_PROMPT, ARCH_USER_TEMPLATE

def build_file_tree(repo_path: str, max_files: int = 120) -> str:
    tree_lines = []
    count = 0
    ignore_dirs = {".git", "__pycache__", "node_modules", "venv", ".venv", ".next", "build", "dist"}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        rel_dir = os.path.relpath(root, repo_path)
        if rel_dir == ".":
            indent = ""
        else:
            depth = len(rel_dir.split(os.sep))
            indent = "  " * depth
            tree_lines.append(f"{indent}{os.path.basename(root)}/")
        
        for f in files:
            if count >= max_files:
                break
            file_indent = "  " * (len(rel_dir.split(os.sep)) + 1) if rel_dir != "." else "  "
            tree_lines.append(f"{file_indent}{f}")
            count += 1
        if count >= max_files:
            tree_lines.append("  ... (file tree truncated)")
            break
    return "\n".join(tree_lines)

def get_qdrant_chunks(repo_id: str, limit: int = 15) -> str:
    client = get_client()
    collection_name = f"codemind_vectors_{repo_id}"
    chunks = []
    try:
        if client.collection_exists(collection_name):
            points, _ = client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            for p in points:
                payload = p.payload
                chunks.append(f"File: {payload.get('filepath')}\nContent:\n{payload.get('text')}\n---")
        if not chunks:
            return ""
        return "\n".join(chunks)
    except Exception:
        return ""

def get_repo_chunks_fallback(repo_path: str) -> str:
    chunks = []
    important_files = [
        "backend/app/main.py", "backend/app/api/v1/repos.py",
        "frontend/package.json", "frontend/app/page.tsx",
        "requirements.txt", "package.json"
    ]
    for rel_file in important_files:
        abs_path = os.path.join(repo_path, rel_file)
        if os.path.exists(abs_path):
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(800)
                chunks.append(f"File: {rel_file}\nContent:\n{content}\n---")
            except Exception:
                pass
    return "\n".join(chunks)

def generate_fallback_mermaid(tech_stack: List[str]) -> str:
    frontend_label = "Frontend (Web Client)"
    backend_label = "Backend (API Server)"
    db_label = "Database (Storage)"
    
    for tech in tech_stack:
        t_lower = tech.lower()
        if "next" in t_lower or "react" in t_lower:
            frontend_label = f"Frontend ({tech})"
        if "fastapi" in t_lower or "flask" in t_lower or "django" in t_lower:
            backend_label = f"Backend ({tech})"
        if "postgres" in t_lower or "mysql" in t_lower or "sqlite" in t_lower or "mongo" in t_lower:
            db_label = f"Database ({tech})"
            
    mermaid = f"""graph TD
    subgraph Client [User Interface]
        web["{frontend_label}"]
    end
    subgraph Server [Application Logic]
        api["{backend_label}"]
        ai["AI Integration (LLM/Embeddings)"]
    end
    subgraph Storage [Data Storage]
        db[("{db_label}")]
    end
    
    web -->|HTTP REST Requests| api
    api -->|Query/Save| db
    api -->|Retrieval/Chat| ai
"""
    return mermaid

def generate_fallback_readme(tech_stack: List[str], file_tree: str, mermaid_diagram: str) -> str:
    techs_str = ", ".join(tech_stack) if tech_stack else "Python, Javascript"
    readme = f"""# CodeMind AI Audited Project

## Overview
This repository has been audited and mapped by CodeMind AI. It contains a software application leveraging modern architectural practices.

## Features
- Codebase Search & Semantics RAG Chat
- Security vulnerability detection & Quality Scans
- Auto-generated architectural mapping

## Tech Stack
Identified technologies: {techs_str}

## Architecture
Below is the visual architectural diagram of the system flow:

```mermaid
{mermaid_diagram}
```

## Setup & Installation
1. Clone the repository and navigate to its root directory.
2. Initialize environment parameters (`.env`).
3. Deploy services and start applications.
"""
    return readme

def parse_json_response(text: str) -> Dict[str, str]:
    text_stripped = text.strip()
    # Strip markdown code wrapper if present
    if text_stripped.startswith("```json"):
        text_stripped = text_stripped[7:]
    if text_stripped.startswith("```"):
        text_stripped = text_stripped[3:]
    if text_stripped.endswith("```"):
        text_stripped = text_stripped[:-3]
    text_stripped = text_stripped.strip()
    
    try:
        data = json.loads(text_stripped)
        if "mermaid_diagram" in data and "readme_content" in data:
            return data
    except Exception:
        pass
        
    # Manual extraction fallback if JSON parsing fails
    mermaid_diagram = ""
    readme_content = ""
    
    # Try finding mermaid code block
    import re
    mermaid_match = re.search(r"```mermaid\s*(.*?)\s*```", text, re.DOTALL)
    if mermaid_match:
        mermaid_diagram = mermaid_match.group(1).strip()
        readme_content = text.replace(mermaid_match.group(0), "").strip()
    else:
        # Split by keys or use defaults
        mermaid_diagram = "graph TD\n    A[App] --> B[Database]"
        readme_content = text
        
    return {
        "mermaid_diagram": mermaid_diagram,
        "readme_content": readme_content
    }

def generate_architecture_data(repo_path: str, repo_id: str) -> Dict[str, str]:
    # 1. Gather context
    tech_stack = detect_tech_stack(repo_path)
    file_tree = build_file_tree(repo_path)
    
    # Try getting chunks from Qdrant first, fallback to files
    code_chunks = get_qdrant_chunks(repo_id)
    if not code_chunks:
        code_chunks = get_repo_chunks_fallback(repo_path)
        
    # 2. Check API Keys
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    prompt_user = ARCH_USER_TEMPLATE.format(
        tech_stack=", ".join(tech_stack) if tech_stack else "None detected",
        file_tree=file_tree,
        code_chunks=code_chunks
    )
    
    # Try OpenAI
    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": ARCH_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_user}
                ],
                response_format={"type": "json_object"},
                max_tokens=1500,
                temperature=0.2
            )
            raw_text = response.choices[0].message.content
            return parse_json_response(raw_text)
        except Exception as e:
            print(f"OpenAI Architecture Generation error: {e}")
            
    # Try Gemini
    elif gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": ARCH_SYSTEM_PROMPT + "\n\n" + prompt_user}]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 1500,
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            res = httpx.post(url, headers=headers, json=payload, timeout=25.0)
            if res.status_code == 200:
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return parse_json_response(raw_text)
        except Exception as e:
            print(f"Gemini Architecture Generation error: {e}")
            
    # 3. Fallback Generation
    fallback_mermaid = generate_fallback_mermaid(tech_stack)
    fallback_readme = generate_fallback_readme(tech_stack, file_tree, fallback_mermaid)
    
    return {
        "mermaid_diagram": fallback_mermaid,
        "readme_content": fallback_readme
    }
