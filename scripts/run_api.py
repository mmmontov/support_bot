"""Run FastAPI with uvicorn (dev)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import uvicorn

from support_bot.config import get_settings


def main() -> None:
    s = get_settings()
    uvicorn.run(
        "support_bot.api.main:app",
        host=s.api_host,
        port=s.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
