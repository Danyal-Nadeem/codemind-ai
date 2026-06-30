import os
import sys
import subprocess
import json
import httpx
from typing import List, Dict
from openai import OpenAI

from .smell_detector import detect_code_smells
from .scorer import calculate_scores

def get_code_snippet(repo_path: str, filepath: str, line: int, context_lines: int = 1) -> str:
    abs_path = os.path.join(repo_path, filepath)
    if not os.path.exists(abs_path):
        return ""
    try:
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        start = max(0, line - 1 - context_lines)
        end = min(len(lines), line + context_lines + 1)
        return "".join(lines[start:end])
    except Exception:
        return ""

def explain_issue_llm(issue: Dict, code_snippet: str = "") -> str:
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    prompt = (
        f"You are a Senior Security & Code Quality Auditor. Explain the following issue in plain, "
        f"friendly English to a junior developer. Explain what the issue is, why it is dangerous/bad, "
        f"and how to fix it with an example.\n\n"
        f"Issue Details:\n"
        f"- Tool: {issue.get('tool')}\n"
        f"- Category: {issue.get('category')}\n"
        f"- Severity: {issue.get('severity')}\n"
        f"- Message: {issue.get('message')}\n"
        f"- File: {issue.get('filepath')}:{issue.get('line')}\n"
    )
    if code_snippet:
        prompt += f"- Code Snippet:\n```\n{code_snippet}\n```\n"

    # Try OpenAI
    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional security and code auditor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI explanation error: {e}")
            
    # Try Gemini
    elif gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "maxOutputTokens": 250,
                    "temperature": 0.3
                }
            }
            res = httpx.post(url, headers=headers, json=payload, timeout=8.0)
            if res.status_code == 200:
                data = res.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"Gemini explanation error: {e}")
            
    # Fallback to predefined template explanation
    test_id = issue.get("test_id", "")
    message = issue.get("message", "")
    
    if test_id == "duplicate_code":
        return (
            "This block of code is identical to code elsewhere in the project. "
            "Code duplication is a major maintainability issue: if a bug is found in this block, "
            "you have to fix it in multiple files. Additionally, it increases the cognitive load of developers. "
            "To fix this, refactor the duplicated logic into a reusable helper function or a utility module."
        )
    elif test_id == "long_function":
        return (
            "This function is longer than 50 lines. Large functions are difficult to read, reason about, "
            "and unit test. They often violate the Single Responsibility Principle by doing too many things. "
            "To fix this, break the function down into smaller, self-contained helper functions with descriptive names."
        )
    elif "eval" in test_id or "eval" in message.lower() or "exec" in message.lower():
        return (
            "Using eval() or exec() dynamically compiles and executes code from a string. If any user input "
            "or untrusted source is passed to it, an attacker can execute arbitrary system commands (Remote Code Execution). "
            "To fix this, avoid eval() completely. Use safe parsing alternatives (like json.loads or ast.literal_eval) "
            "or implement explicit lookup tables (dictionaries)."
        )
    elif "api-key" in test_id or "secret" in message.lower() or "password" in message.lower() or "token" in message.lower():
        return (
            "A potential password, API key, or authorization token was found written directly as a hardcoded string. "
            "Hardcoded secrets can easily be leaked to public repositories, logs, or third parties. "
            "To fix this, extract the secret and load it from environment variables or a configuration manager (e.g. .env)."
        )
    elif "B101" in test_id:
        return (
            "An assert statement was detected. Python removes assertions when compiled with optimization flag '-O' (e.g. production). "
            "If this assertion is performing a safety or validation check, compiling it will bypass the verification. "
            "To fix this, use standard 'if' conditions and raise appropriate exceptions (like ValueError) instead."
        )
    elif "B608" in test_id or "sql" in message.lower():
        return (
            "Possible SQL injection vulnerability. Direct string formatting or concatenation is used to build a database query. "
            "Attackers can manipulate the query structure by sending malicious inputs. "
            "To fix this, always use parameterized queries or an ORM (like SQLAlchemy) that handles database escaping."
        )
        
    return (
        f"Potential issue detected: {message}. Review the source code and ensure it aligns with standard security "
        f"and code style guidelines. If it involves user inputs, validate and sanitize them properly."
    )

def get_executable_path(name: str) -> str:
    venv_dir = os.path.dirname(sys.executable)
    for ext in ["", ".exe", ".cmd", ".bat"]:
        path = os.path.join(venv_dir, name + ext)
        if os.path.exists(path):
            return path
    return name

def run_bandit(repo_path: str) -> List[Dict]:
    try:
        bandit_path = get_executable_path("bandit")
        result = subprocess.run(
            [bandit_path, "-r", repo_path, "-f", "json", "-q"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        issues = []
        for issue in data.get("results", []):
            rel_path = issue["filename"].replace(repo_path, "").replace("\\", "/").lstrip("/")
            issues.append({
                "tool": "bandit",
                "category": "security",
                "severity": issue["issue_severity"].lower(),
                "confidence": issue["issue_confidence"].lower(),
                "message": issue["issue_text"],
                "filepath": rel_path,
                "line": issue["line_number"],
                "test_id": issue["test_id"],
            })
        return issues
    except Exception as e:
        print(f"Bandit scan error: {e}")
        return []

def run_semgrep(repo_path: str) -> List[Dict]:
    rules_dir = os.path.join(os.path.dirname(__file__), "rules")
    rules_path = os.path.join(rules_dir, "custom_rules.yaml")
    if not os.path.exists(rules_path):
        return []
    try:
        # Run semgrep CLI on the repo path
        semgrep_path = get_executable_path("semgrep")
        result = subprocess.run(
            [semgrep_path, "--config", rules_path, repo_path, "--json", "--quiet"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        issues = []
        for issue in data.get("results", []):
            rel_path = issue["path"].replace(repo_path, "").replace("\\", "/").lstrip("/")
            issues.append({
                "tool": "semgrep",
                "category": "security",
                "severity": issue["extra"]["severity"].lower(),
                "confidence": "high",
                "message": issue["extra"]["message"],
                "filepath": rel_path,
                "line": issue["start"]["line"],
                "test_id": issue["check_id"],
            })
        return issues
    except Exception as e:
        print(f"Semgrep scan error or not installed: {e}")
        return []

def scan_repo_full(repo_path: str) -> Dict:
    # 1. Run all scanners
    bandit_issues = run_bandit(repo_path)
    semgrep_issues = run_semgrep(repo_path)
    code_smells = detect_code_smells(repo_path)

    all_issues = []
    
    # 2. Add Bandit issues
    for issue in bandit_issues:
        code = get_code_snippet(repo_path, issue["filepath"], issue["line"])
        issue["code"] = code
        issue["explanation"] = explain_issue_llm(issue, code)
        all_issues.append(issue)

    # 3. Add Semgrep issues
    for issue in semgrep_issues:
        code = get_code_snippet(repo_path, issue["filepath"], issue["line"])
        issue["code"] = code
        issue["explanation"] = explain_issue_llm(issue, code)
        all_issues.append(issue)

    # 4. Add Code Smells
    for issue in code_smells:
        code = get_code_snippet(repo_path, issue["filepath"], issue["line"])
        issue["code"] = code
        issue["explanation"] = explain_issue_llm(issue, code)
        all_issues.append(issue)

    # 5. Compute scores
    scores = calculate_scores(all_issues)

    # Compile result
    result = {
        "status": "success",
        "scores": scores,
        "total_issues": len(all_issues),
        "issues": all_issues,
    }
    return result
