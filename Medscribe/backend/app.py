# Medscribe/backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # type: ignore

try:
    # Direct watsonx summarizer (no CrewAI dependency needed for live mode)
    from .watsonx_summarizer import watsonx_summarize  # type: ignore
except Exception:
    watsonx_summarize = None  # type: ignore


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _has_watsonx_creds() -> bool:
    return bool(_env("WATSONX_APIKEY") and _env("WATSONX_PROJECT_ID"))


if load_dotenv:
    load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


def analyze_clinical_note(note_text: str, patient_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    note_len = len(note_text or "")
    if note_len < 5:
        return {"error": "note_text must be at least 5 characters"}

    live = _has_watsonx_creds()
    if live:
        try:
            from .utils.text_index import split_into_sentences, index_sentences
            from .utils.validation import validate_outputs
            from .watsonx_summarizer import watsonx_summarize_with_citations

            pairs = split_into_sentences(note_text)
            id_to_sentence = index_sentences(pairs)
            raw = watsonx_summarize_with_citations(
                note_text,
                numbered_sentences=pairs,
                style=(patient_context or {}).get("style"),
            )
            raw["model_info"] = {
                "provider": "ibm_watsonx.ai",
                "model": _env("WATSONX_MODEL", "ibm/granite-13b-chat-v2"),
                "mode": "live",
            }
            validated = validate_outputs(raw, id_to_sentence, threshold=0.30)
            return validated
        except Exception as exc:
            return {"error": f"watsonx error: {exc}"}

    # Mock response for local/dev without credentials
    summary = {
        "chief_complaint": "Chest pain",
        "history": "55-year-old with hypertension presents with intermittent chest pain for 2 days.",
        "assessment": "Rule out acute coronary syndrome. Consider GERD.",
        "plan": "Obtain EKG, troponins, start aspirin if no contraindication.",
    }
    suggested_orders = [
        {"type": "lab", "name": "Troponin I", "rationale": "Assess for myocardial injury", "priority": "stat"},
        {"type": "imaging", "name": "12-lead EKG", "rationale": "Evaluate ischemic changes", "priority": "stat"},
        {"type": "medication", "name": "Aspirin 325 mg PO once", "rationale": "Antiplatelet therapy if not contraindicated", "priority": "urgent"},
        {"type": "consult", "name": "Cardiology consult", "rationale": "Evaluate chest pain and risk stratification", "priority": "urgent"},
    ]
    model_info = {
        "provider": "ibm_watsonx.ai",
        "model": _env("WATSONX_MODEL", "ibm/granite-13b-instruct-v2"),
        "mode": "mock",
    }
    return {"summary": summary, "suggested_orders": suggested_orders, "model_info": model_info}


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    note_text = data.get("note_text", "")
    patient_context = data.get("patient_context") or None
    result = analyze_clinical_note(note_text, patient_context)
    status = 200 if "error" not in result else 400
    return jsonify(result), status


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port_str = os.getenv("PORT", "5001")
    debug = os.getenv("DEBUG", "1") == "1"
    use_reloader = os.getenv("USE_RELOADER", "1") == "1"
    fallback_auto = os.getenv("PORT_FALLBACK_AUTO", "0") == "1"
    try:
        app.run(host=host, port=int(port_str), debug=debug, use_reloader=use_reloader)
    except OSError as exc:
        if "Address already in use" in str(exc) and fallback_auto:
            # Bind to an ephemeral free port
            app.run(host=host, port=0, debug=debug, use_reloader=use_reloader)
        else:
            raise