import os
import ast
import re
from typing import List, Dict, Set, Tuple

# Ignore patterns for folder walking
IGNORE_DIRS = {
    ".git", "__pycache__", "venv", ".venv", "node_modules", 
    "tests", "test", "dist", ".next", "build", "target", "out"
}
IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock"
}

def should_ignore(path: str) -> bool:
    parts = PathParts(path)
    return any(p in IGNORE_DIRS for p in parts)

def PathParts(path: str) -> List[str]:
    return os.path.normpath(path).split(os.sep)

def detect_long_functions_py(filepath: str, content: str, threshold: int = 50) -> List[Dict]:
    smells = []
    try:
        tree = ast.parse(content, filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # end_lineno is python 3.8+
                end_line = getattr(node, "end_lineno", node.lineno)
                line_count = end_line - node.lineno + 1
                if line_count > threshold:
                    smells.append({
                        "tool": "smell_detector",
                        "category": "maintainability",
                        "severity": "medium",
                        "filepath": filepath,
                        "line": node.lineno,
                        "message": f"Long Function: Function '{node.name}' is too long ({line_count} lines, threshold is {threshold}).",
                        "test_id": "long_function",
                    })
    except Exception:
        # Fallback if AST parsing fails (e.g. syntax error in repo code)
        pass
    return smells

def detect_long_functions_js(filepath: str, content: str, threshold: int = 50) -> List[Dict]:
    smells = []
    lines = content.splitlines()
    # Simple regex to find function starts in JS/TS
    # e.g., function foo() {, const foo = () => {, foo(bar) {
    func_pattern = re.compile(
        r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|(\w+)\s*\([^)]*\)\s*\{)'
    )
    
    i = 0
    while i < len(lines):
        line = lines[i]
        match = func_pattern.search(line)
        if match and "{" in line:
            func_name = match.group(1) or match.group(2) or match.group(3) or "anonymous"
            start_line = i + 1
            # Count braces to find matching close brace
            brace_count = 0
            found_end = False
            for j in range(i, len(lines)):
                brace_count += lines[j].count("{")
                brace_count -= lines[j].count("}")
                if brace_count <= 0:
                    end_line = j + 1
                    line_count = end_line - start_line + 1
                    if line_count > threshold:
                        smells.append({
                            "tool": "smell_detector",
                            "category": "maintainability",
                            "severity": "medium",
                            "filepath": filepath,
                            "line": start_line,
                            "message": f"Long Function: Function '{func_name}' is too long ({line_count} lines, threshold is {threshold}).",
                            "test_id": "long_function",
                        })
                    i = j  # Skip ahead
                    found_end = True
                    break
            if not found_end:
                i += 1
        else:
            i += 1
    return smells

def clean_and_normalize_lines(content: str) -> List[Tuple[int, str]]:
    cleaned = []
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        raw_line = line.strip()
        # Skip empty lines and comments
        if not raw_line:
            continue
        if raw_line.startswith("#") or raw_line.startswith("//") or raw_line.startswith("/*") or raw_line.startswith("*"):
            continue
        cleaned.append((idx + 1, raw_line))
    return cleaned

def detect_duplicate_code(files_content: Dict[str, str], min_lines: int = 6) -> List[Dict]:
    smells = []
    normalized_files = {}
    for filepath, content in files_content.items():
        normalized_files[filepath] = clean_and_normalize_lines(content)
        
    filepaths = list(normalized_files.keys())
    reported_pairs = set() # Avoid duplicate reports between the same ranges
    
    # Compare each file pair
    for idx_a in range(len(filepaths)):
        for idx_b in range(idx_a, len(filepaths)):
            file_a = filepaths[idx_a]
            file_b = filepaths[idx_b]
            lines_a = normalized_files[file_a]
            lines_b = normalized_files[file_b]
            
            len_a = len(lines_a)
            len_b = len(lines_b)
            
            i = 0
            while i < len_a:
                # Find matching starting line in file_b
                j = 0
                while j < len_b:
                    # Ignore exact same line in the same file (same indices)
                    if file_a == file_b and i == j:
                        j += 1
                        continue
                        
                    # Find consecutive matches
                    match_len = 0
                    while (i + match_len < len_a and 
                           j + match_len < len_b and 
                           lines_a[i + match_len][1] == lines_b[j + match_len][1]):
                        match_len += 1
                        
                    if match_len >= min_lines:
                        # We found a duplicate block!
                        orig_start_a = lines_a[i][0]
                        orig_end_a = lines_a[i + match_len - 1][0]
                        orig_start_b = lines_b[j][0]
                        orig_end_b = lines_b[j + match_len - 1][0]
                        
                        # Create unique key to prevent reporting both A->B and B->A or overlapping ranges
                        key = tuple(sorted([(file_a, orig_start_a, orig_end_a), (file_b, orig_start_b, orig_end_b)]))
                        
                        if key not in reported_pairs:
                            reported_pairs.add(key)
                            
                            # Determine message
                            if file_a == file_b:
                                msg = f"Duplicate Code: Block of {match_len} lines is duplicated in the same file (lines {orig_start_a}-{orig_end_a} and lines {orig_start_b}-{orig_end_b})."
                            else:
                                msg = f"Duplicate Code: Block of {match_len} lines is duplicated between {os.path.basename(file_a)} (lines {orig_start_a}-{orig_end_a}) and {os.path.basename(file_b)} (lines {orig_start_b}-{orig_end_b})."
                                
                            smells.append({
                                "tool": "smell_detector",
                                "category": "quality",
                                "severity": "low",
                                "filepath": file_a,
                                "line": orig_start_a,
                                "message": msg,
                                "test_id": "duplicate_code",
                                "duplicate_file": file_b,
                                "duplicate_start": orig_start_b,
                                "duplicate_end": orig_end_b,
                            })
                        i += match_len - 1 # advance pointer
                        break
                    j += 1
                i += 1
    return smells

def detect_code_smells(repo_path: str) -> List[Dict]:
    smells = []
    files_content = {}
    
    for root, dirs, files in os.walk(repo_path):
        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
                
            ext = os.path.splitext(file)[1].lower()
            if ext in {".py", ".js", ".ts", ".tsx", ".jsx"}:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    # Store relative filepath for frontend compatibility
                    rel_path = os.path.relpath(filepath, repo_path).replace("\\", "/")
                    files_content[rel_path] = content
                    
                    if ext == ".py":
                        smells.extend(detect_long_functions_py(rel_path, content))
                    elif ext in {".js", ".ts", ".tsx", ".jsx"}:
                        smells.extend(detect_long_functions_js(rel_path, content))
                except Exception:
                    pass
                    
    # Detect duplicate code smells
    duplicate_smells = detect_duplicate_code(files_content)
    smells.extend(duplicate_smells)
    
    return smells
