import os
import sys
from typing import Optional

try:
    # CrewAI core components
    from crewai import Agent, Task, Crew  # type: ignore
    # Preferred lightweight LLM wrapper in modern CrewAI (avoids LangChain)
    try:
        from crewai import LLM  # type: ignore
    except Exception:  # pragma: no cover - older CrewAI versions may not export LLM
        LLM = None  # type: ignore
except Exception:  # pragma: no cover - crewai not installed
    Agent = None  # type: ignore
    Task = None  # type: ignore
    Crew = None  # type: ignore
    LLM = None  # type: ignore


__all__ = ["crewai_summarize"]


class CrewAIDependencyError(RuntimeError):
    pass


def _ensure_dependencies() -> None:
    if Agent is None or Task is None or Crew is None:
        raise CrewAIDependencyError(
            "crewai is not installed. Install with: pip install crewai"
        )
    # Require watsonx credentials via .env
    if not os.getenv("WATSONX_APIKEY") or not os.getenv("WATSONX_PROJECT_ID"):
        raise CrewAIDependencyError(
            "Missing WATSONX_APIKEY or WATSONX_PROJECT_ID in environment (.env)"
        )


def _build_llm(model: str) -> object:
    """
    Build a CrewAI LLM configured for IBM watsonx.
    If LLM wrapper isn't available, return the model string for compatibility.
    """
    if LLM is not None:
        # CrewAI may route by provider name; rely on env for extra params.
        return LLM(
            model=model,
            provider="watsonx",
            api_key=os.getenv("WATSONX_APIKEY"),
            temperature=float(os.getenv("CREWAI_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("CREWAI_MAX_TOKENS", "800")),
        )
    return model  # type: ignore[return-value]


def crewai_summarize(
    text: str,
    *,
    style: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Summarize input text using a CrewAI Agent powered by IBM watsonx.

    Environment variables (via .env):
      - WATSONX_APIKEY (required)
      - WATSONX_PROJECT_ID (required)
      - WATSONX_MODEL (optional, defaults to ibm/granite-13b-chat-v2)
      - WATSONX_URL (optional)
      - CREWAI_TEMPERATURE (optional, default 0.2)
      - CREWAI_MAX_TOKENS (optional, default 800)
      - CREWAI_VERBOSE (optional, "1" to enable)
    """
    _ensure_dependencies()

    input_text = (text or "").strip()
    if len(input_text) < 5:
        raise ValueError("text must be at least 5 characters")

    model_name = model or os.getenv("WATSONX_MODEL", "ibm/granite-13b-chat-v2")
    llm = _build_llm(model_name)

    verbose = os.getenv("CREWAI_VERBOSE", "0") == "1"

    agent = Agent(
        role="Clinical Text Summarizer",
        goal=(
            "Produce faithful, concise summaries with bullet points and a brief "
            "paragraph tailored for clinicians."
            "Will provide most likely diagnosis." 
        ),
        backstory=(
            "Experienced medical scribe skilled at capturing salient findings, "
            "assessments, and plans without adding information not present in the source."
        ),
        allow_delegation=False,
        verbose=verbose,
        llm=llm,
    )

    style_instruction = (
        f"Use this style: {style}. " if style and style.strip() else ""
    )

    task = Task(
        description=(
            "Summarize the provided clinical text. "
            "Return: (1) 3-7 bullet points of key facts, (2) a 2-4 sentence "
            "narrative summary. "
            "Cite no external knowledge and do not fabricate details. "
            + style_instruction +
            "\n\nTEXT TO SUMMARIZE:\n" + input_text
        ),
        expected_output=(
            "A concise, accurate summary with clear bullets followed by a short paragraph."
        ),
        agent=agent,
    )

    # Primary path: CrewAI orchestrates generation via watsonx LLM
    try:
        crew = Crew(agents=[agent], tasks=[task])
        result = crew.kickoff()
        return str(result).strip()
    except Exception:
        # Fallback: directly use our watsonx summarizer to ensure watsonx usage
        try:
            from .watsonx_summarizer import watsonx_summarize  # type: ignore
            return watsonx_summarize(input_text, style=style)
        except Exception as exc:
            raise CrewAIDependencyError(str(exc))


def _read_all_stdin() -> str:
    return sys.stdin.read()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Summarize text using a CrewAI agent with IBM watsonx"
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
        help="Optional style guidance for the summary",
    )
    parser.add_argument(
        "--model",
        dest="model",
        default=None,
        help="Watsonx model id (default: env WATSONX_MODEL)",
    )

    args = parser.parse_args()
    payload = args.text
    if payload is None or payload == "-":
        payload = _read_all_stdin()

    try:
        summary = crewai_summarize(payload or "", style=args.style, model=args.model)
        print(summary)
    except Exception as exc:  # pragma: no cover - CLI convenience
        sys.stderr.write(f"[error] {exc}\n")
        sys.exit(1)


