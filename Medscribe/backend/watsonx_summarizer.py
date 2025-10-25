import os
import sys
from typing import Optional

try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore
    find_dotenv = None  # type: ignore

try:
    # Reuse existing helper and consistent config
    from .agent import _get_wx_model  # type: ignore
except Exception as exc:  # pragma: no cover
    _get_wx_model = None  # type: ignore


__all__ = ["watsonx_summarize"]


def _load_env() -> None:
    # Load .env if available (non-fatal if missing)
    if load_dotenv and find_dotenv:
        env_path = find_dotenv(usecwd=True)
        if env_path:
            load_dotenv(env_path)


def _ensure_wx_ready() -> None:
    if _get_wx_model is None:
        raise RuntimeError("agent._get_wx_model unavailable; check installation")
    # Minimal validation so errors are clearer before API call
    required = ["WATSONX_APIKEY", "WATSONX_PROJECT_ID"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            "Missing environment: " + ", ".join(missing) +
            ". Ensure your .env is loaded."
        )


def _build_prompt(text: str, style: Optional[str]) -> str:
    header = (
        "You are an expert medical scribe. Summarize the clinical text "
        "faithfully without fabricating details.\n\n"
    )
    rules = (
        "- Provide 3-7 bullet points of key facts (diagnoses, symptoms, labs, treatments).\n"
        "- Then provide a 2-4 sentence narrative summary.\n"
        "- Do not add information not present in the source.\n"
    )
    style_line = (f"- Style: {style}\n" if style and style.strip() else "")
    body = "\nTEXT TO SUMMARIZE:\n" + text.strip()
    return header + rules + style_line + body


def watsonx_summarize(
    text: str,
    *,
    style: Optional[str] = None,
) -> str:
    """
    Summarize input text using IBM watsonx.ai foundation model configured via .env.

    Expects environment variables (via .env):
      - WATSONX_APIKEY (required)
      - WATSONX_PROJECT_ID (required)
      - WATSONX_URL (optional; default in helper)
      - WATSONX_MODEL (optional; default in helper)
    """
    _load_env()
    src = (text or "").strip()
    if len(src) < 5:
        raise ValueError("text must be at least 5 characters")

    _ensure_wx_ready()
    model = _get_wx_model()
    prompt = _build_prompt(src, style)
    result = model.generate(prompt=prompt)
    if isinstance(result, dict):
        items = result.get("results") or []
        return (items[0].get("generated_text", "") if items else "").strip()
    return str(result).strip()


def _read_all_stdin() -> str:
    return sys.stdin.read()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Summarize text using IBM watsonx model (env-configured)"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to summarize. Use '-' to read from stdin.",
    )
    parser.add_argument(
        "--style",
        dest="style",
        default=None,
        help="Optional style guidance (e.g., 'bullet-heavy', 'SOAP note style')",
    )

    args = parser.parse_args()
    payload = args.text
    if payload is None or payload == "-":
        payload = _read_all_stdin()

    try:
        summary = watsonx_summarize(payload or "", style=args.style)
        print(summary)
    except Exception as exc:  # pragma: no cover - CLI convenience
        sys.stderr.write(f"[error] {exc}\n")
        sys.exit(1)


