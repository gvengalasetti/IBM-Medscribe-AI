import json
import os
from typing import Any, Dict

# Runtime dependency: ibm-watsonx-ai
# pip install ibm-watsonx-ai
try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import Model
except Exception:  # pragma: no cover - allow file import when package not installed
    Credentials = None  # type: ignore
    Model = None  # type: ignore


class WatsonxClient:
    """
    Thin wrapper around IBM watsonx.ai Granite text generation for summarization.
    Reads configuration from environment variables:
      - WATSONX_APIKEY
      - WATSONX_URL (e.g., https://us-south.ml.cloud.ibm.com)
      - WATSONX_PROJECT_ID
      - WATSONX_MODEL (default: ibm/granite-13b-instruct-v2)
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("WATSONX_APIKEY", "")
        self.url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.project_id = os.getenv("WATSONX_PROJECT_ID", "")
        self.model_id = os.getenv("WATSONX_MODEL", "ibm/granite-13b-instruct-v2")
        self._model = None

    def _get_model(self):
        if self._model is not None:
            return self._model
        if not Credentials or not Model:
            raise RuntimeError("ibm-watsonx-ai not installed. Run: pip install ibm-watsonx-ai")
        if not self.api_key or not self.project_id:
            raise RuntimeError("Missing WATSONX_APIKEY or WATSONX_PROJECT_ID in environment.")
        credentials = Credentials(api_key=self.api_key, url=self.url)
        params = {
            "decoding_method": "greedy",
            "max_new_tokens": 300,
            "min_new_tokens": 1,
            "temperature": 0.2,
        }
        self._model = Model(
            model_id=self.model_id,
            params=params,
            credentials=credentials,
            project_id=self.project_id,
        )
        return self._model

    def summarize_note_to_json(self, note_text: str) -> Dict[str, Any]:
        """
        Ask Granite to output strict JSON with chief_complaint, history, assessment, plan.
        Returns a Python dict parsed from the model output. Falls back gracefully if parsing fails.
        """
        prompt = (
            "You are a clinical assistant. Read the clinical note and produce a concise summary.\n"
            "Return strict JSON with keys: chief_complaint, history, assessment, plan.\n"
            "Do not include any extra text or code fencing.\n\n"
            f"Clinical note:\n{note_text}\n\n"
            "JSON:"
        )

        model = self._get_model()
        result = model.generate(prompt=prompt)
        # The SDK typically returns a dict with 'results' -> [{'generated_text': '...'}]
        if isinstance(result, dict):
            try:
                candidates = result.get("results") or []
                if candidates:
                    text = candidates[0].get("generated_text", "").strip()
                else:
                    text = ""
            except Exception:
                text = ""
        else:
            # Fallback if SDK returns raw text
            text = str(result)

        try:
            parsed = json.loads(text)
            # Basic shape guard
            for k in ["chief_complaint", "history", "assessment", "plan"]:
                parsed.setdefault(k, None)
            return parsed
        except Exception:
            # Graceful fallback to a simple summary string placed in 'history'
            return {
                "chief_complaint": None,
                "history": text or "Summary unavailable",
                "assessment": None,
                "plan": None,
            }


