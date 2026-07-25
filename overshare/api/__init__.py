"""HTTP API for the scanner.

Implements API_CONTRACT.md at the repo root, which is the shared source of truth
with the frontend in web/. Change the contract first, then this.

Optional: the CLI is the primary distribution channel and stays dependency-light,
so FastAPI and uvicorn live behind the `api` extra.
"""

from .app import create_app

__all__ = ["create_app"]
