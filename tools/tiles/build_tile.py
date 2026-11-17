#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W1 技术验证：把 Overpass 原始数据转换成小程序可直接 require 的瓦片模块，
并生成一个 5,000 建筑的合成压力测试瓦片。

输出：
  pages/map25d/data/tile_osm_jiaxiu.js
  pages/map25d/data/tile_synthetic_5k.js
  tools/tiles/out/tile_manifest.json
  tools/tiles/out/build_stats.json

用法：
  python tools/tiles/fetch_osm_tile.py
  python tools/tiles/build_tile.py
"""

import json
import math
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_PATH = os.path.join(os.path.dirname(__file__), "out", "osm_tile_raw.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
DATA_DIR = os.path.join(ROOT, "pages", "map25d", "data")

LAT0, LON0 = 26.5686, 106.7167
M_PER_DEG_LAT = 110_540.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(LAT0))

# 建筑类型 -> 默认层数（OSM 缺少 building:levels 时使用）
TYPE_LEVELS = {
    "residential": 7,
    "apartments": 9,
    "commercial": 6,
    "office": 8,
    "retail": 5,
    "hotel": 9,
    "school": 5,
    "hospital": 7,
    "government": 6,
    "yes": 4,
}

ROAD_PRIMARY = {
    "motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"
}
ROAD_SECONDARY = {
    "secondary", "tertiary", "secondary_link", "tertiary_link",
    "residential", "service", "unclassified", "pedestrian", "living_street"
}


def project(lat, lon):
    x = (lon - LON0) * M_PER_DEG_LON
    z = (lat - LAT0) * M_PER_DEG_LAT
    return round(x, 1), round(z, 1)


def num(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_from_osm():
    data = json.load(open(RAW_PATH, encoding="utf-8"))
    elements = data.get("elements", [])

    buildings = []
    roads_primary = []
    roads_secondary = []
    water = []

    for el in elements:
        tags = el.get("tags") or {}
        geom = el.get("geometry") or []
        if not geom:
            continue

        if tags.get("building") or tags.get("building:part"):
            pts = [project(p["lat"], p["lon"]) for p in geom]
            if len(pts) < 3:
                continue
            xs = [p[0] for p in pts]
            zs = [p[1] for p in pts]
            w = max(xs) - min(xs)
            d = max(zs) - min(zs)
            if w * d < 20:  # 过滤过小体块
                continue

            btype = tags.get("building") or "yes"
            levels = num(tags.get("building:levels"), 0)
            if levels <= 0:
                levels = TYPE_LEVELS.get(btype, 4)
            height = min(150.0, max(6.0, levels * 3.2))
            # 用 id 做确定性高度扰动，避免过于整齐
            height *= 0.85 + ((el.get("id", 0) * 37) % 100) / 330.0

            name = tags.get("name:zh") or tags.get("name") or ""
            kind = "block"
            if tags.get("tourism") or tags.get("historic") or any(
                key in name for key in ("甲秀", "翠微", "寺", "阁", "塔")
            ):
                kind = "landmark"
                height = max(height, 28.0)

            buildings.append(
                {
                    "x": round((min(xs) + max(xs)) / 2, 1),
                    "z": round((min(zs) + max(zs)) / 2, 1),
                    "w": round(max(3.0, w), 1),
                    "d": round(max(3.0, d), 1),
                    "h": round(height, 1),
                    "k": kind,
                }
            )

        elif tags.get("highway"):
            hw = tags["highway"]
            if hw not in ROAD_PRIMARY and hw not in ROAD_SECONDARY:
                continue
            pts = [project(p["lat"], p["lon"]) for p in geom]
            if len(pts) < 2:
                continue
            if len(pts) > 30:
                step = max(1, len(pts) // 30)
                pts = pts[::step] + [pts[-1]]
            item = {"p": [[x, z] for x, z in pts], "t": "primary" if hw in ROAD_PRIMARY else "secondary"}
            if hw in ROAD_PRIMARY:
                roads_primary.append(item)
            else:
                roads_secondary.append(item)

        elif (
            tags.get("natural") == "water"
            or tags.get("waterway") == "riverbank"
            or tags.get("landuse") == "reservoir"
        ):
            pts = [project(p["lat"], p["lon"]) for p in geom]
            if len(pts) >= 3:
                water.append({"p": [[x, z] for x, z in pts]})

    pois = [
        {"id": 1, "name": "甲秀楼", "type": "landmark", "x": 0.0, "z": 0.0,
         "desc": "南明河上的明代三层楼阁，贵阳城市名片。"},
        {"id": 2, "name": "翠微园", "type": "landmark", "x": 28.0, "z": -34.0,
         "desc": "甲秀楼旁的明清园林建筑群。"},
        {"id": 3, "name": "南明河", "type": "river", "x": -40.0, "z": -120.0,
         "desc": "穿城而过的母亲河，滨河步道适合夜游。"},
        {"id": 4, "name": "甲秀广场", "type": "district", "x": 75.0, "z": 60.0,
         "desc": "老城核心的公共空间与商业节点。"},
    ]

    tile = {
        "meta": {
            "name": "甲秀楼 OSM 500m 瓦片",
            "note": "W1 验证数据：OSM 建筑覆盖稀疏，仅用于管线验证。",
            "center": {"lat": LAT0, "lon": LON0},
            "area": {"width": 500, "depth": 500},
            "attribution": "© OpenStreetMap contributors (ODbL)",
        },
        "water": water,
        "roads": roads_primary + roads_secondary,
        "buildings": buildings,
        "pois": pois,
    }

    stats = {
        "tile": "osm_jiaxiu",
        "buildings": len(buildings),
        "roads_primary": len(roads_primary),
        "roads_secondary": len(roads_secondary),
        "water": len(water),
        "pois": len(pois),
        "bytes": len(json.dumps(tile, ensure_ascii=False)),
    }
    return tile, stats


def build_synthetic(count=5000, size=2000):
    """生成 2000m × 2000m 的合成街区，用于 5K 建筑性能基线。"""
    rng = random.Random(20261117)
    half = size / 2.0
    buildings = []
    roads = []
    pois = []

    # 道路网格：200m 一支，400m 一条主干道
    for i in range(-10, 11):
        v = i * 100.0
        primary = i % 2 == 0
        roads.append({"p": [[v, -half], [v, half]], "t": "primary" if primary else "secondary"})
        roads.append({"p": [[-half, v], [half, v]], "t": "primary" if primary else "secondary"})

    # 在 100m 街区里铺建筑，直到达到目标数量
    block = 100.0
    inner = 72.0
    for bx in range(-10, 10):
        for bz in range(-10, 10):
            cx = bx * block + block / 2
            cz = bz * block + block / 2
            for _ in range(13):
                if len(buildings) >= count:
                    break
                w = rng.uniform(8, 18)
                d = rng.uniform(8, 18)
                x = cx + rng.uniform(-inner / 2 + w / 2, inner / 2 - w / 2)
                z = cz + rng.uniform(-inner / 2 + d / 2, inner / 2 - d / 2)
                h = rng.choice([8, 12, 18, 24, 32, 48, 64, 88])
                buildings.append(
                    {"x": round(x, 1), "z": round(z, 1), "w": round(w, 1),
                     "d": round(d, 1), "h": h, "k": "block"}
                )
            if len(buildings) >= count:
                break
        if len(buildings) >= count:
            break

    # 一条斜向水系（带状多边形）
    river = []
    for i in range(0, 41):
        t = -half + (size * i / 40.0)
        z = 0.25 * t + 40 * math.sin(t / 260.0)
        river.append([round(t, 1), round(z - 35, 1)])
    for i in range(40, -1, -1):
        t = -half + (size * i / 40.0)
        z = 0.25 * t + 40 * math.sin(t / 260.0)
        river.append([round(t, 1), round(z + 35, 1)])
    water = [{"p": river}]

    poi_names = [
        ("城市之眼", "landmark"), ("中央广场", "district"), ("滨河步道", "river"),
        ("甲秀楼", "landmark"), ("翠微园", "landmark"), ("南明河", "river"),
        ("老城街区", "district"), ("文昌阁", "landmark"), ("阳明祠", "landmark"),
        ("商业中心", "district"), ("观景台", "landmark"), ("文化街", "district"),
    ]
    for i in range(12):
        a = rng.uniform(0, math.pi * 2)
        r = rng.uniform(300, 900)
        name, ptype = poi_names[i]
        pois.append(
            {"id": i + 1, "name": name, "type": ptype,
             "x": round(math.cos(a) * r, 1), "z": round(math.sin(a) * r, 1),
             "desc": "5K 合成压力测试点位，用于验证按需加载与交互。"}
        )

    tile = {
        "meta": {
            "name": "5K 合成压力测试瓦片",
            "note": "W1 性能基线：5,000 个建筑盒体、网格道路、1 段水系。",
            "center": {"lat": LAT0, "lon": LON0},
            "area": {"width": size, "depth": size},
            "attribution": "Synthetic geometry for performance testing",
        },
        "water": water,
        "roads": roads,
        "buildings": buildings,
        "pois": pois,
    }
    stats = {
        "tile": "synthetic_5k",
        "buildings": len(buildings),
        "roads": len(roads),
        "water": len(water),
        "pois": len(pois),
        "bytes": len(json.dumps(tile, ensure_ascii=False)),
    }
    return tile, stats


def write_module(path, tile):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = json.dumps(tile, ensure_ascii=False, separators=(",", ":"))
    with open(path, "w", encoding="utf-8") as f:
        f.write("// 自动生成：tools/tiles/build_tile.py，请勿手工修改\n")
        f.write("module.exports = " + body + ";\n")
    return os.path.getsize(path)


def main():
    if not os.path.exists(RAW_PATH):
        raise SystemExit("缺少 OSM 原始数据，请先运行 tools/tiles/fetch_osm_tile.py")

    osm_tile, osm_stats = build_from_osm()
    syn_tile, syn_stats = build_synthetic(5000, 1000)

    osm_path = os.path.join(DATA_DIR, "tile_osm_jiaxiu.js")
    syn_path = os.path.join(DATA_DIR, "tile_synthetic_5k.js")
    osm_stats["module_bytes"] = write_module(osm_path, osm_tile)
    syn_stats["module_bytes"] = write_module(syn_path, syn_tile)

    manifest = {
        "version": 1,
        "tileSize": 500,
        "tiles": [
            {
                "id": "osm_jiaxiu",
                "file": "pages/map25d/data/tile_osm_jiaxiu.js",
                "bbox": [26.5663, 106.7141, 26.5709, 106.7193],
                "lod": 1,
                "buildings": osm_stats["buildings"],
                "size": osm_stats["module_bytes"],
            },
            {
                "id": "synthetic_5k",
                "file": "pages/map25d/data/tile_synthetic_5k.js",
                "bbox": None,
                "lod": 1,
                "buildings": syn_stats["buildings"],
                "size": syn_stats["module_bytes"],
            },
        ],
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "tile_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUT_DIR, "build_stats.json"), "w", encoding="utf-8") as f:
        json.dump({"osm": osm_stats, "synthetic": syn_stats}, f, ensure_ascii=False, indent=2)

    print(json.dumps({"osm": osm_stats, "synthetic": syn_stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
