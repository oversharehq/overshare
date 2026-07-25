"""Run the API: python -m overshare.api"""

from __future__ import annotations

import os

import uvicorn

from .app import create_app


def main() -> None:
    uvicorn.run(
        create_app(),
        host=os.environ.get("OVERSHARE_HOST", "127.0.0.1"),
        port=int(os.environ.get("OVERSHARE_PORT", "8000")),
        log_level=os.environ.get("OVERSHARE_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
