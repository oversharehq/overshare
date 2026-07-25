"""Run the API: python -m leakscan.api"""

from __future__ import annotations

import os

import uvicorn

from .app import create_app


def main() -> None:
    uvicorn.run(
        create_app(),
        host=os.environ.get("LEAKSCAN_HOST", "127.0.0.1"),
        port=int(os.environ.get("LEAKSCAN_PORT", "8000")),
        log_level=os.environ.get("LEAKSCAN_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
