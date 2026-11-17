#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W2 混合方案：核心区程序化 2.5D 瓦片生成。

输入：
  tools/tiles/out/core_osm_raw.json（真实路网/水系/用地）

输出：
  tools/tiles/out/hybrid/tile_*.json      全部瓦片
  tools/tiles/out/hybrid/manifest.json    瓦片清单
  tools/tiles/out/hybrid_stats.json       统计
  pages/map25d/data/tile_hybrid_preview.js 甲秀楼所在瓦片（供页面预览）

策略：
  - 真实 OSM 路网 / 水系 / 用地
  - 程序化建筑：按街区主方向旋转的 50m 网格，40m 街区内铺 2×3 / 3×3 建筑
  - 高度：城市中心高度场 + 用地类型 + 随机扰动
  - LOD2：每个街区聚合为一个盒体

用法：
  python tools/tiles/fetch_core_osm.py
  python tools/tiles/build_core_hybrid.py
"""

import json
import math
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_PATH = os.path.join(os.path.dirname(__file__), "out", "core_osm_raw.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "out", "hybrid")
DATA_DIR = os.path.join(ROOT, "pages", "map25d", "data")
HYBRID_DATA_DIR = os.path.join(DATA_DIR, "hybrid")

# 全局投影原点（核心区中心）
LAT0, LON0 = 26.6075, 106.6675
M_PER_DEG_LAT = 110_540.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(LAT0))

TILE_SIZE = 500.0
BLOCK_PITCH = 50.0
BLOCK_INNER = 40.0

# 核心区多边形（lat, lon）：甲秀楼—喷水池—黔灵山南麓
CORE_LATLON = [
    (26.5686, 106.7167),  # 甲秀楼
    (26.5610, 106.7090),
    (26.5620, 106.6960),
    (26.5700, 106.6860),
    (26.5710, 106.6700),
    (26.5780, 106.6560),
    (26.5900, 106.6450),
    (26.6050, 106.6360),
    (26.6200, 106.6250),
    (26.6350, 106.6200),
    (26.6520, 106.6220),
    (26.6550, 106.6320),
    (26.6480, 106.6420),
    (26.6380, 106.6520),
    (26.6250, 106.6650),
    (26.6100, 106.6750),
    (26.5980, 106.6880),
    (26.5850, 106.7000),
    (26.5750, 106.7120),
]

# 高度场中心
HEIGHT_CENTERS = [
    (26.6470, 106.6302, 1200.0, 85.0),  # 喷水池
    (26.5686, 106.7167, 900.0, 55.0),   # 甲秀楼
    (26.5730, 106.6860, 900.0, 75.0),   # 花果园方向
]

# 手工地标（示意坐标）
LANDMARKS = [
    ("甲秀楼", 26.5686, 106.7167, 32.0, "南明河上的明代三层楼阁，贵阳城市名片。"),
    ("翠微园", 26.5692, 106.7150, 18.0, "甲秀楼旁的明清园林建筑群。"),
    ("文昌阁", 26.5804, 106.7165, 28.0, "贵阳老城明代阁楼式建筑。"),
    ("阳明祠", 26.5960, 106.7150, 20.0, "纪念王阳明的祠庙与园林。"),
    ("贵州美术馆", 26.5840, 106.7130, 24.0, "贵州现代艺术展示空间。"),
    ("纪念塔", 26.5700, 106.7000, 30.0, "贵阳城市纪念地标。"),
    ("黔灵山公园", 26.6250, 106.6170, 0.0, "城市北部的山体公园与猕猴栖息地。"),
    ("喷水池", 26.6470, 106.6302, 0.0, "贵阳老城中心商圈与交通节点。"),
    ("大十字", 26.6430, 106.6340, 0.0, "中华路与中山路交汇的老城核心。"),
    ("河滨公园", 26.5650, 106.7120, 0.0, "南明河畔的城市公园。"),
    ("贵阳站", 26.5680, 106.7050, 0.0, "贵阳老火车站片区。"),
    ("贵州师范大学", 26.5980, 106.6500, 0.0, "老校区与周边学府街区。"),
    ("观水路", 26.5850, 106.6650, 0.0, "连接老城与东侧片区的干道。"),
    ("油榨街", 26.5750, 106.6930, 0.0, "老城东南侧商业与居住街区。"),
    ("花果园", 26.5730, 106.6860, 0.0, "高密度居住与商业综合体片区。"),
]

# 页面可切换的预览区域
PREVIEW_AREAS = [
    {"key": "jiaxiu", "name": "甲秀楼", "lat": 26.5686, "lon": 106.7167},
    {"key": "penshuichi", "name": "喷水池", "lat": 26.6470, "lon": 106.6302},
    {"key": "dashizi", "name": "大十字", "lat": 26.6430, "lon": 106.6340},
    {"key": "huaguoyuan", "name": "花果园", "lat": 26.5730, "lon": 106.6860},
    {"key": "hebin", "name": "河滨公园", "lat": 26.5650, "lon": 106.7120},
    {"key": "guiyangzhan", "name": "贵阳站", "lat": 26.5680, "lon": 106.7050},
]

RESIDENTIAL = {"residential", "commercial", "industrial", "retail", "construction"}


def project(lat, lon):
    x = (lon - LON0) * M_PER_DEG_LON
    z = (lat - LAT0) * M_PER_DEG_LAT
    return x, z


def unproject(x, z):
    lon = LON0 + x / M_PER_DEG_LON
    lat = LAT0 + z / M_PER_DEG_LAT
    return lat, lon


def point_in_poly(x, z, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if (zi > z) != (zj > z):
            if x < (xj - xi) * (z - zi) / (zj - zi) + xi:
                inside = not inside
        j = i
    return inside


def dist_point_segment(px, pz, x1, z1, x2, z2):
    dx = x2 - x1
    dz = z2 - z1
    if dx == 0 and dz == 0:
        return math.hypot(px - x1, pz - z1)
    t = ((px - x1) * dx + (pz - z1) * dz) / (dx * dx + dz * dz)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (x1 + t * dx), pz - (z1 + t * dz))


def bbox_of(points):
    xs = [p[0] for p in points]
    zs = [p[1] for p in points]
    return min(xs), min(zs), max(xs), max(zs)


def bbox_overlap(a, b, pad=0.0):
    return not (a[2] + pad < b[0] or a[0] - pad > b[2] or a[3] + pad < b[1] or a[1] - pad > b[3])


def load_osm():
    data = json.load(open(RAW_PATH, encoding="utf-8"))
    roads = []
    water = []
    landuse = []

    for el in data.get("elements", []):
        tags = el.get("tags") or {}
        geom = el.get("geometry") or []
        if len(geom) < 2:
            continue
        pts = [project(p["lat"], p["lon"]) for p in geom]

        hw = tags.get("highway")
        if hw:
            if hw in {"footway", "path", "steps", "cycleway", "elevator", "ladder", "construction"}:
                continue
            primary = hw in {"motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"}
            secondary = hw in {
                "secondary", "tertiary", "secondary_link", "tertiary_link",
                "residential", "service", "unclassified", "pedestrian", "living_street",
            }
            if not (primary or secondary):
                continue
            roads.append({
                "p": pts,
                "t": "primary" if primary else "secondary",
                "bbox": bbox_of(pts),
                "hw": hw,
            })
            continue

        ww = tags.get("waterway")
        if ww in {"river", "stream", "canal"}:
            roads.append({"p": pts, "t": "river", "bbox": bbox_of(pts), "hw": ww})
            continue

        if tags.get("natural") == "water" or tags.get("waterway") == "riverbank":
            if len(pts) >= 3:
                water.append({"p": pts, "bbox": bbox_of(pts)})
            continue

        lu = tags.get("landuse")
        if lu in RESIDENTIAL and len(pts) >= 3:
            landuse.append({"p": pts, "type": lu, "bbox": bbox_of(pts)})

    return roads, water, landuse


def dominant_angle(segments):
    import collections

    bins = collections.Counter()
    for x1, z1, x2, z2, kind in segments:
        if kind == "river":
            continue
        dx = x2 - x1
        dz = z2 - z1
        if dx * dx + dz * dz < 400:
            continue
        angle = math.degrees(math.atan2(dz, dx)) % 90.0
        bins[int(angle / 5.0) * 5] += 1
    if not bins:
        return 0.0
    peak = bins.most_common(1)[0][0]
    return math.radians(peak + 2.5)


def rotate(u, v, angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return u * c - v * s, u * s + v * c


def landuse_at(x, z, landuse_polys):
    for item in landuse_polys:
        if point_in_poly(x, z, item["p"]):
            return item["type"]
    return "residential"


def height_at(lat, lon, landuse_type, rng):
    h = 12.0
    for clat, clon, sigma, peak in HEIGHT_CENTERS:
        d = math.hypot((lat - clat) * M_PER_DEG_LAT, (lon - clon) * M_PER_DEG_LON)
        h += peak * math.exp(-(d * d) / (2 * sigma * sigma))
    if landuse_type == "commercial":
        h *= 1.2
    elif landuse_type == "industrial":
        h *= 0.75
    elif landuse_type == "construction":
        h *= 0.3
    h *= rng.uniform(0.65, 1.45)
    h = max(8.0, min(120.0, h))
    return round(round(h / 3.0) * 3.0, 1)


def make_block_buildings(
    rng,
    tile_x,
    tile_z,
    angle,
    road_segments,
    water_polys,
    landuse_polys,
    core_poly,
    landmarks_local,
):
    buildings = []
    lod2 = []

    for bx in range(-5, 5):
        for bz in range(-5, 5):
            # 街区中心（瓦片局部坐标）
            u = bx * BLOCK_PITCH + BLOCK_PITCH / 2
            v = bz * BLOCK_PITCH + BLOCK_PITCH / 2
            cx, cz = rotate(u, v, angle)

            if abs(cx) > 250 or abs(cz) > 250:
                continue
            if not point_in_poly(cx, cz, core_poly):
                continue

            # 水面 / 水边留白
            in_water = False
            for w in water_polys:
                if point_in_poly(cx, cz, w["p"]):
                    in_water = True
                    break
            if in_water:
                continue

            # 主干道 / 次干道让位
            near_road = False
            for x1, z1, x2, z2, kind in road_segments:
                clearance = {"primary": 11.0, "secondary": 8.0, "river": 18.0}.get(kind, 8.0)
                if dist_point_segment(cx, cz, x1, z1, x2, z2) < clearance:
                    near_road = True
                    break
            if near_road:
                continue

            # 少量广场/绿地留白
            if rng.random() < 0.06:
                continue

            lat, lon = unproject(tile_x + cx, tile_z + cz)
            lu = landuse_at(cx, cz, landuse_polys)

            if lu == "construction":
                continue

            # 核心区高密度：默认 3×3 槽位；工业用地略稀疏
            cols = 2 if lu == "industrial" else 3
            rows = 3
            spacing_x = BLOCK_INNER / cols
            spacing_z = BLOCK_INNER / rows
            size = min(11.5, spacing_x - 2.6, spacing_z - 2.6)

            placed = 0
            for col in range(cols):
                for row in range(rows):
                    build_prob = 0.9 if lu in ("commercial", "retail") else (0.62 if lu == "industrial" else 0.82)
                    if rng.random() > build_prob:
                        continue

                    su = (col - (cols - 1) / 2.0) * spacing_x
                    sv = (row - (rows - 1) / 2.0) * spacing_z
                    bu, bv = rotate(su, sv, angle)
                    px = cx + bu + rng.uniform(-1.8, 1.8)
                    pz = cz + bv + rng.uniform(-1.8, 1.8)

                    if abs(px) > 248 or abs(pz) > 248:
                        continue
                    if not point_in_poly(px, pz, core_poly):
                        continue

                    water_near = False
                    for w in water_polys:
                        if point_in_poly(px, pz, w["p"]):
                            water_near = True
                            break
                        poly = w["p"]
                        for i in range(len(poly) - 1):
                            if dist_point_segment(px, pz, poly[i][0], poly[i][1], poly[i + 1][0], poly[i + 1][1]) < 12.0:
                                water_near = True
                                break
                        if water_near:
                            break
                    if water_near:
                        continue

                    road_hit = False
                    for x1, z1, x2, z2, kind in road_segments:
                        clearance = {"primary": 8.0, "secondary": 5.0, "river": 14.0}.get(kind, 5.0)
                        if dist_point_segment(px, pz, x1, z1, x2, z2) < clearance:
                            road_hit = True
                            break
                    if road_hit:
                        continue

                    landmark_hit = False
                    for lx, lz, _lname, _lh, _ldesc in landmarks_local:
                        if math.hypot(px - lx, pz - lz) < 18.0:
                            landmark_hit = True
                            break
                    if landmark_hit:
                        continue

                    blat, blon = unproject(tile_x + px, tile_z + pz)
                    h = height_at(blat, blon, lu, rng)
                    w = round(rng.uniform(7.5, size), 1)
                    d = round(rng.uniform(7.5, size), 1)
                    buildings.append({
                        "x": round(px, 1), "z": round(pz, 1),
                        "w": w, "d": d, "h": h, "k": "block",
                    })
                    placed += 1

            if placed:
                heights = [b["h"] for b in buildings[-placed:]]
                lod2.append({
                    "x": round(cx, 1), "z": round(cz, 1),
                    "w": BLOCK_INNER - 2.0, "d": BLOCK_INNER - 2.0,
                    "h": round(sum(heights) / len(heights), 1),
                    "k": "block",
                })

    return buildings, lod2


def build():
    if not os.path.exists(RAW_PATH):
        raise SystemExit("缺少核心区 OSM 数据，请先运行 tools/tiles/fetch_core_osm.py")

    roads, water, landuse = load_osm()
    os.makedirs(OUT_DIR, exist_ok=True)

    core_poly = [project(lat, lon) for lat, lon in CORE_LATLON]
    core_bbox = bbox_of(core_poly)
    area_km2 = abs(
        sum(
            core_poly[i][0] * core_poly[(i + 1) % len(core_poly)][1]
            - core_poly[(i + 1) % len(core_poly)][0] * core_poly[i][1]
            for i in range(len(core_poly))
        )
    ) / 2.0 / 1_000_000.0

    landmarks = []
    for name, lat, lon, h, desc in LANDMARKS:
        x, z = project(lat, lon)
        landmarks.append({"name": name, "x": x, "z": z, "h": h, "desc": desc,
                          "type": "landmark" if h > 0 else ("river" if "河" in name else "district")})

    # 瓦片索引范围
    ix_min = int(math.floor(core_bbox[0] / TILE_SIZE))
    ix_max = int(math.floor(core_bbox[2] / TILE_SIZE))
    iz_min = int(math.floor(core_bbox[1] / TILE_SIZE))
    iz_max = int(math.floor(core_bbox[3] / TILE_SIZE))

    NL = chr(10)
    tiles = []
    total_buildings = 0
    total_lod2 = 0
    preview_modules = {}
    area_tiles = {}
    for item in PREVIEW_AREAS:
        ax, az = project(item["lat"], item["lon"])
        aix = int(math.floor(ax / TILE_SIZE))
        aiz = int(math.floor(az / TILE_SIZE))
        area_tiles.setdefault((aix, aiz), []).append(item)
    os.makedirs(HYBRID_DATA_DIR, exist_ok=True)

    for ix in range(ix_min, ix_max + 1):
        for iz in range(iz_min, iz_max + 1):
            cx_global = ix * TILE_SIZE + TILE_SIZE / 2
            cz_global = iz * TILE_SIZE + TILE_SIZE / 2

            corners = [
                (cx_global - 250, cz_global - 250),
                (cx_global + 250, cz_global - 250),
                (cx_global - 250, cz_global + 250),
                (cx_global + 250, cz_global + 250),
                (cx_global, cz_global),
            ]
            if not any(point_in_poly(x, z, core_poly) for x, z in corners):
                continue

            tile_x = cx_global - TILE_SIZE / 2
            tile_z = cz_global - TILE_SIZE / 2
            tile_bbox = (tile_x - 20, tile_z - 20, tile_x + TILE_SIZE + 20, tile_z + TILE_SIZE + 20)

            # 收集瓦片附近道路
            tile_roads = []
            road_segments = []
            for r in roads:
                if not bbox_overlap(r["bbox"], tile_bbox, 80):
                    continue
                pts = [[round(x - cx_global, 1), round(z - cz_global, 1)] for x, z in r["p"]]
                tile_roads.append({"p": pts, "t": r["t"]})
                for i in range(len(pts) - 1):
                    road_segments.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], r["t"]))

            tile_water = []
            for w in water:
                if not bbox_overlap(w["bbox"], tile_bbox, 40):
                    continue
                tile_water.append({"p": [[round(x - cx_global, 1), round(z - cz_global, 1)] for x, z in w["p"]]})

            tile_landuse = []
            for lu in landuse:
                if not bbox_overlap(lu["bbox"], tile_bbox, 40):
                    continue
                tile_landuse.append({
                    "type": lu["type"],
                    "p": [[round(x - cx_global, 1), round(z - cz_global, 1)] for x, z in lu["p"]],
                })

            local_core_poly = [(x - cx_global, z - cz_global) for x, z in core_poly]

            landmarks_local = []
            tile_landmarks = []
            for lm in landmarks:
                if abs(lm["x"] - cx_global) <= 260 and abs(lm["z"] - cz_global) <= 260:
                    lx = lm["x"] - cx_global
                    lz = lm["z"] - cz_global
                    landmarks_local.append((lx, lz, lm["name"], lm["h"], lm["desc"]))
                    tile_landmarks.append(lm)

            angle = dominant_angle(road_segments)
            rng = random.Random(ix * 73856093 ^ iz * 19349663 ^ 20261117)
            buildings, lod2 = make_block_buildings(
                rng, tile_x, tile_z, angle, road_segments, tile_water, tile_landuse,
                local_core_poly, landmarks_local
            )

            # 手工地标体块
            for lm in landmarks_local:
                lx, lz, lname, lh, ldesc = lm
                if lh > 0:
                    buildings.append({
                        "x": round(lx, 1), "z": round(lz, 1),
                        "w": 18.0, "d": 18.0, "h": lh, "k": "landmark",
                    })
                    lod2.append({
                        "x": round(lx, 1), "z": round(lz, 1),
                        "w": 18.0, "d": 18.0, "h": lh, "k": "landmark",
                    })

            pois = []
            for i, lm in enumerate(tile_landmarks):
                pois.append({
                    "id": i + 1,
                    "name": lm["name"],
                    "type": lm["type"],
                    "x": round(lm["x"] - cx_global, 1),
                    "z": round(lm["z"] - cz_global, 1),
                    "desc": lm["desc"],
                })

            if not buildings:
                continue

            tile_id = f"tile_{ix}_{iz}"
            tile = {
                "meta": {
                    "name": f"核心区瓦片 {ix},{iz}",
                    "note": "W2 混合方案：OSM 路网/水系 + 程序化建筑，非测绘数据。",
                    "center": dict(zip(("lat", "lon"), unproject(cx_global, cz_global))),
                    "area": {"width": TILE_SIZE, "depth": TILE_SIZE},
                    "attribution": "Roads/water © OpenStreetMap contributors (ODbL); buildings generated",
                },
                "water": tile_water,
                "roads": tile_roads,
                "buildings": buildings,
                "buildingsLod2": lod2,
                "pois": pois,
            }

            path = os.path.join(OUT_DIR, tile_id + ".json")
            body = json.dumps(tile, ensure_ascii=False, separators=(",", ":"))
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)

            lat, lon = unproject(cx_global, cz_global)
            tiles.append({
                "id": tile_id,
                "file": f"tile_{ix}_{iz}.json",
                "center": [round(lat, 6), round(lon, 6)],
                "bbox": [
                    round(unproject(tile_x, tile_z)[1], 6),
                    round(unproject(tile_x, tile_z)[0], 6),
                    round(unproject(tile_x + TILE_SIZE, tile_z + TILE_SIZE)[1], 6),
                    round(unproject(tile_x + TILE_SIZE, tile_z + TILE_SIZE)[0], 6),
                ],
                "buildings": len(buildings),
                "lod2": len(lod2),
                "size": os.path.getsize(path),
            })
            total_buildings += len(buildings)
            total_lod2 += len(lod2)

            # 预览区域所在瓦片：输出为页面可 require 的模块
            if (ix, iz) in area_tiles:
                module_name = f"tile_{ix}_{iz}.js"
                module_path = os.path.join(HYBRID_DATA_DIR, module_name)
                with open(module_path, "w", encoding="utf-8") as f:
                    f.write("// 自动生成：tools/tiles/build_core_hybrid.py，请勿手工修改" + NL)
                    f.write("module.exports = " + body + ";" + NL)
                for item in area_tiles[(ix, iz)]:
                    preview_modules[item["key"]] = "./hybrid/" + module_name

    # 生成预览区域索引（惰性 require）
    loader_lines = []
    list_items = []
    for item in PREVIEW_AREAS:
        if item["key"] not in preview_modules:
            print(f"[warn] preview area not generated: {item['name']}")
            continue
        rel = preview_modules[item["key"]]
        loader_lines.append('    %s: () => require("%s")' % (item["key"], rel))
        list_items.append(
            '    { key: "%s", name: "%s", lat: %s, lon: %s }'
            % (item["key"], item["name"], item["lat"], item["lon"])
        )
    preview_js = NL.join([
        "// 自动生成：tools/tiles/build_core_hybrid.py，请勿手工修改",
        "module.exports = {",
        "  list: [",
        ("," + NL).join(list_items),
        "  ],",
        "  loaders: {",
        ("," + NL).join(loader_lines),
        "  }",
        "};",
        ""
    ])
    with open(os.path.join(DATA_DIR, "hybrid_previews.js"), "w", encoding="utf-8") as f:
        f.write(preview_js)

    # 清理旧版单预览文件
    old_preview = os.path.join(DATA_DIR, "tile_hybrid_preview.js")
    if os.path.exists(old_preview):
        os.remove(old_preview)

    manifest = {
        "version": 1,
        "tileSize": TILE_SIZE,
        "coreAreaKm2": round(area_km2, 2),
        "generatedAt": "2026-11-17",
        "tiles": sorted(tiles, key=lambda t: t["id"]),
    }
    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    sizes = [t["size"] for t in tiles]
    counts = [t["buildings"] for t in tiles]
    stats = {
        "coreAreaKm2": round(area_km2, 2),
        "tiles": len(tiles),
        "buildings": total_buildings,
        "lod2": total_lod2,
        "buildingsPerKm2": round(total_buildings / area_km2, 1) if area_km2 else 0,
        "buildingsPerTileMin": min(counts) if counts else 0,
        "buildingsPerTileMax": max(counts) if counts else 0,
        "buildingsPerTileAvg": round(sum(counts) / len(counts), 1) if counts else 0,
        "tileBytesMin": min(sizes) if sizes else 0,
        "tileBytesMax": max(sizes) if sizes else 0,
        "tileBytesAvg": round(sum(sizes) / len(sizes), 1) if sizes else 0,
        "totalMB": round(sum(sizes) / 1048576.0, 2),
        "previewAreas": [item["key"] for item in PREVIEW_AREAS if item["key"] in preview_modules],
    }
    with open(os.path.join(OUT_DIR, "..", "hybrid_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
