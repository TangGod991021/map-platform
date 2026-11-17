from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, parse_permissions, verify_password
from app.models.admin import SysUser


async def get_user_by_username(db: AsyncSession, username: str) -> SysUser | None:
    return await db.scalar(select(SysUser).where(SysUser.username == username))


async def authenticate(db: AsyncSession, username: str, password: str) -> SysUser | None:
    user = await get_user_by_username(db, username)
    if user is None or user.status != "0":
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def build_token(user: SysUser) -> dict:
    return {
        "access_token": create_access_token(user.username, user.id),
        "token_type": "bearer",
    }


def user_info(user: SysUser) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname or user.username,
        "roles": [user.role or "admin"],
        "permissions": parse_permissions(user.permissions) or ["*:*:*"],
    }


async def seed_admin(db: AsyncSession) -> None:
    exists = await db.scalar(select(SysUser).where(SysUser.username == "admin"))
    if exists:
        return
    db.add(
        SysUser(
            username="admin",
            password_hash=hash_password("admin123"),
            nickname="系统管理员",
            role="admin",
            permissions='["*:*:*"]',
            status="0",
        )
    )
    await db.commit()
