import os
import requests
import time
import textwrap
import logging
from typing import Optional, List

from file_utils import (
    build_context_from_main,
    find_all_main_files, 
    prompt_user_to_choose,
)
from summary_error import SummarizationError

logging.basicConfig(
    level=logging.INFO,
    format="[{levelname}] {message}",
    style="{"
)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def summarize_main_logic(full_code_context: str, retries: int = 3, backoff: int = 2) -> str:
    """Attempts to summarize using multiple fallback Groq models if needed."""
    if not GROQ_API_KEY:
        raise SummarizationError("Missing GROQ_API_KEY. Set it in your environment.")

    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prioritized_models = ["llama3-70b-8192", "llama3-8b-8192", "gemma-7b-it"]

    prompt = textwrap.dedent(f"""
        You are a technical product analyst writing documentation for business stakeholders. Please focus on
        the business problem being solved not the code. Your goal is to ensure that the code used to solve
        the business problem is translated to natural language seamlessly and with articulate ease to
        non-technical personnel. These sections should be present in the output "Business Problem",
        "Overview", "Methodology", and "Conclusion" with graphics/examples being shown in each section
        as needed.

        Below is a combined view of the main Python file and all local modules it uses.
        This collection represents the core logic of the project.

        Your goals:
        1. Identify the **business problem** the code is solving.
        2. Summarize the **methodology** and any reasoning behind the implementation choices.
        3. Do NOT list any function being used! Keep the tone **non-technical** and easy to **understand**.
        4. Use clear, simple language appropriate for a **non-technical executive**.
        5. SOLELY focus on the **business problem** and what is being solved with the code.

        Codebase:
        {full_code_context}
    """).strip()

    for model_name in prioritized_models:
        logger.info(f"Trying model: {model_name}")
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at converting code into business documentation for non-technical readers."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.4,
            "max_tokens": 2500
        }

        for attempt in range(1, retries + 1):
            logger.info(f"Attempt {attempt} of {retries}...")
            try:
                response = requests.post(endpoint, headers=headers, json=payload, timeout=30)

                if response.status_code != 200:
                    logger.warning(f"[{model_name}] Groq API error response:\n{response.text}")
                    break  # Skip to next model

                response.raise_for_status()
                data = response.json()
                summary = data["choices"][0]["message"]["content"].strip()

                # ✅ Log token usage
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", "?")
                completion_tokens = usage.get("completion_tokens", "?")
                total_tokens = usage.get("total_tokens", "?")

                logger.info(f"✅ Successfully received summary using model: {model_name}")
                logger.info(f"🔢 Token usage: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}")

                return logger.info(f"🤖 Summary generated using `{model_name}`\n\n{summary}")

            except requests.RequestException as e:
                logger.warning(f"[Attempt {attempt}] API request failed: {e}")
                if attempt == retries:
                    logger.error(f"All retry attempts failed for model: {model_name}")
                time.sleep(backoff * attempt)

            except (KeyError, ValueError) as e:
                logger.error(f"Unexpected API response format: {e}")
                break  # Skip to next model

    raise SummarizationError("All model attempts failed. No valid response from Groq.")


def summarize_project(root_dir: Optional[str] = None) -> str:
    """Entry point: finds main.py, builds context, summarizes the project."""
    root_dir = root_dir or os.getcwd()
    logger.info(f"Starting summarization in project root: {root_dir}")
    
    main_files = find_all_main_files(root_dir)
    chosen_path = prompt_user_to_choose(main_files)
    if not chosen_path:
        return "❌ No main.py file found in the project."

    try:
        logger.info(f"Selected file for summarization: {chosen_path}")
        context = build_context_from_main(chosen_path)
        return summarize_main_logic(context)
    except SummarizationError as e:
        logger.error(f"Summarization failed: {e}")
        return f"❌ Summarization failed: {e}"