# syntax=docker/dockerfile:1

# Use uv's official image to get a fast, reproducible dependency install.
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Install dependencies first (cached layer) using the lockfile for reproducibility.
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy the application code and install the project itself.
COPY app ./app
RUN uv sync --frozen --no-dev

# Container Apps sends traffic to this port.
ENV PORT=8000
EXPOSE 8000

# uv run executes inside the project's virtualenv.
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
