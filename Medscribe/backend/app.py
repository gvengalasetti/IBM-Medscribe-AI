# # Medscribe/backend/app.py
# # -----------------------------------------------------------------------------
# # Simple Flask API to accept a clinical note and return a mocked Granite/watsonx-style
# # summary and structured order suggestions. Starts in "mock" mode (free).
# # -----------------------------------------------------------------------------

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import os
# import re
# from typing import List, Dict, Any, Tuple
# from dotenv import load_dotenv
# from .agent import watsonx_chat_agent

# load_dotenv()
# app = Flask(__name__)
# # Allow local frontend (Vite on 5173) to call this API during development
# CORS(app, resources={r"/*": {"origins": "*"}})

# WATSONX_MODE = os.getenv("WATSONX_MODE", "mock")  # mock | live (keep mock for free dev)
# wx_client = None

# _SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')

# def split_into_sentences(note_text: str) -> List[Tuple[int, str]]:
#     raw = [s.strip() for s in _SENT_SPLIT.split(note_text or "") if s.strip()]
#     return [(i + 1, s) for i, s in enumerate(raw)]

# def _tokenize(text: str) -> set:
#     return set(re.findall(r"[a-z0-9]+", (text or "").lower()))

# def _jaccard(a: str, b: str) -> float:
#     ta, tb = _tokenize(a), _tokenize(b)
#     if not ta or not tb:
#         return 0.0
#     inter = len(ta & tb)
#     union = len(ta | tb)
#     return inter / union if union else 0.0

# def validate_with_citations(summary_bullets: List[Dict[str, Any]],
#                             orders: List[Dict[str, Any]],
#                             id_to_sentence: Dict[int, str],
#                             threshold: float = 0.30):
#     def supported(text: str, cites: List[int]) -> bool:
#         if not cites:
#             return False
#         best = 0.0
#         for cid in cites:
#             src = id_to_sentence.get(int(cid), "")
#             best = max(best, _jaccard(text, src))
#         return best >= threshold

#     good_bullets: List[Dict[str, Any]] = []
#     for b in summary_bullets or []:
#         txt = (b or {}).get("text", "")
#         cites = (b or {}).get("citations") or []
#         if supported(txt, cites):
#             good_bullets.append({
#                 "text": txt,
#                 "citations": [int(c) for c in cites if int(c) in id_to_sentence]
#             })

#     good_orders: List[Dict[str, Any]] = []
#     for o in orders or []:
#         name = (o or {}).get("name", "")
#         reason = (o or {}).get("reason", "")
#         cites = (o or {}).get("citations") or []
#         if supported(name + " " + reason, cites):
#             good_orders.append({
#                 "name": name,
#                 "type": (o or {}).get("type"),
#                 "reason": reason,
#                 "citations": [int(c) for c in cites if int(c) in id_to_sentence],
#                 "confidence": float((o or {}).get("confidence", 0.0)),
#             })

#     return good_bullets, good_orders

# def analyze_clinical_note(note_text: str, patient_context: dict | None = None) -> dict:
#     """
#     Mocked analyzer. Later, if WATSONX_MODE == 'live', replace with an actual watsonx.ai call.
#     """
#     # Minimal guardrails to keep responses consistent
#     note_len = len(note_text or "")
#     if note_len < 5:
#         return {"error": "note_text must be at least 5 characters"}

#     if WATSONX_MODE == "live":
#         # Minimal live mode: return a plain text summary via chat agent
#         summary_text = watsonx_chat_agent(
#             f"Summarize clinically: {note_text}"
#         )
#         model_info = {
#             "provider": "ibm_watsonx.ai",
#             "model": os.getenv("WATSONX_MODEL", "ibm/granite-13b-chat-v2"),
#             "mode": "live"
#         }
#         return {"summary": {"text": summary_text}, "suggested_orders": [], "model_info": model_info}
#     else:
#         summary = {
#             "chief_complaint": "Chest pain",
#             "history": "55-year-old with hypertension presents with intermittent chest pain for 2 days.",
#             "assessment": "Rule out acute coronary syndrome. Consider GERD.",
#             "plan": "Obtain EKG, troponins, start aspirin if no contraindication."
#         }
#         suggested_orders = [
#             {"type": "lab", "name": "Troponin I", "rationale": "Assess for myocardial injury", "priority": "stat"},
#             {"type": "imaging", "name": "12-lead EKG", "rationale": "Evaluate ischemic changes", "priority": "stat"},
#             {"type": "medication", "name": "Aspirin 325 mg PO once", "rationale": "Antiplatelet therapy if not contraindicated", "priority": "urgent"},
#             {"type": "consult", "name": "Cardiology consult", "rationale": "Evaluate chest pain and risk stratification", "priority": "urgent"},
#         ]
#         model_info = {
#             "provider": "ibm_watsonx.ai",
#             "model": "ibm/granite-13b-instruct-v2",
#             "mode": WATSONX_MODE
#         }
#         return {"summary": summary, "suggested_orders": suggested_orders, "model_info": model_info}

# @app.get("/health")
# def health():
#     return jsonify({"status": "ok"})

# @app.post("/analyze")
# def analyze():
#     """
#     Expects JSON: { "note_text": "...", "patient_context": { ... }? }
#     Returns: { "summary": {...}, "suggested_orders": [...], "model_info": {...} }
#     """
#     data = request.get_json(silent=True) or {}
#     note_text = data.get("note_text", "")
#     patient_context = data.get("patient_context") or None

#     result = analyze_clinical_note(note_text, patient_context)
#     status = 200 if "error" not in result else 400
#     return jsonify(result), status

# if __name__ == "__main__":
#     port = int(os.getenv("PORT", "5000"))
#     app.run(host="0.0.0.0", port=port, debug=True)