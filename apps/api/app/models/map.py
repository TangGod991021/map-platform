from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MapCategory(Base):
    __tablename__ = "map_category"
    __table_args__ = {"comment": "地图分类"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, comment="分类编码")
    name: Mapped[str] = mapped_column(String(32), comment="分类名称")
    color: Mapped[str] = mapped_column(String(16), default="#00e5ff", comment="颜色")
    icon: Mapped[str] = mapped_column(String(255), default="", comment="图标 URL")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[str] = mapped_column(String(1), default="0", comment="0 启用 1 停用")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class MapLabel(Base):
    __tablename__ = "map_label"
    __table_args__ = {"comment": "地图标签/点位"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("map_category.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(64), index=True, comment="名称")
    subtitle: Mapped[str] = mapped_column(String(128), default="", comment="副标题")
    lng: Mapped[float] = mapped_column(Float, comment="经度 WGS84")
    lat: Mapped[float] = mapped_column(Float, comment="纬度 WGS84")
    address: Mapped[str] = mapped_column(String(255), default="", comment="地址")
    summary: Mapped[str] = mapped_column(String(500), default="", comment="摘要")
    description: Mapped[str] = mapped_column(Text, default="", comment="详情正文")
    cover_image: Mapped[str] = mapped_column(String(500), default="", comment="封面")
    images: Mapped[str] = mapped_column(Text, default="[]", comment="图片 JSON 数组")
    tags: Mapped[str] = mapped_column(Text, default="[]", comment="标签 JSON 数组")
    phone: Mapped[str] = mapped_column(String(64), default="", comment="电话")
    business_hours: Mapped[str] = mapped_column(String(128), default="", comment="营业时间")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[str] = mapped_column(
        String(1), default="0", index=True, comment="0 草稿 1 已发布 2 已下线"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class MapRoute(Base):
    __tablename__ = "map_route"
    __table_args__ = {"comment": "地图路线"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), comment="路线名称")
    color: Mapped[str] = mapped_column(String(16), default="#00e5ff")
    weight: Mapped[int] = mapped_column(Integer, default=4)
    description: Mapped[str] = mapped_column(String(500), default="")
    points: Mapped[str] = mapped_column(Text, default="[]", comment="[[lng,lat],...] JSON")
    sort: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(1), default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class MapArea(Base):
    __tablename__ = "map_area"
    __table_args__ = {"comment": "地图区域"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), comment="区域名称")
    color: Mapped[str] = mapped_column(String(16), default="#8b5cf6")
    description: Mapped[str] = mapped_column(String(500), default="")
    polygon: Mapped[str] = mapped_column(Text, default="[]", comment="[[lng,lat],...] JSON")
    sort: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(1), default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class MapRelease(Base):
    __tablename__ = "map_release"
    __table_args__ = {"comment": "地图数据发布版本"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    note: Mapped[str] = mapped_column(String(255), default="")
    snapshot_path: Mapped[str] = mapped_column(String(500), default="")
    created_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
