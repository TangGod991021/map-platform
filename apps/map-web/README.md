# 地图 H5（天地图卫星）

静态站点，供微信小程序 `<web-view>` 加载。

## 本地运行

```bash
cd apps/map-web
python -m http.server 8081
```

地址：<http://127.0.0.1:8081/>

## 配置 `config.js`

```js
window.TIANDITU_TK = '你的浏览器端 Key';

window.MAP_CONFIG = {
  center: { lng: 106.6302, lat: 26.6470 },
  zoom: 13,
  showTiandituLabels: false,
  showPois: true,
  showRoutes: true,
  showAreas: true,
  poisApi: './data/map.json', // 或 http://127.0.0.1:8000/map-api/v1/bootstrap
  dataVersion: '1'
};
```

- `showTiandituLabels: false`：不加载 `cia_w`，去掉了地铁线/官方注记；
- `poisApi`：静态快照优先；开发时也可直连后端公开 API；
- 静态快照由后台「发布管理」生成。

## 数据

```text
data/
├── guizhou.json             # 省界
├── guizhou-cities.json      # 市州边界
├── guizhou-counties.json    # 区县边界
├── guizhou-towns.json       # 乡镇中心点（部分）
├── pois.json                # 示例数据
├── map.json                 # 后台发布生成（gitignore）
└── manifest.json            # 后台发布生成（gitignore）
```

## 功能

- 天地图 `img_w` 卫星底图
- 贵州省界高亮 + 省外遮罩 + 查看范围限制
- 省/市/区县边界与动态名称
- 顶部居中逆地理编码位置
- 标签/分类筛选/详情、路线、区域（由后台数据驱动）

## 部署

部署到 `tianmap.mengyu.live` 的静态目录，Nginx 示例见 `deploy/nginx/map-platform.conf`。
`/data/map.json` 建议 `no-store`，保证发布后立即生效。
