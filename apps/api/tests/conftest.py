"""测试夹具：独立临时数据库 + 临时发布目录，不触碰开发数据。"""

import asyncio
import os
import sys
import tempfile
import uuid
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


@pytest.fixture()
async def limited_auth(client) -> dict:
    """只有 map:label:list 权限的编辑账号。"""
    from app.core.security import hash_password
    from app.database import SessionLocal
    from app.models.admin import SysUser

    username = f"editor_{uuid.uuid4().hex[:8]}"
    async with SessionLocal() as db:
        db.add(
            SysUser(
                username=username,
                password_hash=hash_password("editor123"),
                nickname="编辑",
                role="editor",
                permissions='["map:label:list"]',
                status="0",
            )
        )
        await db.commit()

    resp = await client.post(
        "/prod-api/login", json={"username": username, "password": "editor123"}
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}
