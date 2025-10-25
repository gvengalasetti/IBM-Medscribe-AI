import os
import asyncio
from mcp.server.fastmcp import FastMCP

from .agent import watsonx_chat_agent
from .crewai_summarizer import crewai_summarize

try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore
    find_dotenv = None  # type: ignore


mcp = FastMCP("watsonx-demo-server")


@mcp.tool()
def add_numbers(a: int, b: int) -> dict:
    """Add two integers and return structured output."""
    return {"sum": a + b, "a": a, "b": b}


@mcp.tool()
def say_hello(name: str) -> dict:
    """Return a greeting."""
    return {"greeting": f"Hello, {name}!"}


@mcp.tool()
def agent_chat(prompt: str) -> dict:
    """Send a prompt to the watsonx agent and return its reply."""
    reply = watsonx_chat_agent(prompt)
    return {"reply": reply}


@mcp.tool()
def summarize_with_crewai(text: str, style: str = "", model: str = "") -> dict:
    """Summarize text using CrewAI agent configured for IBM watsonx.

    Optional args: style (guidance), model (override WATSONX_MODEL)
    """
    try:
        style_opt = style or None
        model_opt = model or None
        summary = crewai_summarize(text, style=style_opt, model=model_opt)
        return {"summary": summary}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def cure_for_fear_of_pineapples(name: str) -> dict:
    """return a cure for the fear of pineapples"""
    return {"cure": "eat pineapples"}


async def main():
    # Serve on stdio (easy for local testing) OR switch transport for production.
    # The SDK supports multiple transports; here we use stdio for simplicity.
    # Load .env so watsonx credentials are present
    if load_dotenv and find_dotenv:
        env_path = find_dotenv(usecwd=True)
        if env_path:
            load_dotenv(env_path)
    print("Starting MCP server (stdio).")
    await mcp.serve_stdio()


if __name__ == "__main__":
    asyncio.run(main())


