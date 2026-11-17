"""生成地图静态快照。

用法：python scripts/publish_snapshot.py "发布说明"
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.services.publish_service import publish_snapshot  # noqa: E402


async def main() -> None:
    note = sys.argv[1] if len(sys.argv) > 1 else "CLI 发布"
    async with SessionLocal() as db:
        result = await publish_snapshot(db, note, "cli")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
