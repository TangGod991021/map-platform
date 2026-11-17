#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W2 混合方案：抓取贵阳核心区 OSM 路网 / 水系 / 用地。

按 4 个象限分批请求 Overpass，降低单次查询压力并提高成功率。
建筑轮廓不使用 OSM（覆盖不足），由 build_core_hybrid.py 程序化生成。

输出：
  tools/tiles/out/core_osm_raw.json
  tools/tiles/out/core_osm_stats.json

用法：
  python tools/tiles/fetch_core_osm.py
"""

import json
import os
import sys
import time
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

# 核心区外接矩形（覆盖甲秀楼—喷水池—黔灵山南麓）
SOUTH, WEST, NORTH, EAST = 26.555, 106.610, 26.660, 106.725
MID_LAT = (SOUTH + NORTH) / 2
MID_LON = (WEST + EAST) / 2

QUADRANTS = [
    (SOUTH, WEST, MID_LAT, MID_LON),
    (SOUTH, MID_LON, MID_LAT, EAST),
    (MID_LAT, WEST, NORTH, MID_LON),
    (MID_LAT, MID_LON, NORTH, EAST),
]

QUERY_TEMPLATE = """
[out:json][timeout:180];
(
  way["highway"]({s},{w},{n},{e});
  way["natural"="water"]({s},{w},{n},{e});
  way["waterway"="riverbank"]({s},{w},{n},{e});
  way["waterway"~"^(river|stream|canal)$"]({s},{w},{n},{e});
  way["landuse"~"^(residential|commercial|industrial|retail|construction)$"]({s},{w},{n},{e});
);
out geom;
""".strip()

ENDPOINT = "https://overpass-api.de/api/interpreter"
OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
RAW_PATH = os.path.join(OUT_DIR, "core_osm_raw.json")
STATS_PATH = os.path.join(OUT_DIR, "core_osm_stats.json")


def fetch(url: str) -> str:
    with sync_playwright() as p:
        ctx = p.request.new_context()
        resp = ctx.get(url, timeout=240_000)
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}: {resp.text()[:200]}")
        return resp.text()


def fetch_quadrant(bbox):
    s, w, n, e = bbox
    query = QUERY_TEMPLATE.format(s=s, w=w, n=n, e=e)
    url = ENDPOINT + "?data=" + urllib.parse.quote(query)
    last_err = None
    for attempt in range(4):
        print(f"[fetch] {bbox} try {attempt + 1}")
        try:
            text = fetch(url)
            data = json.loads(text)
            if "elements" not in data:
                raise RuntimeError("no elements")
            return data["elements"]
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f"[warn] {exc}")
            if attempt < 3:
                time.sleep(8 * (attempt + 1))
    raise RuntimeError(f"quadrant failed: {bbox}: {last_err}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    merged = {}
    for bbox in QUADRANTS:
        elements = fetch_quadrant(bbox)
        print(f"[ok] {len(elements)} elements")
        for el in elements:
            key = (el.get("type"), el.get("id"))
            merged[key] = el

    elements = list(merged.values())
    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump({"elements": elements}, f, ensure_ascii=False)

    def count(pred):
        return sum(1 for e in elements if pred(e))

    stats = {
        "bbox": [SOUTH, WEST, NORTH, EAST],
        "elements": len(elements),
        "highways": count(lambda e: (e.get("tags") or {}).get("highway")),
        "water": count(
            lambda e: (e.get("tags") or {}).get("natural") == "water"
            or (e.get("tags") or {}).get("waterway") == "riverbank"
        ),
        "landuse": count(lambda e: (e.get("tags") or {}).get("landuse")),
        "road_types": {},
    }
    for e in elements:
        hw = (e.get("tags") or {}).get("highway")
        if hw:
            stats["road_types"][hw] = stats["road_types"].get(hw, 0) + 1
    stats["road_types"] = dict(sorted(stats["road_types"].items(), key=lambda kv: -kv[1]))

    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
