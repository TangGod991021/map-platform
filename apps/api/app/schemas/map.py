from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------- 分类 ----------------
class CategoryBase(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=32)
    color: str = "#00e5ff"
    icon: str = ""
    sort: int = 0
    status: str = "0"


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    color: str | None = None
    icon: str | None = None
    sort: int | None = None
    status: str | None = None


class CategoryOut(CategoryBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------------- 标签 ----------------
class LabelBase(BaseModel):
    category_id: int | None = None
    name: str = Field(min_length=1, max_length=64)
    subtitle: str = ""
    lng: float
    lat: float
    address: str = ""
    summary: str = ""
    description: str = ""
    cover_image: str = ""
    images: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    phone: str = ""
    business_hours: str = ""
    sort: int = 0
    status: str = "0"


class LabelCreate(LabelBase):
    pass


class LabelUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    subtitle: str | None = None
    lng: float | None = None
    lat: float | None = None
    address: str | None = None
    summary: str | None = None
    description: str | None = None
    cover_image: str | None = None
    images: list[str] | None = None
    tags: list[str] | None = None
    phone: str | None = None
    business_hours: str | None = None
    sort: int | None = None
    status: str | None = None


class LabelOut(LabelBase):
    id: int
    category_code: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------- 路线 / 区域 ----------------
class RouteBase(BaseModel):
    name: str
    color: str = "#00e5ff"
    weight: int = 4
    description: str = ""
    points: list[list[float]] = Field(default_factory=list)
    sort: int = 0
    status: str = "0"


class RouteCreate(RouteBase):
    pass


class RouteUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    weight: int | None = None
    description: str | None = None
    points: list[list[float]] | None = None
    sort: int | None = None
    status: str | None = None


class RouteOut(RouteBase):
    id: int


class AreaBase(BaseModel):
    name: str
    color: str = "#8b5cf6"
    description: str = ""
    polygon: list[list[float]] = Field(default_factory=list)
    sort: int = 0
    status: str = "0"


class AreaCreate(AreaBase):
    pass


class AreaUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    description: str | None = None
    polygon: list[list[float]] | None = None
    sort: int | None = None
    status: str | None = None


class AreaOut(AreaBase):
    id: int


# ---------------- 发布 ----------------
class PublishRequest(BaseModel):
    note: str = ""


class ReleaseOut(BaseModel):
    id: int
    version: int
    note: str
    snapshot_path: str
    created_by: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BootstrapResponse(BaseModel):
    version: int
    generated_at: str | None = None
    categories: list[dict]
    pois: list[dict]
    routes: list[dict]
    areas: list[dict]
