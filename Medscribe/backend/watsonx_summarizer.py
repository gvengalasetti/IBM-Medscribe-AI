import os
import sys
import json
from typing import Optional, Dict, Any, List, Tuple

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


__all__ = ["watsonx_summarize", "watsonx_summarize_with_citations"]


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
        "You are an expert medical scribe and clinician. Summarize the clinical text "
        "faithfully without fabricating details.\n\n"
    )
    rules = (
        "- Provide 3-7 bullet points of key facts (diagnoses, symptoms, labs, treatments).\n"
        "- Then provide a 2-4 sentence narrative summary.\n"
        "- Provide the most likely diagnosis or differential if applicable.\n"
        "- List 2-4 probable treatments/cures with concise rationale (evidence-based, no fabrication).\n"
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


def _extract_json(text: str) -> Dict[str, Any]:
    raw = (text or "").strip().lstrip("\ufeff")  # strip BOM if present

    # 1) Strip fenced code blocks if present
    if raw.startswith("```"):
        parts = raw.split("```", 2)
        raw = parts[1] if len(parts) > 1 else parts[-1]
        raw = raw.strip()
        # Drop possible language hint line
        if not raw.startswith("{") and "\n" in raw:
            raw = "\n".join(raw.splitlines()[1:])

    # 2) Fast path: direct JSON
    try:
        return json.loads(raw)
    except Exception:
        pass

    # 3) Robust scan: find first balanced JSON object outside of quotes
    def find_balanced_object(s: str) -> str | None:
        start = s.find('{')
        if start == -1:
            return None
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(s)):
            ch = s[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            else:
                if ch == '"':
                    in_str = True
                    continue
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        return s[start:i+1]
        return None

    candidate = find_balanced_object(raw)
    if candidate is None:
        # 4) Fallback: trim to outermost braces if present
        try:
            l = raw.index('{')
            r = raw.rindex('}')
            candidate = raw[l:r+1]
        except Exception:
            candidate = None

    if candidate is not None:
        # 5) Sanitize trailing commas like ,}\n or ,]\n
        import re as _re
        sanitized = _re.sub(r",\s*([}\]])", r"\1", candidate)
        # Attempt brace/bracket repair if unbalanced
        def _repair_brackets(s: str) -> str:
            stack = []
            out = []
            in_str = False
            esc = False
            pairs = { '{': '}', '[': ']' }
            for ch in s:
                out.append(ch)
                if in_str:
                    if esc:
                        esc = False
                    elif ch == '\\':
                        esc = True
                    elif ch == '"':
                        in_str = False
                    continue
                else:
                    if ch == '"':
                        in_str = True
                        continue
                    if ch in pairs:
                        stack.append(pairs[ch])
                    elif ch in (']', '}'):
                        if stack and stack[-1] == ch:
                            stack.pop()
            while stack:
                out.append(stack.pop())
            return ''.join(out)

        for attempt in range(2):
            try:
                return json.loads(sanitized)
            except Exception:
                sanitized = _repair_brackets(sanitized)

    preview = raw[:300].replace('\n', ' ')
    raise ValueError(f"Unable to parse JSON from model output. Preview: {preview}")


def _build_citation_prompt(note_text: str, numbered_sentences: List[Tuple[int, str]], style: Optional[str]) -> str:
    header = (
        "You are an expert medical scribe and clinician. "
        "Read the NOTE and the NUMBERED_SENTENCES (1..N). "
        "Return ONLY valid JSON (no prose, no markdown), following the schema below. "
        "Use ONLY evidence from the numbered sentences for citations.\n\n"
    )
    rules = (
        "- Produce:\n"
        "  1) summary_bullets: 3-7 short bullets of key facts; each must include citations [ids].\n"
        "  2) suggested_orders: array of recommendations with fields: {type, name, reason, citations[], confidence, external_citations[]?}. "
        "Focus on treatment recommendations first (e.g., medications) when clinically appropriate; include dose/route/duration if standard and supported. List 2-4 items max; do not fabricate.\n"
        "- All 'citations' must be sentence IDs from NUMBERED_SENTENCES that support the claim.\n"
        "- If evidence is insufficient for any bullet or order, OMIT that item (do not guess).\n"
        "- confidence is a number in [0,1].\n"
        "- Keep 'reason' concise and specific to the patient context.\n"
        "- Avoid external citations unless clearly applicable guidelines are known; include title/url/year/snippet if used.\n"
        "- Prefer concise, clinically faithful phrasing.\n"
    )
    style_line = (f"- Style: {style}\n" if style and style.strip() else "")
    schema = (
        "JSON schema:\n"
        "{\n"
        "  \"summary_bullets\": [ { \"text\": str, \"citations\": [int] } ],\n"
        "  \"suggested_orders\": [ {\n"
        "     \"type\": \"lab\"|\"imaging\"|\"medication\"|\"consult\"|\"other\",\n"
        "     \"name\": str,\n"
        "     \"reason\": str,\n"
        "     \"citations\": [int],\n"
        "     \"confidence\": number,\n"
        "     \"external_citations\": [ { \"title\": str, \"url\": str, \"year\": number, \"snippet\": str } ]\n"
        "  } ]\n"
        "}\n"
    )
    numbered = "NUMBERED_SENTENCES:\n" + "\n".join([f"{i}. {s}" for i, s in numbered_sentences])
    body = "\nNOTE:\n" + note_text.strip()
    instruction = (
        "\nReturn ONLY JSON. Do not include explanations or markdown. "
        "Ensure valid JSON (no trailing commas), and all arrays/objects are closed."
    )
    return header + rules + style_line + schema + "\n\n" + numbered + body + instruction


def watsonx_summarize_with_citations(
    text: str,
    *,
    numbered_sentences: List[Tuple[int, str]],
    style: Optional[str] = None,
) -> Dict[str, Any]:
    _load_env()
    src = (text or "").strip()
    if len(src) < 5:
        raise ValueError("text must be at least 5 characters")
    _ensure_wx_ready()
    model = _get_wx_model()
    prompt = _build_citation_prompt(src, numbered_sentences, style)
    result = model.generate(prompt=prompt)
    if isinstance(result, dict):
        items = result.get("results") or []
        content = (items[0].get("generated_text", "") if items else "").strip()
    else:
        content = str(result).strip()
    payload = _extract_json(content)
    return payload


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


