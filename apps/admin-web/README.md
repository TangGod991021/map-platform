# 地图管理后台（Vue 3）

## 快速开始

```bash
cd apps/admin-web
npm install
cp .env.example .env
npm run dev
```

- 地址：<http://127.0.0.1:5173>
- 默认账号：`admin / admin123`
- 代理：`/prod-api`、`/profile`、`/map-api` → `http://127.0.0.1:8000`

## 环境变量

```env
# 地图选点需要天地图浏览器端 Key
VITE_TIANDITU_TK=
```

未配置 Key 时，标签编辑仍可手动输入经纬度。

## 页面

| 路由 | 功能 |
|---|---|
| `/login` | 登录 |
| `/dashboard` | 首页统计与快捷入口 |
| `/map/category` | 分类管理 |
| `/map/label` | 标签管理（地图选点、富文本、媒体 URL） |
| `/map/release` | 发布快照与版本记录 |

## 构建

```bash
npm run build
```

产物：`dist/`，部署到 `map-admin.mengyu.live` 的静态目录。

## 组件

- `components/MapPicker.vue`：天地图选点（地图中心十字准星 + 手动坐标）
- `components/RichEditor.vue`：Quill 富文本编辑器

## 约定

- API 统一走 `src/utils/request.js`，自动带 JWT；
- 页面状态：loading / 空态 / 错误提示；
- 标签保存时坐标必须是 WGS84，后端会校验贵州范围。
