"""贵州省界空间校验。

启动后首次调用时加载省界 GeoJSON（默认取地图 H5 的 ``guizhou.json``），
用 Shapely 预处理几何做点面判断；边界文件缺失时自动回退到外接矩形，
保证服务仍可启动。
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.prepared import PreparedGeometry, prep

from app.config import settings

logger = logging.getLogger(__name__)

# 贵州粗略外接矩形：用于边界文件加载失败时的兜底
GUZHOU_BBOX = (103.3, 24.3, 109.9, 29.5)


@lru_cache(maxsize=1)
def _province_geometry() -> PreparedGeometry | None:
    path = Path(settings.geo_boundary_path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        features = data.get("features") or []
        if not features:
            raise ValueError("FeatureCollection 为空")
        return prep(shape(features[0]["geometry"]))
    except Exception as exc:  # noqa: BLE001 - 兜底后继续服务
        logger.warning("贵州边界加载失败，回退到外接矩形校验：%s", exc)
        return None


def is_in_guizhou(lng: float, lat: float) -> bool:
    """判断坐标是否落在贵州省界内（含边界线）。"""
    geometry = _province_geometry()
    if geometry is None:
        min_lng, min_lat, max_lng, max_lat = GUZHOU_BBOX
        return min_lng <= lng <= max_lng and min_lat <= lat <= max_lat
    return bool(geometry.covers(Point(lng, lat)))
