import ast
import os
import logging
from typing import List, Dict, Optional, Any

# Set up logging configuration for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def extract_definitions_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Parses a single Python file and extracts classes, functions, and docstrings.
    Returns a dictionary or None if the file can't be parsed.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source: str = f.read()

    try:
        tree: ast.Module = ast.parse(source)
    except SyntaxError as e:
        logging.warning(f"Syntax error in {file_path}: {e}")
        return None

    parsed: Dict[str, Any] = {
        "file": file_path,
        "classes": [],
        "functions": []
    }

    # Only track top-level FunctionDefs (not class methods)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            parsed["functions"].append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "docstring": ast.get_docstring(node)
            })

        elif isinstance(node, ast.ClassDef):
            methods: List[Dict[str, Any]] = [
                {
                    "name": n.name,
                    "args": [arg.arg for arg in n.args.args],
                    "docstring": ast.get_docstring(n)
                }
                for n in node.body if isinstance(n, ast.FunctionDef)
            ]
            parsed["classes"].append({
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "methods": methods
            })

    return parsed


def parse_directory(root_dir: str) -> List[Dict[str, Any]]:
    """
    Walks a directory and parses all .py files using extract_definitions_from_file.
    Returns a list of parsed file structures.
    """
    if not os.path.exists(root_dir):
        logging.error(f"Directory not found: {root_dir}")
        return []

    parsed_results: List[Dict[str, Any]] = []

    logging.info(f"Scanning directory: {root_dir}")

    found_files: bool = False
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py"):
                found_files = True
                file_path = os.path.join(dirpath, filename)
                logging.info(f"Processing file: {file_path}")
                try:
                    parsed = extract_definitions_from_file(file_path)
                    if parsed:
                        parsed_results.append(parsed)
                except Exception as e:
                    logging.error(f"Failed to parse {file_path}: {e}")

    if not found_files:
        logging.warning(f"No Python files found in: {root_dir}")

    return parsed_results