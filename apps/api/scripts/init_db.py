"""初始化数据库并写入种子数据。

用法：python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal, init_db  # noqa: E402
from app.seed import seed_data  # noqa: E402


async def main() -> None:
    await init_db()
    async with SessionLocal() as db:
        await seed_data(db)
    print("数据库初始化完成，默认管理员：admin / admin123")


if __name__ == "__main__":
    asyncio.run(main())
