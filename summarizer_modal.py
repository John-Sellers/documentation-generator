import os
import modal
from fastapi import Request, HTTPException

image = (
    modal.Image.debian_slim()
    .pip_install_from_requirements("requirements.txt")
    .pip_install("fastapi[standard]")
    .env({"PYTHONPATH": "/root/app"})
    .add_local_dir(".", remote_path="/root/app")
)

groq_secret   = modal.Secret.from_name("groq-api-key")   # supplies GROQ_API_KEY
auth_secret   = modal.Secret.from_name("secret-token")   # supplies SECRET_TOKEN

app = modal.App("python_documentation_generator", image=image)

@app.function(timeout=300, secrets=[groq_secret, auth_secret])
@modal.fastapi_endpoint(method="POST")
async def summarize_python(request: Request):
    """
    Send the token in either place:

    Header:
        Authorization: Bearer my-secret-value

    Body JSON:
        { "token": "my-secret-value", "project_path": "/root/app" }
    """
    from src.llm import summarize_project

    # 1. verify token
    expected_token = os.getenv("SECRET_TOKEN")
    header_token   = request.headers.get("authorization", "").replace("Bearer ", "")
    body_json      = await request.json()
    body_token     = body_json.get("token") if isinstance(body_json, dict) else None

    supplied_token = header_token or body_token
    if supplied_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    # 2. pick path
    project_path = body_json.get("project_path", "/root/app") if isinstance(body_json, dict) else "/root/app"

    # 3. summarize
    summary_text = summarize_project(project_path)

    return {"summary": summary_text}