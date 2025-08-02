import ast
import os
import logging
from typing import Set, List, Optional

from src.summary_error import SummarizationError

logging.basicConfig(
    level=logging.INFO,
    format="[{levelname}] {message}",
    style="{"
)
logger = logging.getLogger(__name__)


def extract_local_imports(file_path: str, project_root: str) -> Set[str]:
    """Extracts local module imports from a Python file."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])

    local_modules = set()
    for imp in imports:
        local_path = os.path.join(project_root, f"{imp}.py")
        if os.path.exists(local_path):
            local_modules.add(imp)

    return local_modules


def collect_all_dependencies(entry_path: str, project_root: str) -> Set[str]:
    """Recursively collects paths to all local .py files used by the entry file."""
    visited = set()
    to_visit = [entry_path]

    while to_visit:
        current_path = to_visit.pop()
        if current_path in visited:
            continue
        visited.add(current_path)

        logger.debug(f"Analyzing imports in: {current_path}")
        local_imports = extract_local_imports(current_path, project_root)
        for mod in local_imports:
            mod_path = os.path.join(project_root, f"{mod}.py")
            if os.path.exists(mod_path) and mod_path not in visited:
                logger.debug(f"Discovered dependency: {mod_path}")
                to_visit.append(mod_path)

    return visited


def read_file_code(path: str) -> str:
    """Reads the contents of a Python file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_context_from_main(main_path: str) -> str:
    """
    Builds a combined code context from main.py and all recursively imported local modules.
    Returns a string to send to the LLM.
    """
    project_root = os.path.dirname(main_path)
    logger.info(f"Building context from: {main_path}")
    all_paths = collect_all_dependencies(main_path, project_root)

    combined_blocks = []
    for path in sorted(all_paths):
        if os.path.exists(path):
            label = os.path.relpath(path, project_root)
            logger.info(f"Including module: {label}")
            code = read_file_code(path)
            combined_blocks.append(f"# === {label} ===\n{code}")

    return "\n\n".join(combined_blocks)


def find_all_main_files(root_dir: str) -> List[str]:
    """Recursively find all main.py files under the given directory."""
    matches = []
    for dirpath, _, filenames in os.walk(root_dir):
        if "main.py" in filenames:
            matches.append(os.path.join(dirpath, "main.py"))
    logger.info(f"Found {len(matches)} main.py file(s) under {root_dir}")
    return matches


def prompt_user_to_choose(files: List[str]) -> Optional[str]:
    """Prompt user to select one of the found files."""
    if not files:
        return None
    if len(files) == 1:
        logger.info(f"Only one main.py file found: {files[0]}")
        return files[0]

    print("Multiple 'main.py' files found:")
    for idx, path in enumerate(files):
        print(f"[{idx + 1}] {path}")
    while True:
        try:
            choice = int(input("Select the number of the file to summarize: ").strip())
            if 1 <= choice <= len(files):
                logger.info(f"User selected main.py: {files[choice - 1]}")
                return files[choice - 1]
        except ValueError:
            pass
        print("Invalid choice. Please enter a number from the list.")


def read_main_file(path: str) -> str:
    """Reads the contents of the main Python file."""
    if not os.path.exists(path):
        raise SummarizationError(f"main.py not found at: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise SummarizationError(f"Failed to read file: {e}")