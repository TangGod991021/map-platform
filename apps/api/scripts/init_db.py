"""执行数据库迁移并写入种子数据。

用法：python scripts/init_db.py
等价于 `alembic upgrade head` + 种子数据。
"""

import asyncio
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.seed import seed_data  # noqa: E402


def run_migrations() -> None:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    command.upgrade(config, "head")


async def seed() -> None:
    async with SessionLocal() as db:
        await seed_data(db)


def main() -> None:
    run_migrations()
    asyncio.run(seed())
    print("数据库初始化完成，默认管理员：admin / admin123")


if __name__ == "__main__":
    main()
