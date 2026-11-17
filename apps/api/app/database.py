from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


class Base(DeclarativeBase):
    pass


_engine_options: dict = {"echo": False, "future": True}
if settings.app_env == "test":
    # 测试中每个用例可能使用独立事件循环，NullPool 避免连接跨循环复用
    _engine_options["poolclass"] = NullPool

engine = create_async_engine(settings.database_url, **_engine_options)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
