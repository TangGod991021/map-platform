"""测试夹具：独立临时数据库 + 临时发布目录，不触碰开发数据。"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

_TMP_DIR = Path(tempfile.mkdtemp(prefix="map_api_tests_"))
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_TMP_DIR / 'test.db').as_posix()}"
os.environ["MAP_PUBLISH_DIR"] = str(_TMP_DIR / "publish")


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    """用 Alembic 迁移建表，顺带验证迁移脚本可用。"""
    from alembic.config import Config

    from alembic import command

    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    command.upgrade(config, "head")
    yield


@pytest.fixture(scope="session", autouse=True)
def seeded_db(migrated_db):
    from app.database import SessionLocal
    from app.seed import seed_data

    async def run() -> None:
        async with SessionLocal() as db:
            await seed_data(db)

    asyncio.run(run())
    yield


@pytest.fixture()
async def client():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture()
async def token(client) -> str:
    resp = await client.post(
        "/prod-api/login", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


@pytest.fixture()
def auth(token) -> dict:
    return {"Authorization": f"Bearer {token}"}
