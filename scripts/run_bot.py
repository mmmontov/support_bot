"""Run Telegram bot (long polling)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from support_bot.bot.main import run_bot


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
