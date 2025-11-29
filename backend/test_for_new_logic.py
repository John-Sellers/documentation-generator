"""
Pure Modal web endpoints.

This module exposes two HTTPS endpoints, both created via @modal.fastapi_endpoint:

1) POST /prepare
   - Accepts EITHER:
       a) JSON (application/json) describing the source (Git repo, zip URL, pasted text), OR
       b) multipart/form-data with a *local .zip upload* from the user's device.
   - It "materializes" the source into a *per-request working folder* inside a Modal Volume
     mounted at /data. (Each request gets a unique folder key called "source_id".)
   - It then walks the chosen root folder, applies include/exclude glob filters and size caps,
     and returns a *file index* with tiny previews so the UI can let the user pick exactly
     which files to summarize (language-agnostic).
   - Returns JSON: { "source_id": "<short id>", "files": [ { "path": "...", "size": 123, "preview": "..." }, ... ] }
   - **Important:** At the end of /prepare we call `volume.commit()` so that subsequent functions
     (such as /summarize) see the written files and the saved manifest.

2) POST /summarize
   - Accepts JSON:
       {
         "source_id": "<id from /prepare>",
         "selected_paths": ["relative/path/1", "relative/path/2", ...],
         "sections": [ ... SectionSpec objects ... ],
         "constraints": { "audience": "...", "tone": "...", "reading_level": "...", "max_tokens": 1800 },
         "cleanup": true
       }
   - It first calls `volume.reload()` to make sure we see the latest committed state from /prepare.
   - It loads /data/<source_id>/manifest.json to learn the *actual root folder* to read from.
   - It concatenates the selected files into one text bundle, then calls Groq (OpenAI-compatible API)
     asking for **strict JSON** whose keys *exactly* match the requested section "id"s.
   - Returns JSON: { "source_id": "...", "sections": { "<id>": <value>, ... }, "meta": { "warnings": [], "truncated": false } }
   - If "cleanup": true, it deletes the working folder and then calls `volume.commit()` again so the deletion is visible.

Authentication:
- Both endpoints require the HTTP header:  Authorization: Bearer <SECRET_TOKEN>
- SECRET_TOKEN is provided to the container by a Modal Secret named "secret-token".

Other Secrets:
- "groq-api-key" provides GROQ_API_KEY used to call Groq's API.
- (Optional) If you want private GitHub clones, create a secret holding GITHUB_TOKEN
  (e.g., named "github-token") and make sure clone_repo() can see it via env.
  NOTE: This file does not explicitly declare that secret; clone_repo reads os.getenv("GITHUB_TOKEN").
        For private repos, ensure  Modal function has that env set (via Secret or env injection).

Deployment:
  modal deploy backend/summarizer_modal.py
"""

# ------------------------------
# Standard library dependencies
# ------------------------------
import os  # Read environment variables and build file paths.
import json  # Parse and produce JSON text.
import uuid  # Generate short unique ids for per-request folders.
import shutil  # Remove directories during cleanup.
from typing import Any  # Type hints for unstructured dicts used in requests.
import requests  # Make HTTPS requests to Groq.
import time  # Sleep for retry backoff.
import logging  # Emit structured logs that help debugging.
import re  # Rescue JSON if the model accidentally wraps it with extra text.

# ------------------------------
# Third-party and Modal imports
# ------------------------------
import modal  # Modal SDK: images, functions, secrets, volumes, etc.
from fastapi import (
    HTTPException,
    Request,
    UploadFile,
)  # FastAPI request types + HTTP error.
from pydantic import BaseModel, Field  # Request body validation with helpful 400s.

# ------------------------------
# Logging configuration
# ------------------------------
# We pick a simple log format and INFO level so useful events show up in Modal logs.
logging.basicConfig(level=logging.INFO, format="[{levelname}] {message}", style="{")
logger = logging.getLogger(__name__)

# ------------------------------
# Helper functions for file work
# ------------------------------
# NOTE: We import from  sibling module `source_utils.py` which holds small, testable helpers.
#       Those helpers are language-agnostic and do not assume a Python-only project.
from source_utils import (
    clone_repo,  # Shallow clone a Git repo; uses GITHUB_TOKEN if present.
    download_and_extract_zip,  # Download a .zip by URL and extract it.
    extract_zip_file,  # Extract a local .zip (used for direct multipart uploads).
    write_snippet_temp,  # Save pasted code into a folder.
    index_files,  # Build a filtered file list with tiny previews.
    read_selected_bundle,  # Concatenate chosen files into one large text string.
)

# ------------------------------
# Container image definition
# ------------------------------
# This image is what Modal will build and run  functions inside.
# We:
#  - Install pinned requirements (requests, fastapi, etc.)
#  - Install FastAPI's ASGI server shim used by Modal's web endpoints
#  - apt-get install `git` so we can clone repositories
#  - set PYTHONPATH so `import source_utils` etc. works
#  - copy current repository tree into /root/app (inside the container)
image = (
    modal.Image.debian_slim()
    .pip_install_from_requirements("requirements.txt")  # Install deps pinned in  file.
    .pip_install(
        "fastapi[standard]"
    )  # Install server + uvicorn used under the hood by Modal.
    .apt_install("git")  # Needed for `git clone` in clone_repo().
    .env(
        {
            "PYTHONPATH": "/root/app",  # Make `/root/app` importable as module roots.
        }
    )
    .add_local_dir(
        ".", remote_path="/root/app"
    )  # Ship  repo contents into the container working dir.
)

# ------------------------------
# Modal Secrets
# ------------------------------
# These are "named secrets" in Modal's dashboard. At runtime, Modal injects them into env vars.
groq_secret = modal.Secret.from_name(
    "groq-api-key"
)  # Provides GROQ_API_KEY env var for Groq API calls.
auth_secret = modal.Secret.from_name(
    "secret-token"
)  # Provides SECRET_TOKEN env var for endpoint auth.

# ------------------------------
# Groq key from environment
# ------------------------------
# We look up GROQ_API_KEY on import. If it's missing, _call_llm_sections() will raise a clean 500.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ------------------------------
# Shared storage: Modal Volume
# ------------------------------
# A Modal Volume is a versioned, persistent shared filesystem mount. Each function call
# can read/write at /data. To make writes visible across functions, we must call `volume.commit()`.
# To see the latest committed state in a new function, call `volume.reload()`.
volume = modal.Volume.from_name("docgen-sources", create_if_missing=True)

# ------------------------------
# Modal App (groups functions)
# ------------------------------
app = modal.App("documentation_generator", image=image)

# ------------------------------
# Pydantic request models
# ------------------------------


class PrepareBody(BaseModel):
    """
    Request model for JSON mode of /prepare.

    If the incoming Content-Type is application/json, we parse the body into this model.
    For multipart/form-data uploads (direct .zip), we do NOT use this model; we read the form fields.

    Fields:
      input_type      : REQUIRED. One of:
        - "github_repo"            : clone a whole repo
        - "github_repo_directory"  : clone a repo and use subdir as root
        - "zipped_folder"          : download a .zip by HTTPS URL and extract it
        - "pasted_code"            : write raw text to snippet/snippet.txt
      repo_url        : For github_* types, the HTTPS URL to the repository.
      repo_ref        : Branch/tag/commit to check out. Defaults to "main".
      subdir          : For github_repo_directory, the path inside the repo to treat as root.
      zip_url         : For zipped_folder (JSON mode only), an HTTPS URL to a .zip file.
      code_snippet    : For pasted_code, the raw text to save.

      include_globs   : Optional allow-list of file patterns (ORed). If omitted, we default to common code/text.
      exclude_globs   : Optional block-list of file patterns (ORed). We default to ignoring .git, node_modules, etc.
      max_files       : Optional safety cap on number of files returned by the index.
      max_total_bytes : Optional safety cap on sum of sizes across returned files.
    """

    input_type: str = Field(
        ...,
        description="github_repo | github_repo_directory | zipped_folder | pasted_code",
    )
    # GitHub-related inputs
    repo_url: str | None = None
    repo_ref: str | None = "main"
    subdir: str | None = None
    # Zip-by-URL input
    zip_url: str | None = None
    # Pasted code input
    code_snippet: str | None = None
    # Filters and caps
    include_globs: list[str] | None = None
    exclude_globs: list[str] | None = None
    max_files: int | None = 500
    max_total_bytes: int | None = 20_000_000


class SectionSpec(BaseModel):
    """
    Describes ONE output field that you want the model to produce.

    The `id` becomes the key in the response JSON under "sections".
    The `type` tells the model and  UI how to shape/display that value.

    Fields:
      id          : REQUIRED. Unique key you want back. Example: "title", "overview", "key_points".
      label       : Optional human-friendly label for UI display. Does not change the JSON key.
      type        : One of:
                      - "short_text" -> brief string; we can enforce max_chars.
                      - "markdown"   -> longer text; markdown formatting allowed.
                      - "list"       -> an array of items (strings/URLs/etc.).
      required    : Optional hint to emphasize that this section must be present. We still return the key
                    even if the model could not fill it (empty string or empty list).
      max_chars   : For "short_text" only; we truncate the returned string to this many characters.
      item_type   : For "list" only; hints the item kind (e.g., "string" or "url") for better generation and UI.
      prompt_hint : Optional extra instruction for JUST this section. E.g., "Return 3-5 bullets."
    """

    id: str
    label: str | None = None
    type: str = "markdown"
    required: bool | None = None
    max_chars: int | None = None
    item_type: str | None = None
    prompt_hint: str | None = None


class SummarizeBody(BaseModel):
    """
    Request model for /summarize.

    Fields:
      source_id      : REQUIRED. The short id returned by /prepare; points us to /data/<source_id>.
      selected_paths : REQUIRED. Relative file paths (as returned by /prepare) that you want summarized.
      sections       : REQUIRED. A list of SectionSpec items that define the *shape of the output JSON*.
      constraints    : Optional dict of style hints; supported keys:
                         - "audience": "business" | "technical" | "general" | ...
                         - "tone": "non_technical" | "neutral" | "formal" | "concise" | ...
                         - "reading_level": "grade_7" | "grade_9" | ...
                         - "max_tokens": integer limit for the model's completion tokens
      cleanup        : Optional boolean (default True). If True, we delete /data/<source_id> after summarizing.
    """

    source_id: str
    selected_paths: list[str]
    sections: list[SectionSpec]
    constraints: dict[str, Any] | None = None
    cleanup: bool | None = True


# ------------------------------
# Authentication helper
# ------------------------------


def _require_token_or_401(request: Request) -> None:
    """
    Enforce a simple bearer token scheme.

    - Reads SECRET_TOKEN from the environment (provided via Modal Secret "secret-token").
    - Reads the HTTP header "Authorization" and strips "Bearer " prefix.
    - If the supplied token does not match SECRET_TOKEN, raise 401.

    This runs at the top of both /prepare and /summarize to protect  endpoints.
    """
    expected = os.getenv("SECRET_TOKEN", "")
    supplied = request.headers.get("authorization", "").replace("Bearer ", "")
    if not expected or supplied != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing token")


# ------------------------------
# JSON parsing helper (robust)
# ------------------------------


def _safe_parse_json(text: str) -> dict:
    """
    Parse a JSON object from a string and be forgiving if the model wraps it with prose.

    In theory, we ask the model for `response_format={"type":"json_object"}` so it *should* return pure JSON.
    In practice, some models still add stray text. We try `json.loads` first and, if that fails,
    we search for the first curly-brace block and parse that.

    Returns:
      dict (possibly empty if we cannot recover).
    """
    try:
        return json.loads(text)  # Happy path: exact JSON.
    except Exception:
        pass
    try:
        # Regex searches for the first top-level {...} block (recursive pattern).
        match = re.search(r"\{(?:[^{}]|(?R))*\}", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    return {}


# ------------------------------
# Groq call that returns *strict* JSON sections
# ------------------------------


def _call_llm_sections(
    code_bundle: str, sections: list[SectionSpec], constraints: dict | None
) -> dict:
    """
    Ask Groq (OpenAI-compatible API) to produce JSON with keys EXACTLY equal to the requested section ids.

    Steps:
      1) Build a minimal "schema" summary from the given SectionSpec list. This gives the model
         enough structure (ids, types, max_chars, hints) to return predictable JSON.
      2) Build a system message for voice ("audience", "tone", "reading_level").
      3) Build a user message that:
           - instructs the model to produce one JSON object ONLY,
           - includes the schema summary,
           - includes the concatenated file contents.
      4) Try a small list of models in order (with a few network retries).
      5) Parse the response with _safe_parse_json; drop any extra keys; ensure all requested keys exist.

    Raises:
      HTTPException(500) if GROQ_API_KEY is missing.
      HTTPException(502) if all model attempts fail.
    """
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Missing GROQ_API_KEY secret")

    # Build a compact schema that the model can read (and logs can show for debugging).
    schema = [
        {
            "id": s.id,
            "type": s.type,
            "label": s.label or s.id,
            "required": bool(s.required) if s.required is not None else False,
            "max_chars": s.max_chars,
            "item_type": s.item_type,
            "prompt_hint": s.prompt_hint,
        }
        for s in sections
    ]

    # Pull style constraints with defaults so requests can be minimal.
    constraints = constraints or {}
    audience = constraints.get("audience", "general")
    tone = constraints.get("tone", "neutral")
    reading_level = constraints.get("reading_level", "grade_8")
    max_tokens = int(
        constraints.get("max_tokens", 2000)
    )  # server-side cap to avoid runaway cost.

    # System message: sets voice and audience.
    system_msg = (
        f"You are a documentation helper. Write for {audience} readers. "
        f"Use a {tone} tone. Target reading level {reading_level}."
    )

    # User message: strictly instructs that we want *one* JSON object and nothing else.
    # We include the schema for structure and the entire code bundle as context.
    user_msg = (
        "Return one JSON object with keys exactly matching the given section ids. "
        "Do not add extra keys. For list sections return an array. "
        "For short_text return a short string. For markdown return markdown. "
        "If a section is not applicable, return an empty string or empty list.\n\n"
        f"Sections spec:\n{json.dumps(schema, ensure_ascii=False)}\n\n"
        "===== BEGIN CONTENT =====\n"
        f"{code_bundle}\n"
        "===== END CONTENT ====="
    )

    # Groq endpoint is OpenAI-compatible.
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    # We try a few models in order. You can change this list to taste or make it env-driven.
    models_to_try = [
        "llama3-70b-8192",  # strong default
        "llama3-8b-8192",  # smaller fallback
        "gemma-7b-it",  # another fallback
    ]

    # Try each model with up to 3 network attempts.
    for model_name in models_to_try:
        logger.info(f"Trying model {model_name}")
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            "response_format": {"type": "json_object"},  # Ask the API to enforce JSON.
            "temperature": 0.3,  # Slight randomness but still focused.
            "max_tokens": max_tokens,  # Let caller tune upper bound if needed.
        }

        for attempt in range(1, 4):
            logger.info(f"[{model_name}] attempt {attempt} of 3")
            try:
                resp = requests.post(
                    endpoint, headers=headers, json=payload, timeout=45
                )
                if resp.status_code != 200:
                    # API-level error (auth, quota, or other). Try the next model.
                    logger.warning(
                        f"[{model_name}] Groq error {resp.status_code}: {resp.text}"
                    )
                    break

                data = resp.json()
                raw = data["choices"][0]["message"]["content"] or "{}"

                # Log token usage when present (handy for budget visibility).
                usage = data.get("usage", {})
                logger.info(
                    f"[{model_name}] tokens prompt={usage.get('prompt_tokens','?')} "
                    f"completion={usage.get('completion_tokens','?')} total={usage.get('total_tokens','?')}"
                )

                # Parse the content into a dict, then filter & fill so output shape is stable.
                parsed = _safe_parse_json(raw)
                requested = {s.id for s in sections}
                clean = {k: v for k, v in parsed.items() if k in requested}

                # Ensure every requested key exists; enforce short_text limits.
                for s in sections:
                    if s.id not in clean:
                        clean[s.id] = [] if s.type == "list" else ""
                    if (
                        s.type == "short_text"
                        and s.max_chars
                        and isinstance(clean[s.id], str)
                    ):
                        clean[s.id] = clean[s.id][: s.max_chars]

                logger.info(f"[{model_name}] success!")
                logger.info(f"[{model_name}] output: {clean}")

                return clean  # Success — return the shaped JSON to caller.

            except requests.RequestException as e:
                # Network/transient error; retry a couple times then move to next model.
                logger.warning(f"[{model_name}] network error: {e}")
                if attempt == 3:
                    logger.error(f"[{model_name}] all attempts failed")
                time.sleep(2 * attempt)  # simple linear-ish backoff
            except Exception as e:
                # Unexpected response shape or parsing failure — try the next model entirely.
                logger.error(f"[{model_name}] unexpected error: {e}")
                break

    # If we exhaust all models without success, surface a clear 502 to the client.
    raise HTTPException(status_code=502, detail="All model attempts failed on Groq")


# ------------------------------
# POST /prepare  (JSON or multipart)
# ------------------------------


@app.function(
    timeout=300,  # room for git clone or zip extraction
    image=image,  # use the image defined above
    secrets=[
        s for s in [groq_secret, auth_secret] if s
    ],  # inject SECRET_TOKEN and GROQ_API_KEY
    volumes={"/data": volume},  # mount the shared volume at /data
)
@modal.fastapi_endpoint(method="POST")
async def prepare(request: Request):
    """
    Normalize an input source (git repo, zip URL, or uploaded zip / pasted code) into files on disk,
    index those files, and return a short-lived "source_id" plus the file list.

    Accepts TWO content types:

    (1) JSON mode (Content-Type: application/json)
        Body matches PrepareBody, e.g.:
        {
          "input_type": github_repo | github_repo_directory | zipped_folder | pasted_code
          "repo_url": "https://github.com/owner/repo",
          "repo_ref": "main",
          "subdir": "packages/service",
          "zip_url": "https://example.com/my.zip",
          "code_snippet": "def hello(): pass",
          "include_globs": ["**/*.py","**/*.md"],
          "exclude_globs": ["**/.git/**","**/node_modules/**"],
          "max_files": 500,
          "max_total_bytes": 20000000
        }

    (2) Multipart mode (Content-Type: multipart/form-data)
        Fields:
          - input_type = zipped_folder
          - file = <a .zip selected on the user's device>
        This path is handy for users who just want to upload a local folder as a zip
        without hosting it anywhere.
    """
    # 1) Enforce auth early so we don't waste work on unauthorized calls.
    _require_token_or_401(request)

    # 2) Decide which parsing branch to take.
    #    We try JSON first; if parsing throws, we fall back to reading form-data.
    body_json = None
    is_json = False
    try:
        body_json = await request.json()
        is_json = True
    except Exception:
        # Not JSON; we will handle multipart below.
        pass

    # 3) Create a per-request working folder under /data using a short unique id.
    #    We store everything for this request under /data/<source_id>/...
    source_id = f"src-{uuid.uuid4().hex[:11]}"
    work_root = os.path.join("/data", source_id)
    os.makedirs(work_root, exist_ok=True)

    try:
        # --------------------
        #       JSON MODE
        # --------------------
        if is_json:
            # 3a) Validate the JSON so clients get nice 400s if they send bad fields.
            try:
                prepared_body = PrepareBody(**body_json)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Bad request: {e}")

            # 3b) Materialize the source according to input_type.
            if prepared_body.input_type in ("github_repo", "github_repo_directory"):
                # REQUIRE repo_url in this case.
                if not prepared_body.repo_url:
                    raise HTTPException(
                        status_code=400, detail="repo_url is required for GitHub input"
                    )
                logger.info(f"Cloning {prepared_body.repo_url}")
                repo_dir = os.path.join(work_root, "repo")  # where we will clone into
                clone_repo(
                    prepared_body.repo_url, prepared_body.repo_ref or "main", repo_dir
                )  # shallow clone; uses GITHUB_TOKEN if present

                # Choose root: either a subdir (if type==github_repo_directory) or the repo root.
                if (
                    prepared_body.input_type == "github_repo_directory"
                    and prepared_body.subdir
                ):
                    root = os.path.join(repo_dir, prepared_body.subdir)
                else:
                    root = repo_dir

                # If caller asked for subdir but it doesn't exist, fail fast.
                if not os.path.isdir(root):
                    raise HTTPException(
                        status_code=400, detail="subdir not found in repository"
                    )

            elif prepared_body.input_type == "zipped_folder":
                # JSON zip flow requires a publicly reachable HTTPS URL.
                if not prepared_body.zip_url:
                    raise HTTPException(
                        status_code=400, detail="zip_url is required for zipped_folder"
                    )
                logger.info(f"Downloading {prepared_body.zip_url}")
                root = download_and_extract_zip(
                    prepared_body.zip_url, os.path.join(work_root, "zip")
                )

            elif prepared_body.input_type == "pasted_code":
                # Write raw text into a "snippet" folder so we can index it like any other source.
                if not prepared_body.code_snippet:
                    raise HTTPException(
                        status_code=400,
                        detail="code_snippet is required for pasted_code",
                    )
                logger.info("Writing snippet")
                root = write_snippet_temp(work_root, prepared_body.code_snippet)

            else:
                raise HTTPException(status_code=400, detail="unknown input_type")

            # 3c) Pick include/exclude filters;  defaults cover common code/text & skip heavy dirs.
            include = prepared_body.include_globs or [
                "**/*.py",
                "**/*.ts",
                "**/*.js",
                "**/*.go",
                "**/*.java",
                "**/*.cs",
                "**/*.rb",
                "**/*.php",
                "**/*.rs",
                "**/*.cpp",
                "**/*.c",
                "**/*.md",
                "**/*.txt",
            ]
            exclude = prepared_body.exclude_globs or [
                "**/.git/**",
                "**/node_modules/**",
                "**/.venv/**",
                "**/dist/**",
                "**/build/**",
                "**/.cache/**",
            ]

            # 3d) Build the file index according to filters and caps.
            files = index_files(
                root=root,
                include_globs=include,
                exclude_globs=exclude,
                max_files=prepared_body.max_files or 500,
                max_bytes=prepared_body.max_total_bytes or 20_000_000,
            )

        # ------------------------
        #     MULTIPART MODE
        # ------------------------
        else:
            # In multipart we only support "zipped_folder" with an actual uploaded zip file.
            form = await request.form()
            input_type = (form.get("input_type") or "").strip()
            if input_type != "zipped_folder":
                raise HTTPException(
                    status_code=400,
                    detail="multipart supports input_type=zipped_folder only; use JSON for other types",
                )

            # FastAPI parses uploaded files into UploadFile objects.
            upload = form.get("file")
            if not isinstance(upload, UploadFile):
                raise HTTPException(
                    status_code=400,
                    detail="attach a .zip file as form field named 'file'",
                )
            if upload.filename and not upload.filename.lower().endswith(".zip"):
                raise HTTPException(
                    status_code=400, detail="uploaded file must be a .zip"
                )

            # Stream the uploaded file to disk in chunks so memory usage stays low.
            local_zip_dir = os.path.join(work_root, "upload")
            os.makedirs(local_zip_dir, exist_ok=True)
            local_zip_path = os.path.join(local_zip_dir, "upload.zip")
            with open(local_zip_path, "wb") as out:
                while True:
                    chunk = await upload.read(1 << 20)  # 1 MiB
                    if not chunk:
                        break
                    out.write(chunk)

            # Extract the local zip into a subfolder; that folder becomes our root for indexing.
            extract_root = os.path.join(local_zip_dir, "unzipped")
            root = extract_zip_file(local_zip_path, extract_root)

            # Defaults for include/exclude when using uploads.
            include = [
                "**/*.py",
                "**/*.ts",
                "**/*.js",
                "**/*.go",
                "**/*.java",
                "**/*.cs",
                "**/*.rb",
                "**/*.php",
                "**/*.rs",
                "**/*.cpp",
                "**/*.c",
                "**/*.md",
                "**/*.txt",
            ]
            exclude = [
                "**/.git/**",
                "**/node_modules/**",
                "**/.venv/**",
                "**/dist/**",
                "**/build/**",
                "**/.cache/**",
            ]
            files = index_files(root, include, exclude, 500, 20_000_000)

        # 4) Persist a tiny manifest that records the *actual* root we used.
        #    This allows /summarize to read the same place without guessing.
        with open(os.path.join(work_root, "manifest.json"), "w", encoding="utf8") as f:
            json.dump({"root": root}, f)

        # 5) VERY IMPORTANT: commit the volume so the writes are visible to /summarize.
        volume.commit()

        # 6) Return the source id (for subsequent calls) and the file index (for the UI).
        return {"source_id": source_id, "files": files}

    except HTTPException:
        # On "expected" errors (400/401/etc.), clean up any partial folder to avoid leaks.
        shutil.rmtree(work_root, ignore_errors=True)
        # We do NOT need to commit deletions here, since /summarize won't be called with this source_id.
        raise

    except Exception as e:
        # On unexpected errors, also clean up then surface a 500 to the client.
        shutil.rmtree(work_root, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------
# POST /summarize (JSON only)
# ------------------------------


@app.function(
    timeout=300,  # allow time for model call
    image=image,  # same image as /prepare
    secrets=[s for s in [groq_secret, auth_secret] if s],  # auth + Groq key
    volumes={"/data": volume},  # mount the same shared volume
)
@modal.fastapi_endpoint(method="POST")
async def summarize(request: Request):
    """
    Produce structured documentation sections based on user-selected files.

    Flow:
      - Authenticate (Bearer token).
      - volume.reload() to see latest /prepare state.
      - Load /data/<source_id>/manifest.json to find the root folder.
      - Read and concatenate "selected_paths" into one string bundle.
      - Ask Groq to return *strict JSON* with keys equal to the "sections[].id" values.
      - Optionally delete the working folder if "cleanup": true, and volume.commit() that deletion.
      - Return { source_id, sections: {<id>: value, ...}, meta: {...} }.

    Expected request body:
      {
        "source_id": "src-abcde12345",
        "selected_paths": ["README.md", "src/main.ts"],
        "sections": [
          {"id": "title", "type": "short_text", "max_chars": 120},
          {"id": "overview", "type": "markdown"},
          {"id": "references", "type": "list", "item_type": "url"}
        ],
        "constraints": {"audience": "business", "tone": "non_technical", "reading_level": "grade_7"},
        "cleanup": true
      }
    """
    # 1) Enforce auth first.
    _require_token_or_401(request)

    # 2) VERY IMPORTANT: reload the volume so we see what /prepare committed.
    volume.reload()

    # 3) Parse and validate JSON body.
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        summarize_body = SummarizeBody(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bad request: {e}")

    # 4) Locate the prepared working folder using the source_id.
    work_root = os.path.join("/data", summarize_body.source_id)
    manifest_path = os.path.join(work_root, "manifest.json")
    if not os.path.isfile(manifest_path):
        # This happens if: wrong id, expired/cleaned-up folder, or /prepare never committed.
        raise HTTPException(status_code=400, detail="unknown source_id or expired")

    # 5) Read the manifest to learn the *actual* root folder.
    with open(manifest_path, "r", encoding="utf8") as f:
        manifest = json.load(f)
    root = manifest.get("root")
    if not root or not os.path.isdir(root):
        raise HTTPException(status_code=400, detail="prepared source is missing")

    # 6) Read and join the selected files into one big text bundle with clear per-file headers.
    bundle = read_selected_bundle(root, summarize_body.selected_paths)

    # 7) Call Groq to generate the sections as strict JSON.
    sections_json = _call_llm_sections(
        bundle, summarize_body.sections, summarize_body.constraints
    )

    # 8) If requested, delete the folder and commit the deletion so future calls won't find it.
    if summarize_body.cleanup:
        shutil.rmtree(work_root, ignore_errors=True)
        volume.commit()  # make the deletion visible to other functions / later calls

    # 9) Return the shaped result.
    return {
        "source_id": summarize_body.source_id,
        "sections": sections_json,
        "meta": {"warnings": [], "truncated": False},
    }
