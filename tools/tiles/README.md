# 瓦片数据管线（W1）

W1 技术验证用的离线脚本：抓取 OSM 单瓦片、生成小程序可直接 `require` 的瓦片模块，以及 5K 合成压力测试瓦片。

## 环境

- Python 3.10+
- Playwright（Chromium 已安装）
- 可访问 Overpass API

```bash
python -c "from playwright.sync_api import sync_playwright; print('ok')"
```

## 用法

```bash
# 1. 抓取甲秀楼 500m 瓦片（WGS-84）
python tools/tiles/fetch_osm_tile.py

# 2. 生成瓦片模块
python tools/tiles/build_tile.py

# 3. Node 侧几何构建基准（5K 建筑）
node tools/tiles/bench_build.js

# 4. W2 混合方案：抓取核心区路网/水系/用地
python tools/tiles/fetch_core_osm.py

# 5. W2 混合方案：生成 500m 瓦片 + 程序化建筑
python tools/tiles/build_core_hybrid.py
```

输出：

| 文件 | 说明 |
|---|---|
| `tools/tiles/out/osm_tile_raw.json` | Overpass 原始数据 |
| `tools/tiles/out/osm_tile_stats.json` | OSM 覆盖统计 |
| `tools/tiles/out/tile_manifest.json` | 瓦片清单（W1 版） |
| `tools/tiles/out/build_stats.json` | 生成统计 |
| `pages/map25d/data/tile_osm_jiaxiu.js` | 甲秀楼 OSM 单瓦片 |
| `pages/map25d/data/tile_synthetic_5k.js` | 5,000 建筑合成压测瓦片 |
| `tools/tiles/out/core_osm_raw.json` | 核心区真实路网/水系/用地 |
| `tools/tiles/out/hybrid/tile_*.json` | 194 个核心区混合瓦片 |
| `tools/tiles/out/hybrid/manifest.json` | 瓦片清单（W2） |
| `tools/tiles/out/hybrid_stats.json` | 生成统计 |
| `pages/map25d/data/tile_hybrid_preview.js` | 甲秀楼所在瓦片预览 |

## 开发者工具编译模式

| 模式 | query | 用途 |
|---|---|---|
| 2.5D 城市地图（演示） | 空 | 原有 224 建筑演示场景 |
| W1 · OSM 单瓦片 | `tile=osm&debug=1` | 验证真实数据管线 |
| W1 · 合成 5K 压测 | `tile=synthetic&debug=1` | 性能基线 |
| W2 · 混合方案预览 | `tile=hybrid&debug=1` | 真实路网 + 程序化建筑预览 |

## 说明

- 瓦片模块与 `area25d.js` 结构一致，现有页面可直接渲染。
- W1 使用 JS 模块便于快速验证；W2 改为二进制 `.bin` + manifest，并接入 TileManager。
- OSM 建筑覆盖不足，生产环境需授权数据或程序化街区补全。
