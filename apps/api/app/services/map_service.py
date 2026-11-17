import json
import re
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.map import MapArea, MapCategory, MapLabel, MapRelease, MapRoute
from app.schemas.map import (
    AreaCreate,
    AreaUpdate,
    CategoryCreate,
    CategoryUpdate,
    LabelCreate,
    LabelUpdate,
    RouteCreate,
    RouteUpdate,
)

# 贵州粗略外接矩形；后续可替换为省界多边形精确校验
GUZHOU_BBOX = (103.3, 24.3, 109.9, 29.5)


def parse_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def dump_list(value: list | None) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def strip_html(value: str | None) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()


def validate_coordinate(lng: float, lat: float) -> None:
    min_lng, min_lat, max_lng, max_lat = GUZHOU_BBOX
    if not (min_lng <= lng <= max_lng and min_lat <= lat <= max_lat):
        raise ValueError("坐标不在贵州省范围内")


def validate_points(points: list[list[float]], minimum: int, label: str) -> None:
    if len(points) < minimum:
        raise ValueError(f"{label}至少需要 {minimum} 个顶点")


def category_to_dict(category: MapCategory) -> dict:
    return {
        "id": category.id,
        "code": category.code,
        "key": category.code,
        "name": category.name,
        "color": category.color,
        "icon": category.icon,
        "sort": category.sort,
        "status": category.status,
        "created_at": category.created_at.isoformat() if category.created_at else None,
        "updated_at": category.updated_at.isoformat() if category.updated_at else None,
    }


def label_to_dict(label: MapLabel, category_code: str | None = None) -> dict:
    return {
        "id": label.id,
        "category_id": label.category_id,
        "category_code": category_code,
        "category": category_code,
        "name": label.name,
        "subtitle": label.subtitle,
        "lng": label.lng,
        "lat": label.lat,
        "address": label.address,
        "summary": label.summary,
        "description": label.description,
        "cover_image": label.cover_image,
        "images": parse_list(label.images),
        "tags": parse_list(label.tags),
        "phone": label.phone,
        "business_hours": label.business_hours,
        "sort": label.sort,
        "status": label.status,
        "created_at": label.created_at.isoformat() if label.created_at else None,
        "updated_at": label.updated_at.isoformat() if label.updated_at else None,
    }


def route_to_dict(route: MapRoute) -> dict:
    return {
        "id": route.id,
        "name": route.name,
        "color": route.color,
        "weight": route.weight,
        "description": route.description,
        "points": parse_list(route.points),
        "sort": route.sort,
        "status": route.status,
    }


def area_to_dict(area: MapArea) -> dict:
    return {
        "id": area.id,
        "name": area.name,
        "color": area.color,
        "description": area.description,
        "polygon": parse_list(area.polygon),
        "sort": area.sort,
        "status": area.status,
    }


# ---------------- 分类 ----------------
async def list_categories(db: AsyncSession) -> list[dict]:
    rows = (
        await db.scalars(select(MapCategory).order_by(MapCategory.sort, MapCategory.id))
    ).all()
    return [category_to_dict(row) for row in rows]


async def get_category(db: AsyncSession, category_id: int) -> MapCategory | None:
    return await db.get(MapCategory, category_id)


async def create_category(db: AsyncSession, payload: CategoryCreate) -> MapCategory:
    exists = await db.scalar(select(MapCategory).where(MapCategory.code == payload.code))
    if exists:
        raise ValueError("分类编码已存在")
    category = MapCategory(**payload.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update_category(
    db: AsyncSession, category_id: int, payload: CategoryUpdate
) -> MapCategory:
    category = await db.get(MapCategory, category_id)
    if category is None:
        raise LookupError("分类不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(db: AsyncSession, category_id: int) -> None:
    category = await db.get(MapCategory, category_id)
    if category is None:
        raise LookupError("分类不存在")
    count = await db.scalar(
        select(func.count()).select_from(MapLabel).where(MapLabel.category_id == category_id)
    )
    if count:
        raise ValueError("分类下存在标签，无法删除")
    await db.delete(category)
    await db.commit()


# ---------------- 标签 ----------------
async def list_labels(
    db: AsyncSession,
    category_id: int | None = None,
    status: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    page = max(1, page)
    page_size = max(1, min(page_size, 200))

    conditions = []
    if category_id is not None:
        conditions.append(MapLabel.category_id == category_id)
    if status:
        conditions.append(MapLabel.status == status)
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                MapLabel.name.like(like),
                MapLabel.address.like(like),
                MapLabel.summary.like(like),
            )
        )

    count_query = select(func.count()).select_from(MapLabel)
    query = select(MapLabel)
    for condition in conditions:
        count_query = count_query.where(condition)
        query = query.where(condition)

    total = await db.scalar(count_query) or 0
    query = (
        query.order_by(MapLabel.sort, MapLabel.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    labels = (await db.scalars(query)).all()

    category_ids = {label.category_id for label in labels if label.category_id}
    categories = {}
    if category_ids:
        rows = (
            await db.scalars(select(MapCategory).where(MapCategory.id.in_(category_ids)))
        ).all()
        categories = {row.id: row.code for row in rows}

    return [label_to_dict(label, categories.get(label.category_id)) for label in labels], total


async def get_label(db: AsyncSession, label_id: int) -> MapLabel | None:
    return await db.get(MapLabel, label_id)


async def get_label_detail(db: AsyncSession, label_id: int) -> dict | None:
    label = await db.get(MapLabel, label_id)
    if label is None:
        return None
    category = await db.get(MapCategory, label.category_id) if label.category_id else None
    return label_to_dict(label, category.code if category else None)


async def create_label(db: AsyncSession, payload: LabelCreate) -> MapLabel:
    validate_coordinate(payload.lng, payload.lat)
    if payload.category_id is not None:
        category = await db.get(MapCategory, payload.category_id)
        if category is None:
            raise ValueError("分类不存在")
    data = payload.model_dump()
    data["images"] = dump_list(data.get("images"))
    data["tags"] = dump_list(data.get("tags"))
    label = MapLabel(**data)
    db.add(label)
    await db.commit()
    await db.refresh(label)
    return label


async def update_label(db: AsyncSession, label_id: int, payload: LabelUpdate) -> MapLabel:
    label = await db.get(MapLabel, label_id)
    if label is None:
        raise LookupError("标签不存在")

    data = payload.model_dump(exclude_unset=True)
    if "lng" in data or "lat" in data:
        validate_coordinate(
            float(data.get("lng", label.lng)), float(data.get("lat", label.lat))
        )
    if data.get("category_id") is not None:
        category = await db.get(MapCategory, data["category_id"])
        if category is None:
            raise ValueError("分类不存在")
    if "images" in data:
        data["images"] = dump_list(data["images"])
    if "tags" in data:
        data["tags"] = dump_list(data["tags"])

    for key, value in data.items():
        setattr(label, key, value)
    await db.commit()
    await db.refresh(label)
    return label


async def delete_label(db: AsyncSession, label_id: int) -> None:
    label = await db.get(MapLabel, label_id)
    if label is None:
        raise LookupError("标签不存在")
    await db.delete(label)
    await db.commit()


# ---------------- 路线 / 区域 ----------------
async def list_routes(db: AsyncSession) -> list[dict]:
    rows = (await db.scalars(select(MapRoute).order_by(MapRoute.sort, MapRoute.id))).all()
    return [route_to_dict(row) for row in rows]


async def create_route(db: AsyncSession, payload: RouteCreate) -> MapRoute:
    validate_points(payload.points, 2, "路线")
    data = payload.model_dump()
    data["points"] = dump_list(data["points"])
    route = MapRoute(**data)
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return route


async def update_route(db: AsyncSession, route_id: int, payload: RouteUpdate) -> MapRoute:
    route = await db.get(MapRoute, route_id)
    if route is None:
        raise LookupError("路线不存在")
    data = payload.model_dump(exclude_unset=True)
    if "points" in data:
        validate_points(data["points"], 2, "路线")
        data["points"] = dump_list(data["points"])
    for key, value in data.items():
        setattr(route, key, value)
    await db.commit()
    await db.refresh(route)
    return route


async def delete_route(db: AsyncSession, route_id: int) -> None:
    route = await db.get(MapRoute, route_id)
    if route is None:
        raise LookupError("路线不存在")
    await db.delete(route)
    await db.commit()


async def list_areas(db: AsyncSession) -> list[dict]:
    rows = (await db.scalars(select(MapArea).order_by(MapArea.sort, MapArea.id))).all()
    return [area_to_dict(row) for row in rows]


async def create_area(db: AsyncSession, payload: AreaCreate) -> MapArea:
    validate_points(payload.polygon, 3, "区域")
    data = payload.model_dump()
    data["polygon"] = dump_list(data["polygon"])
    area = MapArea(**data)
    db.add(area)
    await db.commit()
    await db.refresh(area)
    return area


async def update_area(db: AsyncSession, area_id: int, payload: AreaUpdate) -> MapArea:
    area = await db.get(MapArea, area_id)
    if area is None:
        raise LookupError("区域不存在")
    data = payload.model_dump(exclude_unset=True)
    if "polygon" in data:
        validate_points(data["polygon"], 3, "区域")
        data["polygon"] = dump_list(data["polygon"])
    for key, value in data.items():
        setattr(area, key, value)
    await db.commit()
    await db.refresh(area)
    return area


async def delete_area(db: AsyncSession, area_id: int) -> None:
    area = await db.get(MapArea, area_id)
    if area is None:
        raise LookupError("区域不存在")
    await db.delete(area)
    await db.commit()


# ---------------- 公开数据 ----------------
async def build_public_data(db: AsyncSession) -> dict:
    categories = (
        await db.scalars(
            select(MapCategory)
            .where(MapCategory.status == "0")
            .order_by(MapCategory.sort, MapCategory.id)
        )
    ).all()
    labels = (
        await db.scalars(
            select(MapLabel)
            .where(MapLabel.status == "1")
            .order_by(MapLabel.sort, MapLabel.id)
        )
    ).all()
    routes = (
        await db.scalars(
            select(MapRoute).where(MapRoute.status == "0").order_by(MapRoute.sort, MapRoute.id)
        )
    ).all()
    areas = (
        await db.scalars(
            select(MapArea).where(MapArea.status == "0").order_by(MapArea.sort, MapArea.id)
        )
    ).all()

    category_code = {category.id: category.code for category in categories}
    version = await db.scalar(select(func.max(MapRelease.version))) or 0

    return {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "categories": [category_to_dict(category) for category in categories],
        "pois": [
            {
                "id": label.id,
                "name": label.name,
                "category": category_code.get(label.category_id, ""),
                "lng": label.lng,
                "lat": label.lat,
                "address": label.address,
                "desc": label.summary or strip_html(label.description)[:160],
                "cover": label.cover_image,
                "images": parse_list(label.images),
                "tags": parse_list(label.tags),
            }
            for label in labels
        ],
        "routes": [
            {
                "name": route.name,
                "color": route.color,
                "weight": route.weight,
                "description": route.description,
                "points": parse_list(route.points),
            }
            for route in routes
        ],
        "areas": [
            {
                "name": area.name,
                "color": area.color,
                "description": area.description,
                "polygon": parse_list(area.polygon),
            }
            for area in areas
        ],
    }
