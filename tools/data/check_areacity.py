"""核对本地贵州区划数据与 AreaCity 免费数据。

用法（项目根目录）：
    python tools/data/check_areacity.py
    python tools/data/check_areacity.py --level3 ok_data_level3.csv --level4 ok_data_level4.csv

默认从 jsDelivr 拉取 AreaCity master 分支的两个免费 CSV：
- ok_data_level3.csv：省/市/区县（名称 + 编码）
- ok_data_level4.csv：省/市/区县/乡镇（仅名称与编码，无坐标）

乡镇级坐标/边界（ok_geo4_*.csv）为付费数据，本脚本不做下载。
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "apps" / "map-web" / "data"
BASE_URL = (
    "https://cdn.jsdelivr.net/gh/xiangyuecn/AreaCity-JsSpider-StatsGov@master"
    "/src/%E9%87%87%E9%9B%86%E5%88%B0%E7%9A%84%E6%95%B0%E6%8D%AE/"
)


def read_csv(path: str | None, filename: str) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8-sig")
    url = BASE_URL + filename
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 - 固定数据源
        return resp.read().decode("utf-8-sig")


def rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def load_features(name: str) -> list[dict]:
    path = DATA_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))["features"]


def compare(expected: dict[str, str], actual: dict[str, str], label: str) -> None:
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    renamed = [
        (code, expected[code], actual[code])
        for code in sorted(set(expected) & set(actual))
        if expected[code] != actual[code]
    ]
    print(f"\n[{label}] 本地 {len(actual)} 条，AreaCity {len(expected)} 条")
    print("  缺失:", missing or "无")
    print("  多余:", extra or "无")
    print("  名称不一致:", renamed or "无")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level3", help="本地 ok_data_level3.csv 路径")
    parser.add_argument("--level4", help="本地 ok_data_level4.csv 路径")
    args = parser.parse_args()

    level3 = rows(read_csv(args.level3, "ok_data_level3.csv"))
    level4 = rows(read_csv(args.level4, "ok_data_level4.csv"))
    guizhou3 = [r for r in level3 if r["ext_id"].startswith("52")]
    guizhou4 = [r for r in level4 if r["ext_id"].startswith("52")]

    cities = {r["ext_id"][:6]: r["ext_name"] for r in guizhou3 if r["deep"] == "1"}
    counties = {r["ext_id"][:6]: r["ext_name"] for r in guizhou3 if r["deep"] == "2"}
    towns = {r["ext_id"][:9]: r["ext_name"] for r in guizhou4 if r["deep"] == "3"}

    local_cities = {
        str(f["properties"]["adcode"]): f["properties"]["name"]
        for f in load_features("guizhou-cities.json")
    }
    local_counties = {
        str(f["properties"]["adcode"]): f["properties"]["name"]
        for f in load_features("guizhou-counties.json")
    }
    local_towns = [
        f["properties"].get("name", "") for f in load_features("guizhou-towns.json")
    ]

    compare(cities, local_cities, "市州")
    compare(counties, local_counties, "区县")

    matched = sum(1 for name in local_towns if name in set(towns.values()))
    print(f"\n[乡镇] AreaCity 免费数据 {len(towns)} 个，本地坐标点 {len(local_towns)} 个")
    print(f"  名称匹配: {matched}/{len(local_towns)}")
    print("  说明: 乡镇坐标/边界为付费数据（ok_geo4_*），免费版只有名称与编码。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
