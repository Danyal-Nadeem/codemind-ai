import re
from typing import List, Dict


def parse_js_file(content: str, filepath: str) -> List[Dict]:
    chunks = []
    lines = content.split("\n")

    # function declarations
    func_pattern = re.compile(
        r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
        re.MULTILINE
    )

    # arrow functions assigned to const
    arrow_pattern = re.compile(
        r"^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(",
        re.MULTILINE
    )

    # class declarations
    class_pattern = re.compile(
        r"^(?:export\s+)?class\s+(\w+)",
        re.MULTILINE
    )

    for pattern, chunk_type in [
        (func_pattern, "function"),
        (arrow_pattern, "arrow_function"),
        (class_pattern, "class"),
    ]:
        for match in pattern.finditer(content):
            name = match.group(1)
            start_line = content[:match.start()].count("\n") + 1
            end_line = min(start_line + 30, len(lines))
            code = "\n".join(lines[start_line - 1:end_line])

            chunks.append({
                "type": chunk_type,
                "name": name,
                "filepath": filepath,
                "start_line": start_line,
                "end_line": end_line,
                "code": code,
            })

    return chunks
