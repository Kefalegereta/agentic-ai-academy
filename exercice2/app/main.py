"""FastAPI application.

Single GET endpoint that matches the brief's HTTP contract:

    GET /?query=...   ->   {"answer": "..."}

Swagger UI (browsable API docs) is served automatically by FastAPI at /docs.

The KB is loaded once at startup and the Answerer is built once, so each request
just runs one LLM call. Nothing here is Azure-specific: this same file runs
unchanged locally, in Container Apps, and on AWS.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import load_settings
from .kb import load_kb
from .llm import Answerer

# Populated at startup (see lifespan below).
state: dict[str, Answerer] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    knowledge_base = load_kb(settings)  # read the KB from Blob once
    state["answerer"] = Answerer(settings, knowledge_base)
    yield
    state.clear()


app = FastAPI(
    title="Dataroots QnA Bot (Azure)",
    description=(
        "Answers questions about Dataroots, grounded strictly in a knowledge "
        "base stored in Azure Blob Storage, using Azure OpenAI. If the answer "
        "isn't in the knowledge base, it returns a fixed fallback instead of "
        "guessing."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", summary="Answer a question")
def answer(query: str = "") -> dict[str, str]:
    """Return a JSON object with a single `answer` field for the given `query`."""
    return {"answer": state["answerer"].answer(query)}


@app.get("/health", summary="Liveness probe", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}
