"""
Language-agnostic file helpers used by the Modal endpoints.

Why this module exists:
- Keep endpoint files small and readable by pushing I/O details into helpers.
- Make the logic *language neutral* so we don't hard-code "main.py" or Python-only assumptions.
- Provide tiny, predictable building blocks that are easy to test and reuse.

Responsibilities (simple verbs):
  1) clone_repo(repo_url, ref, dest)
       -> shallow-clone a Git repo (supports private GitHub if GITHUB_TOKEN is present in env)

  2) download_and_extract_zip(zip_url, extract_root)
       -> download a .zip file by HTTPS URL and extract it to a folder

  3) extract_zip_file(zip_path, extract_root)
       -> extract a *local* .zip file into a folder (used for direct multipart uploads)

  4) write_snippet_temp(parent, code)
       -> write a pasted code snippet to parent/snippet/snippet.txt so it can be indexed like any other source

  5) index_files(root, include_globs, exclude_globs, max_files, max_bytes)
       -> walk root, filter by globs, apply caps, and return [{ path, size, preview } ...]

  6) read_selected_bundle(root, selected_paths)
       -> read specific files and concatenate them into one big text block with per-file headers
"""

import os  # Working with paths and environment variables.
import fnmatch  # Glob-like filename matching (include/exclude patterns).
import zipfile  # Reading and extracting .zip archives.
import subprocess  # Running external commands, e.g., `git`.
from typing import List  # Type hints for clarity.
import urllib.request  # Simple HTTPS downloads without extra deps.
import shutil  # Streaming copy to file; file operations.

# -----------------------------------------------------------------------------
# 1) Clone a Git repository (supports private repos on GitHub if GITHUB_TOKEN set)
# -----------------------------------------------------------------------------


def clone_repo(repo_url: str, ref: str, dest: str) -> None:
    """
    Shallow-clone a repo at a specific ref into a destination folder.

    This uses `git clone --depth 1 --branch <ref> <url> <dest>` which:
      - Avoids full history (much faster, less bandwidth).
      - Checks out only the specified branch/tag/commit.

    Private GitHub:
      If the environment variable GITHUB_TOKEN is set and the URL host is github.com,
      we inject the token into the HTTPS URL so `git clone` can authenticate transparently.

    Args:
      repo_url : HTTPS URL to the repository (e.g., "https://github.com/owner/repo").
      ref      : Branch, tag, or commit SHA to check out (e.g., "main").
      dest     : Destination directory path for the clone (created if missing).

    Raises:
      subprocess.CalledProcessError if `git clone` fails (bad URL, bad ref, no auth, etc.).
    """
    token = os.getenv("GITHUB_TOKEN")  # Read token if provided by your runtime.
    url = repo_url  # Start with the plain URL.
    if token and repo_url.startswith("https://github.com/"):
        # Insert the token in the URL so `git` can do HTTPS Basic auth.
        # NOTE: We purposely do not log this URL anywhere to avoid leaking the token.
        url = repo_url.replace("https://", f"https://{token}:x-oauth-basic@")

    cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        ref,
        url,
        dest,
    ]  # Shallow clone command.
    subprocess.run(cmd, check=True)  # Raises if clone fails.


# -----------------------------------------------------------------------------
# 2) Download a .zip by URL and extract it
# -----------------------------------------------------------------------------


def download_and_extract_zip(zip_url: str, extract_root: str) -> str:
    """
    Download a .zip from `zip_url` over HTTPS and extract it into `extract_root`.

    This is used by the JSON path of /prepare when callers send {"input_type":"zipped_folder","zip_url": "..."}.
    For direct local uploads (multipart/form-data), see `extract_zip_file`.

    Args:
      zip_url      : Direct HTTPS URL to a .zip (must be publicly accessible without auth).
      extract_root : Directory that will hold the downloaded .zip AND its extracted contents.

    Returns:
      The same `extract_root` directory path.

    Raises:
      URLError         : If the URL cannot be reached.
      zipfile.BadZipFile : If the downloaded file is not a valid zip.
      OSError          : On I/O errors writing to disk.
    """
    os.makedirs(extract_root, exist_ok=True)  # Ensure target exists.
    zip_path = os.path.join(extract_root, "archive.zip")  # Temporary local file path.

    # Stream the download straight to disk to avoid loading into memory.
    with urllib.request.urlopen(zip_url) as resp, open(zip_path, "wb") as out:
        shutil.copyfileobj(resp, out)

    # Extract the downloaded archive in-place.
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_root)

    return extract_root


# -----------------------------------------------------------------------------
# 3) Extract a *local* .zip (used when the user uploads a file directly)
# -----------------------------------------------------------------------------


def extract_zip_file(zip_path: str, extract_root: str) -> str:
    """
    Extract a local .zip (already on disk) into `extract_root` and return that path.

    This is the counterpart to `download_and_extract_zip`, used by the multipart
    upload flow where the user provides a .zip file directly from their device.

    Args:
      zip_path     : Absolute path to the local .zip file.
      extract_root : Directory to extract into.

    Returns:
      The same `extract_root` directory path.

    Raises:
      zipfile.BadZipFile : If the file is not a valid zip archive.
      OSError            : On I/O errors.
    """
    os.makedirs(extract_root, exist_ok=True)  # Ensure destination exists.
    with zipfile.ZipFile(zip_path) as zf:  # Open archive.
        zf.extractall(extract_root)  # Extract all members.
    return extract_root


# -----------------------------------------------------------------------------
# 4) Write a pasted code snippet into a file we can index
# -----------------------------------------------------------------------------


def write_snippet_temp(parent: str, code: str) -> str:
    """
    Write raw text to parent/snippet/snippet.txt and return that folder.

    We use this for {"input_type":"pasted_code"} requests so the snippet can go
    through the same filter/index/summarize flow as any other source.

    Args:
      parent : Folder under which we will create "snippet/".
      code   : The text to write.

    Returns:
      The path to the created "snippet" folder.
    """
    root = os.path.join(parent, "snippet")
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "snippet.txt"), "w", encoding="utf8") as f:
        f.write(code)
    return root


# -----------------------------------------------------------------------------
# 5) Walk a folder, filter, cap sizes, and return a compact file list
# -----------------------------------------------------------------------------


def index_files(
    root: str,
    include_globs: List[str],
    exclude_globs: List[str],
    max_files: int,
    max_bytes: int,
) -> list[dict]:
    """
    Traverse `root` recursively and select files that match `include_globs` but
    not `exclude_globs`, without exceeding `max_files` or `max_bytes`.

    For each selected file we return:
      { "path": "<path relative to root>", "size": <bytes>, "preview": "<first ~200 chars if readable>" }

    Why we return a tiny preview:
      - Helps the frontend show a quick "is this the right file?" look.
      - Avoids sending large file contents back to the client.

    Args:
      root          : Root folder to walk.
      include_globs : Allow-list of glob patterns (ORed). If empty/None, treat as "allow all".
      exclude_globs : Block-list of glob patterns (ORed). If a file matches any, it is skipped.
      max_files     : Safety cap on number of files in the output list.
      max_bytes     : Safety cap on the *sum* of sizes across output files.

    Returns:
      A list of dicts with keys path/size/preview, sorted by path for stability.
    """
    candidates: list[tuple[str, int]] = []

    # Walk the tree under root and build a candidate list that passes the glob filters.
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            abs_path = os.path.join(dirpath, name)  # Full path on disk.
            rel_path = os.path.relpath(
                abs_path, root
            )  # Convert to path relative to `root` (for the API/UI).

            # Skip excluded files quickly.
            if any(fnmatch.fnmatch(rel_path, pat) for pat in exclude_globs):
                continue

            # If include_globs is provided, keep the file only if it matches at least one include pattern.
            if include_globs and not any(
                fnmatch.fnmatch(rel_path, pat) for pat in include_globs
            ):
                continue

            # We need the file's size both for the response and for enforcing the total size cap.
            try:
                size = os.path.getsize(abs_path)
            except OSError:
                # If size is unreadable (rare), skip this file.
                continue

            candidates.append((rel_path, size))

    # Sort for deterministic order so the front end sees a stable list.
    candidates.sort()

    out: list[dict] = []
    total = 0

    # Build the output list while enforcing caps.
    for rel_path, size in candidates:
        if len(out) >= max_files:
            break  # Stop if we reached the count cap.
        if total + size > max_bytes:
            break  # Stop if adding this file would cross the size cap.

        # Attempt a tiny text preview; if it is binary or unreadable, preview remains empty.
        preview = ""
        try:
            with open(
                os.path.join(root, rel_path), "r", encoding="utf8", errors="ignore"
            ) as f:
                preview = f.read(
                    200
                )  # Small peek so the UI can render something helpful.
        except Exception:
            preview = ""

        out.append({"path": rel_path, "size": size, "preview": preview})
        total += size

    return out


# -----------------------------------------------------------------------------
# 6) Concatenate selected files into one big text block
# -----------------------------------------------------------------------------


def read_selected_bundle(root: str, selected_paths: list[str]) -> str:
    """
    Read a specific set of files and join them into one large string.

    For clarity (and to help the model), we prefix each file with a header line:
      # === <relative/path> ===
      <content>

    Notes:
    - We open files in text mode with "errors='ignore'" so non-UTF8 bytes won't crash the read.
    - The calling code controls which files are chosen; this helper simply reads them.

    Args:
      root           : Root directory containing the files (the value we saved in manifest.json).
      selected_paths : Relative paths to include, as returned from `index_files`.

    Returns:
      One large string containing all requested file contents back-to-back.

    Raises:
      FileNotFoundError if any selected path does not exist (caller will surface a 400/500).
    """
    parts: list[str] = []
    for rel in selected_paths:
        fp = os.path.join(root, rel)
        if not os.path.isfile(fp):
            # This is a "fail fast" to avoid silently skipping user-selected files.
            raise FileNotFoundError(f"Missing file {rel}")
        with open(fp, "r", encoding="utf8", errors="ignore") as f:
            parts.append(f"# === {rel} ===\n{f.read()}\n")
    return "\n".join(parts)
