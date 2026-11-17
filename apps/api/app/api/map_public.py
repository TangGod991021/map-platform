from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import map_service

router = APIRouter(tags=["public"])


@router.get("/bootstrap", summary="地图 H5 启动数据")
async def bootstrap(db: AsyncSession = Depends(get_db)):
    """与地图 H5 的 pois.json 结构兼容，直接返回原始 JSON。"""
    return await map_service.build_public_data(db)


@router.get("/manifest", summary="地图数据版本清单")
async def manifest(db: AsyncSession = Depends(get_db)):
    data = await map_service.build_public_data(db)
    return {
        "version": data["version"],
        "generated_at": data["generated_at"],
        "categories": len(data["categories"]),
        "pois": len(data["pois"]),
        "routes": len(data["routes"]),
        "areas": len(data["areas"]),
    }


@router.get("/labels", summary="按条件获取已发布标签")
async def labels(
    bbox: str | None = Query(default=None, description="minLng,minLat,maxLng,maxLat"),
    category: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page_no: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    data = await map_service.build_public_data(db)
    items = data["pois"]

    if category:
        items = [item for item in items if item.get("category") == category]
    if keyword:
        text = keyword.strip()
        items = [
            item
            for item in items
            if text in (item.get("name") or "") or text in (item.get("desc") or "")
        ]
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = [float(v) for v in bbox.split(",")]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="bbox 格式应为 minLng,minLat,maxLng,maxLat") from exc
        items = [
            item
            for item in items
            if min_lng <= item["lng"] <= max_lng and min_lat <= item["lat"] <= max_lat
        ]

    total = len(items)
    start = (page_no - 1) * page_size
    return {
        "version": data["version"],
        "total": total,
        "pois": items[start : start + page_size],
    }


@router.get("/labels/{label_id}", summary="标签详情")
async def label_detail(label_id: int, db: AsyncSession = Depends(get_db)):
    detail = await map_service.get_label_detail(db, label_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    label = await map_service.get_label(db, label_id)
    if label is None or label.status != "1":
        raise HTTPException(status_code=404, detail="标签未发布")
    return detail
