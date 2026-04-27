from __future__ import annotations

import asyncio
import sys

from dotenv import load_dotenv


async def _amain() -> int:
    load_dotenv(override=True)

    from .agent import run_digest
    from .format import format_digest
    from .reddit import RedditClient

    async with RedditClient() as client:
        digest = await run_digest(client)
    sys.stdout.write(format_digest(digest))
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_amain()))


if __name__ == "__main__":
    main()
