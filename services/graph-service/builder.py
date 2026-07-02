"""
builder.py — AST-based function call and class dependency extractor.
Supports Python files via ast module; JS/TS via regex patterns.
"""
import os
import ast
import re
from typing import List, Dict

IGNORE_DIRS = {".git", "__pycache__", "node_modules", "venv", ".venv", ".next", "dist", "build"}


def extract_python_graph(filepath: str, content: str) -> Dict:
    """Extract nodes (functions/classes) and edges (calls/inherits) from Python source."""
    nodes = []
    edges = []

    try:
        tree = ast.parse(content, filename=filepath)
    except SyntaxError:
        return {"nodes": nodes, "edges": edges}

    # Collect class names for this file
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            nodes.append({
                "id": f"{filepath}::{node.name}",
                "name": node.name,
                "type": "class",
                "filepath": filepath,
                "line": node.lineno,
            })
            # Inheritance edges
            for base in node.bases:
                base_name = ""
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr
                if base_name:
                    edges.append({
                        "source": f"{filepath}::{node.name}",
                        "target": base_name,
                        "type": "inherits",
                    })

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Determine parent class if exists
            parent_class = None
            for cls_node in ast.walk(tree):
                if isinstance(cls_node, ast.ClassDef):
                    for item in ast.walk(cls_node):
                        if item is node:
                            parent_class = cls_node.name
                            break

            node_id = f"{filepath}::{parent_class}.{node.name}" if parent_class else f"{filepath}::{node.name}"
            nodes.append({
                "id": node_id,
                "name": node.name,
                "type": "method" if parent_class else "function",
                "filepath": filepath,
                "line": node.lineno,
                "parent": parent_class,
            })

            # Function call edges
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    callee = ""
                    if isinstance(child.func, ast.Name):
                        callee = child.func.id
                    elif isinstance(child.func, ast.Attribute):
                        callee = child.func.attr
                    if callee and callee != node.name:
                        edges.append({
                            "source": node_id,
                            "target": callee,
                            "type": "calls",
                        })

    return {"nodes": nodes, "edges": edges}


def extract_js_graph(filepath: str, content: str) -> Dict:
    """Extract function/class definitions and calls from JS/TS using regex."""
    nodes = []
    edges = []
    lines = content.splitlines()

    # Match: function foo(), const foo = () =>, class Foo
    func_pattern = re.compile(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\(|class\s+(\w+))')
    call_pattern = re.compile(r'(\w+)\s*\(')

    current_func = None
    for i, line in enumerate(lines):
        match = func_pattern.search(line)
        if match:
            name = match.group(1) or match.group(2) or match.group(3)
            node_type = "class" if match.group(3) else "function"
            node_id = f"{filepath}::{name}"
            nodes.append({
                "id": node_id,
                "name": name,
                "type": node_type,
                "filepath": filepath,
                "line": i + 1,
            })
            current_func = node_id

        if current_func:
            for call_match in call_pattern.finditer(line):
                callee = call_match.group(1)
                # Skip keywords and self-calls
                skip = {"if", "for", "while", "switch", "catch", "return", "typeof", "instanceof"}
                if callee not in skip and f"::{callee}" not in current_func:
                    edges.append({
                        "source": current_func,
                        "target": callee,
                        "type": "calls",
                    })

    return {"nodes": nodes, "edges": edges}


def build_graph_data(repo_path: str) -> Dict:
    """Walk the repo and extract a combined graph of nodes and edges."""
    all_nodes = []
    all_edges = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in {".py", ".js", ".ts", ".tsx", ".jsx"}:
                continue
            abs_path = os.path.join(root, filename)
            rel_path = os.path.relpath(abs_path, repo_path).replace("\\", "/")
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if ext == ".py":
                    result = extract_python_graph(rel_path, content)
                else:
                    result = extract_js_graph(rel_path, content)
                all_nodes.extend(result["nodes"])
                all_edges.extend(result["edges"])
            except Exception:
                pass

    # Deduplicate nodes by id
    seen_ids = set()
    unique_nodes = []
    for n in all_nodes:
        if n["id"] not in seen_ids:
            seen_ids.add(n["id"])
            unique_nodes.append(n)

    return {
        "nodes": unique_nodes,
        "edges": all_edges,
        "node_count": len(unique_nodes),
        "edge_count": len(all_edges),
    }
