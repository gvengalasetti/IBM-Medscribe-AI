import os

try:
    from ibm_watsonx_ai import APIClient  # type: ignore
except Exception:  # pragma: no cover
    APIClient = None  # type: ignore


def _get_api_client():
    if APIClient is None:
        raise RuntimeError("ibm-watsonx-ai not installed. pip install ibm-watsonx-ai")
    api_key = os.getenv("WATSONX_APIKEY", "")
    url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    project_id = os.getenv("WATSONX_PROJECT_ID", "")
    if not api_key or not project_id:
        raise RuntimeError("Missing WATSONX_APIKEY or WATSONX_PROJECT_ID in environment")
    creds = {"url": url, "apikey": api_key}
    return APIClient(credentials=creds, project_id=project_id)

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import Model

def _get_wx_model():
    api_key = os.getenv("WATSONX_APIKEY", "")
    url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    project_id = os.getenv("WATSONX_PROJECT_ID", "")
    model_id = os.getenv("WATSONX_MODEL", "ibm/granite-13b-chat-v2")
    if not api_key or not project_id:
        raise RuntimeError("Missing WATSONX_APIKEY or WATSONX_PROJECT_ID")

    credentials = Credentials(api_key=api_key, url=url)
    params = {
        "decoding_method": "greedy",
        "max_new_tokens": 256,
        "temperature": 0.7,
        "repetition_penalty": 1.05,
    }
    return Model(model_id=model_id, params=params, credentials=credentials, project_id=project_id)

def watsonx_chat_agent(prompt: str) -> str:
    model = _get_wx_model()
    result = model.generate(prompt=prompt)
    if isinstance(result, dict):
        items = result.get("results") or []
        return (items[0].get("generated_text", "") if items else "").strip()
    return str(result).strip()


def terminal_input_tool(prompt_message: str = "You: ") -> str:
    """
    Tool: read one line of user input from the terminal and return it.
    """
    return input(prompt_message)


def run_agent_once_from_terminal(prompt_message: str = "You: ") -> str:
    """
    Read input via terminal_input_tool and pass it to the chat agent.
    Returns the agent's reply (empty string if user typed exit/quit).
    """
    user_text = terminal_input_tool(prompt_message)
    if user_text.strip().lower() in {"exit", "quit"}:
        return ""
    return watsonx_chat_agent(user_text)


if __name__ == "__main__":
    print("watsonx AI Agent — type 'exit' to quit.")
    try:
        while True:
            prompt = terminal_input_tool("You: ")
            if prompt.strip().lower() in {"exit", "quit"}:
                break
            try:
                reply = watsonx_chat_agent(prompt)
            except Exception as e:
                reply = f"[error] {e}"
            print(f"Agent: {reply}\n")
    except KeyboardInterrupt:
        pass


