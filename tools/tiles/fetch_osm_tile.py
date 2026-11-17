#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W1 技术验证：用 Playwright + Overpass API 抓取一个 500m 瓦片的 OSM 数据。

输出：
  tools/tiles/out/osm_tile_raw.json   Overpass 原始 JSON
  tools/tiles/out/osm_tile_stats.json 统计结果

用法：
  python tools/tiles/fetch_osm_tile.py
"""

import json
import os
import sys
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

# 甲秀楼附近 500m 瓦片（WGS-84）
LAT = 26.5686
LON = 106.7167
HALF_LAT = 250 / 111_000.0
HALF_LON = 250 / (111_000.0 * 0.894)  # cos(26.57°) ≈ 0.894

BBOX = (
    LAT - HALF_LAT,  # south
    LON - HALF_LON,  # west
    LAT + HALF_LAT,  # north
    LON + HALF_LON,  # east
)

QUERY = f"""
[out:json][timeout:120];
(
  way["building"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  way["highway"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  way["natural"="water"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  way["waterway"="riverbank"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  way["landuse"="reservoir"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
);
out geom;
""".strip()

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
RAW_PATH = os.path.join(OUT_DIR, "osm_tile_raw.json")
STATS_PATH = os.path.join(OUT_DIR, "osm_tile_stats.json")


def fetch(url: str) -> str:
    # 用 Playwright 的请求上下文抓取原始响应，避免浏览器 JSON 查看器改写正文
    with sync_playwright() as p:
        ctx = p.request.new_context()
        resp = ctx.get(url, timeout=180_000)
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}: {resp.text()[:200]}")
        return resp.text()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"[bbox] south={BBOX[0]:.6f} west={BBOX[1]:.6f} north={BBOX[2]:.6f} east={BBOX[3]:.6f}")
    print(f"[query] {len(QUERY)} chars")

    last_err = None
    import time

    for endpoint in ENDPOINTS:
        url = endpoint + "?data=" + urllib.parse.quote(QUERY)
        for attempt in range(3):
            print(f"[fetch] {endpoint} (try {attempt + 1})")
            try:
                text = fetch(url)
                trimmed = text.strip()
                if not trimmed:
                    raise RuntimeError("empty response")
                data = json.loads(trimmed)
                if "elements" not in data:
                    raise RuntimeError("no elements: " + trimmed[:300])
                with open(RAW_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                break
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                print(f"[warn] failed: {exc}")
                if attempt < 2:
                    wait = 8 * (attempt + 1)
                    print(f"[retry] wait {wait}s")
                    time.sleep(wait)
        else:
            continue
        break
    else:
        raise SystemExit(f"[error] all endpoints failed: {last_err}")

    elements = data["elements"]
    buildings = [e for e in elements if (e.get("tags") or {}).get("building")]
    roads = [e for e in elements if (e.get("tags") or {}).get("highway")]
    water = [
        e
        for e in elements
        if (e.get("tags") or {}).get("natural") == "water"
        or (e.get("tags") or {}).get("waterway") == "riverbank"
        or (e.get("tags") or {}).get("landuse") == "reservoir"
    ]

    with_geom = [e for e in buildings if e.get("geometry")]
    with_levels = [
        e
        for e in with_geom
        if (e.get("tags") or {}).get("building:levels")
    ]

    stats = {
        "bbox": BBOX,
        "elements": len(elements),
        "buildings": len(buildings),
        "buildings_with_geometry": len(with_geom),
        "buildings_with_levels": len(with_levels),
        "levels_coverage": round(len(with_levels) / max(1, len(with_geom)), 3),
        "roads": len(roads),
        "water": len(water),
        "road_types": _count_tags(roads, "highway"),
        "building_types": _count_tags(with_geom, "building"),
    }
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def _count_tags(items, key):
    counts = {}
    for e in items:
        value = (e.get("tags") or {}).get(key) or "(none)"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


if __name__ == "__main__":
    main()
