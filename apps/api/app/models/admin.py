from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SysUser(Base):
    __tablename__ = "sys_user"
    __table_args__ = {"comment": "系统用户"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="登录账号")
    password_hash: Mapped[str] = mapped_column(String(255), comment="bcrypt 密码哈希")
    nickname: Mapped[str] = mapped_column(String(64), default="", comment="昵称")
    role: Mapped[str] = mapped_column(String(32), default="admin", comment="角色：admin/editor")
    permissions: Mapped[str] = mapped_column(Text, default='["*:*:*"]', comment="权限 JSON 数组")
    status: Mapped[str] = mapped_column(String(1), default="0", comment="0 正常 1 停用")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
