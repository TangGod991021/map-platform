from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, parse_permissions
from app.database import get_db
from app.models.admin import SysUser

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> SysUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未登录，请先完成登录",
        )

    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录",
        ) from exc

    user = await db.scalar(select(SysUser).where(SysUser.username == payload.get("sub")))
    if user is None or user.status != "0":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已停用",
        )
    return user


def user_permissions(user: SysUser) -> list[str]:
    permissions = parse_permissions(user.permissions)
    return permissions or []


def require_permission(permission: str):
    """依赖工厂：要求当前用户拥有 `模块:实体:操作` 权限，`*:*:*` 视为超级权限。"""

    async def checker(user: SysUser = Depends(get_current_user)) -> SysUser:
        permissions = user_permissions(user)
        if "*:*:*" in permissions or permission in permissions:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有操作权限")

    return checker
