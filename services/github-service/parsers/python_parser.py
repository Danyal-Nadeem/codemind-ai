import ast
from typing import List, Dict


def parse_python_file(content: str, filepath: str) -> List[Dict]:
    chunks = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return chunks

    lines = content.split("\n")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno - 1
            end = node.end_lineno
            code = "\n".join(lines[start:end])

            chunks.append({
                "type": "function",
                "name": node.name,
                "filepath": filepath,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "code": code,
            })

        elif isinstance(node, ast.ClassDef):
            start = node.lineno - 1
            end = node.end_lineno
            code = "\n".join(lines[start:end])

            chunks.append({
                "type": "class",
                "name": node.name,
                "filepath": filepath,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "code": code,
            })

    return chunks
