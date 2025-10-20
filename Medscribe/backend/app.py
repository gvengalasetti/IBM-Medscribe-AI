# Medscribe/backend/app.py
# -----------------------------------------------------------------------------
# Simple Flask API to accept a clinical note and return a mocked Granite/watsonx-style
# summary and structured order suggestions. Starts in "mock" mode (free).
# -----------------------------------------------------------------------------

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from .watsonx_client import WatsonxClient

load_dotenv()
app = Flask(__name__)
# Allow local frontend (Vite on 5173) to call this API during development
CORS(app, resources={r"/*": {"origins": "*"}})

WATSONX_MODE = os.getenv("WATSONX_MODE", "mock")  # mock | live (keep mock for free dev)
wx_client = None

def analyze_clinical_note(note_text: str, patient_context: dict | None = None) -> dict:
    """
    Mocked analyzer. Later, if WATSONX_MODE == 'live', replace with an actual watsonx.ai call.
    """
    # Minimal guardrails to keep responses consistent
    note_len = len(note_text or "")
    if note_len < 5:
        return {"error": "note_text must be at least 5 characters"}

    if WATSONX_MODE == "live":
        global wx_client
        if wx_client is None:
            wx_client = WatsonxClient()
        summary = wx_client.summarize_note_to_json(note_text)
        model_info = {
            "provider": "ibm_watsonx.ai",
            "model": os.getenv("WATSONX_MODEL", "ibm/granite-13b-instruct-v2"),
            "mode": "live"
        }
        return {"summary": summary, "suggested_orders": [], "model_info": model_info}
    else:
        summary = {
            "chief_complaint": "Chest pain",
            "history": "55-year-old with hypertension presents with intermittent chest pain for 2 days.",
            "assessment": "Rule out acute coronary syndrome. Consider GERD.",
            "plan": "Obtain EKG, troponins, start aspirin if no contraindication."
        }
        suggested_orders = [
            {"type": "lab", "name": "Troponin I", "rationale": "Assess for myocardial injury", "priority": "stat"},
            {"type": "imaging", "name": "12-lead EKG", "rationale": "Evaluate ischemic changes", "priority": "stat"},
            {"type": "medication", "name": "Aspirin 325 mg PO once", "rationale": "Antiplatelet therapy if not contraindicated", "priority": "urgent"},
            {"type": "consult", "name": "Cardiology consult", "rationale": "Evaluate chest pain and risk stratification", "priority": "urgent"},
        ]
        model_info = {
            "provider": "ibm_watsonx.ai",
            "model": "ibm/granite-13b-instruct-v2",
            "mode": WATSONX_MODE
        }
        return {"summary": summary, "suggested_orders": suggested_orders, "model_info": model_info}

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.post("/analyze")
def analyze():
    """
    Expects JSON: { "note_text": "...", "patient_context": { ... }? }
    Returns: { "summary": {...}, "suggested_orders": [...], "model_info": {...} }
    """
    data = request.get_json(silent=True) or {}
    note_text = data.get("note_text", "")
    patient_context = data.get("patient_context") or None

    result = analyze_clinical_note(note_text, patient_context)
    status = 200 if "error" not in result else 400
    return jsonify(result), status

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)