"""Configuration, read entirely from environment variables.

Everything the app needs to talk to Azure comes from env vars. That keeps the
code portable: the same image runs locally (env from a .env file), in Azure
Container Apps (env from container secrets), and on AWS later (env from task
definition / Secrets Manager) with no code changes.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load a local .env if present. No-op in the container (no .env shipped there),
# where env vars come from container secrets instead.
load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and fill it in (local), or set it as a "
            f"container secret (Azure/AWS)."
        )
    return value


@dataclass(frozen=True)
class Settings:
    # --- Azure OpenAI ---
    openai_endpoint: str
    openai_api_key: str
    openai_deployment: str
    openai_api_version: str

    # --- Azure Blob Storage (the knowledge base) ---
    storage_account: str
    storage_container: str
    storage_key: str


def load_settings() -> Settings:
    return Settings(
        openai_endpoint=_require("AZURE_OPENAI_ENDPOINT"),
        openai_api_key=_require("AZURE_OPENAI_API_KEY"),
        openai_deployment=_require("AZURE_OPENAI_DEPLOYMENT"),
        # API version is stable across Azure OpenAI; override via env if needed.
        openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        storage_account=_require("AZURE_STORAGE_ACCOUNT"),
        storage_container=_require("AZURE_STORAGE_CONTAINER"),
        storage_key=_require("AZURE_STORAGE_KEY"),
    )
