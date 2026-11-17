# 黔山漫游（Qianshan Manyou）· map-platform

面向贵州/贵阳的「天地图卫星地图 + 标签内容管理」一体化平台。小程序对外名：**黔山漫游**；项目代号：**map-platform**。

- **管理后台**：FastAPI + Vue 3 + Element Plus，维护分类、标签、路线、区域与发布版本
- **地图 H5**：天地图卫星底图 + 贵州省界 + 标签/详情，供微信小程序 web-view 加载
- **微信小程序**：卫星地图入口 + 2.5D 实验页
- **发布模型**：后台发布生成静态快照 `map.json`，H5 读取静态文件，公开访问与后台解耦

## 目录结构（Monorepo）

```text
map-platform/
├── apps/
│   ├── api/                 # FastAPI 管理后端 + 公开只读 API
│   │   ├── app/
│   │   │   ├── api/         # admin / map_public
│   │   │   ├── core/        # security / response
│   │   │   ├── models/      # sys_user / map_*
│   │   │   ├── schemas/     # Pydantic
│   │   │   ├── services/    # auth / map / publish
│   │   │   ├── seed.py
│   │   │   └── main.py
│   │   ├── alembic/         # 数据库迁移
│   │   └── scripts/
│   ├── admin-web/           # Vue3 管理后台
│   │   └── src/
│   │       ├── api/ store/ router/ layout/ components/
│   │       └── views/{login,dashboard,map/{category,label,release}}
│   ├── miniprogram/         # 微信小程序（web-view + 2.5D 实验页）
│   └── map-web/             # 天地图卫星 H5（静态站点）
├── deploy/
│   ├── nginx/
│   ├── systemd/
│   └── README.md
├── docs/
│   ├── 架构设计.md
│   ├── 数据库设计.md
│   ├── API设计.md
│   ├── 开发规范.md
│   ├── 部署指南.md
│   └── 操作日志.md
├── scripts/                 # 本地开发脚本
└── tools/tiles/             # 瓦片/数据处理脚本
```

## 快速开始

### 1. 后端

```bash
cd apps/api
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -e .
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

- Swagger：<http://127.0.0.1:8000/docs>
- 默认管理员：`admin / admin123`
- 开发数据库：`apps/api/data/map_platform.db`（SQLite）
- 表结构由 Alembic 迁移管理（`alembic upgrade head`），启动时写入种子数据

### 2. 管理后台

```bash
cd apps/admin-web
npm install
cp .env.example .env
npm run dev
```

- 地址：<http://127.0.0.1:5173>
- 默认代理：`/prod-api`、`/profile`、`/map-api` → `http://127.0.0.1:8000`
- 地图选点需要在 `.env` 填 `VITE_TIANDITU_TK`（浏览器端 Key）

### 3. 地图 H5

```bash
cd apps/map-web
# 任意静态服务器
python -m http.server 8081
```

- 地址：<http://127.0.0.1:8081/>
- 在 `config.js` 填天地图 Key
- 后台点击「发布地图快照」后，H5 读取 `data/map.json`
- 开发也可把 `poisApi` 指向 `http://127.0.0.1:8000/map-api/v1/bootstrap`

### 4. 微信小程序

用微信开发者工具导入 `apps/miniprogram`。

- 默认页面：`pages/map/index`（web-view 加载地图 H5）
- 生产 H5 地址在 `apps/miniprogram/config.js` 的 `mapBaseUrl`
- 2.5D 实验页：`pages/map25d/index`

## 核心流程

```text
管理员登录后台
  → 维护分类 / 标签 / 路线 / 区域
  → 点击「发布地图快照」
  → API 生成 apps/map-web/data/map.json + manifest.json
  → 地图 H5 读取静态快照
  → 小程序 web-view 展示
```

## 企业架构约定

1. **Monorepo 分应用**：api / admin-web / miniprogram / map-web 独立构建、独立部署；
2. **分层**：controller → service → model，业务逻辑不写在路由里；
3. **管理/公开分离**：`/prod-api` 需登录，`/map-api` 只读；
4. **发布快照**：公开地图不直连后台数据库，静态文件可缓存、可回滚；
5. **统一响应**：`{ code, msg, success, data / rows, total }`；
6. **配置外置**：数据库、JWT、目录、Key 全部通过 `.env`；
7. **文档同步**：每次改动更新 `docs/` 对应文档与 `docs/操作日志.md`。

## 部署

见 [docs/部署指南.md](docs/部署指南.md) 与 [deploy/README.md](deploy/README.md)。

## 当前状态

- [x] Monorepo 骨架
- [x] FastAPI 登录 / 分类 / 标签 / 路线 / 区域 / 发布
- [x] Vue3 管理后台：登录、分类、标签、发布
- [x] 发布静态快照 → 地图 H5
- [x] 小程序与 H5 代码迁入
- [ ] 生产 MySQL + Alembic 迁移
- [ ] 富文本/媒体审核、限流、备份
