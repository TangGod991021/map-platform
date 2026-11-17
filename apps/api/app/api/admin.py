import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.response import ok, page
from app.database import get_db
from app.deps import get_current_user, user_permissions
from app.models.map import MapArea, MapCategory, MapLabel, MapRelease, MapRoute
from app.schemas.admin import LoginRequest
from app.schemas.map import (
    AreaCreate,
    AreaUpdate,
    CategoryCreate,
    CategoryUpdate,
    LabelCreate,
    LabelUpdate,
    PublishRequest,
    RouteCreate,
    RouteUpdate,
)
from app.services import auth_service, map_service, publish_service

router = APIRouter(tags=["admin"])


def _raise_service_error(exc: Exception) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------- 登录 / 信息 ----------------
@router.post("/login", summary="管理员登录")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=400, detail="账号或密码错误")
    return ok(auth_service.build_token(user), "登录成功")


@router.get("/getInfo", summary="当前用户信息")
async def get_info(user=Depends(get_current_user)):
    return ok(auth_service.user_info(user))


@router.get("/getRouters", summary="管理端菜单")
async def get_routers(user=Depends(get_current_user)):
    return ok(
        [
            {
                "name": "Dashboard",
                "path": "/dashboard",
                "meta": {"title": "首页", "icon": "Odometer"},
            },
            {
                "name": "MapAdmin",
                "path": "/map",
                "meta": {"title": "地图管理", "icon": "MapLocation"},
                "children": [
                    {
                        "name": "MapCategory",
                        "path": "/map/category",
                        "meta": {"title": "分类管理", "icon": "Files"},
                    },
                    {
                        "name": "MapLabel",
                        "path": "/map/label",
                        "meta": {"title": "标签管理", "icon": "Location"},
                    },
                    {
                        "name": "MapRoute",
                        "path": "/map/route",
                        "meta": {"title": "路线管理", "icon": "Guide"},
                    },
                    {
                        "name": "MapArea",
                        "path": "/map/area",
                        "meta": {"title": "区域管理", "icon": "Grid"},
                    },
                    {
                        "name": "MapRelease",
                        "path": "/map/release",
                        "meta": {"title": "发布管理", "icon": "Upload"},
                    },
                ],
            },
        ]
    )


# ---------------- 首页统计 ----------------
@router.get("/dashboard/summary", summary="首页统计")
async def dashboard_summary(
    user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    categories = await db.scalar(select(func.count()).select_from(MapCategory)) or 0
    labels = await db.scalar(select(func.count()).select_from(MapLabel)) or 0
    published = (
        await db.scalar(
            select(func.count()).select_from(MapLabel).where(MapLabel.status == "1")
        )
        or 0
    )
    routes = await db.scalar(select(func.count()).select_from(MapRoute)) or 0
    areas = await db.scalar(select(func.count()).select_from(MapArea)) or 0
    releases = await db.scalar(select(func.count()).select_from(MapRelease)) or 0
    return ok(
        {
            "categories": categories,
            "labels": labels,
            "published": published,
            "routes": routes,
            "areas": areas,
            "releases": releases,
            "permissions": user_permissions(user),
        }
    )


# ---------------- 分类 ----------------
@router.get("/map/category/list", summary="分类列表")
async def category_list(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return ok(await map_service.list_categories(db))


@router.post("/map/category", summary="新增分类")
async def category_create(
    payload: CategoryCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        category = await map_service.create_category(db, payload)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(map_service.category_to_dict(category), "新增成功")


@router.put("/map/category/{category_id}", summary="修改分类")
async def category_update(
    category_id: int,
    payload: CategoryUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        category = await map_service.update_category(db, category_id, payload)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(map_service.category_to_dict(category), "修改成功")


@router.delete("/map/category/{category_id}", summary="删除分类")
async def category_delete(
    category_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await map_service.delete_category(db, category_id)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(None, "删除成功")


# ---------------- 标签 ----------------
@router.get("/map/label/list", summary="标签分页列表")
async def label_list(
    category_id: int | None = None,
    status: str | None = None,
    keyword: str | None = None,
    page_no: int = 1,
    page_size: int = 20,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await map_service.list_labels(
        db,
        category_id=category_id,
        status=status,
        keyword=keyword,
        page=page_no,
        page_size=page_size,
    )
    return page(rows, total)


@router.get("/map/label/{label_id}", summary="标签详情")
async def label_detail(
    label_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    detail = await map_service.get_label_detail(db, label_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    return ok(detail)


@router.post("/map/label", summary="新增标签")
async def label_create(
    payload: LabelCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        label = await map_service.create_label(db, payload)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    detail = await map_service.get_label_detail(db, label.id)
    return ok(detail, "新增成功")


@router.put("/map/label/{label_id}", summary="修改标签")
async def label_update(
    label_id: int,
    payload: LabelUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await map_service.update_label(db, label_id, payload)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    detail = await map_service.get_label_detail(db, label_id)
    return ok(detail, "修改成功")


@router.put("/map/label/{label_id}/status", summary="标签上下架")
async def label_status(
    label_id: int,
    status: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if status not in {"0", "1", "2"}:
        raise HTTPException(status_code=400, detail="状态值不正确")
    try:
        await map_service.update_label(db, label_id, LabelUpdate(status=status))
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(None, "状态已更新")


@router.delete("/map/label/{label_id}", summary="删除标签")
async def label_delete(
    label_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await map_service.delete_label(db, label_id)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(None, "删除成功")


# ---------------- 路线 ----------------
@router.get("/map/route/list", summary="路线列表")
async def route_list(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return ok(await map_service.list_routes(db))


@router.post("/map/route", summary="新增路线")
async def route_create(
    payload: RouteCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        route = await map_service.create_route(db, payload)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(map_service.route_to_dict(route), "新增成功")


@router.put("/map/route/{route_id}", summary="修改路线")
async def route_update(
    route_id: int,
    payload: RouteUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        route = await map_service.update_route(db, route_id, payload)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(map_service.route_to_dict(route), "修改成功")


@router.delete("/map/route/{route_id}", summary="删除路线")
async def route_delete(
    route_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await map_service.delete_route(db, route_id)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(None, "删除成功")


# ---------------- 区域 ----------------
@router.get("/map/area/list", summary="区域列表")
async def area_list(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return ok(await map_service.list_areas(db))


@router.post("/map/area", summary="新增区域")
async def area_create(
    payload: AreaCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        area = await map_service.create_area(db, payload)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(map_service.area_to_dict(area), "新增成功")


@router.put("/map/area/{area_id}", summary="修改区域")
async def area_update(
    area_id: int,
    payload: AreaUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        area = await map_service.update_area(db, area_id, payload)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(map_service.area_to_dict(area), "修改成功")


@router.delete("/map/area/{area_id}", summary="删除区域")
async def area_delete(
    area_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await map_service.delete_area(db, area_id)
    except Exception as exc:  # noqa: BLE001
        _raise_service_error(exc)
    return ok(None, "删除成功")


# ---------------- 发布 ----------------
@router.post("/map/release/publish", summary="发布地图快照")
async def release_publish(
    payload: PublishRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await publish_service.publish_snapshot(db, payload.note, user.username)
    return ok(result, "发布成功")


@router.get("/map/release/list", summary="发布记录")
async def release_list(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return ok(await publish_service.list_releases(db))


# ---------------- 上传 ----------------
@router.post("/common/upload", summary="文件上传")
async def common_upload(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    allowed = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".mp4",
        ".webm",
        ".mp3",
        ".m4a",
    }
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过 20MB")

    name = f"{uuid.uuid4().hex}{suffix}"
    target = Path(settings.upload_dir) / name
    target.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(target, "wb") as handle:
        await handle.write(content)

    return ok({"url": f"/profile/{name}", "fileName": name}, "上传成功")
