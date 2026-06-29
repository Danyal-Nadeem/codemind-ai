from .python_parser import parse_python_file
from .js_parser import parse_js_file


def parse_file(content: str, filepath: str, extension: str):
    if extension == ".py":
        return parse_python_file(content, filepath)
    elif extension in {".js", ".ts", ".tsx", ".jsx"}:
        return parse_js_file(content, filepath)
    return []
