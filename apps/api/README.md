# 地图平台 · 管理后端（FastAPI）

RuoYi 风格的 FastAPI 管理后端，负责：

- 管理员登录 / JWT
- 分类、标签（点位）、路线、区域 CRUD
- 发布静态快照（供地图 H5 读取）
- 公开只读 API（开发/备用）
- 文件上传

## 快速开始

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
- 默认管理员：`admin / admin123`（生产必须修改）
- 开发数据库：`data/map_platform.db`（SQLite）
- 表结构由 Alembic 管理；启动时写入种子数据

## 数据库迁移

改完 `app/models/` 后：

```bash
# 生成迁移脚本（先确认应用能连到数据库）
alembic revision --autogenerate -m "add xxx field"
# 检查生成的迁移文件后再应用
alembic upgrade head
# 回退一版
alembic downgrade -1
```

- 迁移脚本在 `alembic/versions/`，与代码一起提交；
- 线上禁止手改表结构，统一走 `alembic upgrade head`；
- 已存在的老库首次接入时用 `alembic stamp head` 标记基线。

## 生产数据库

```bash
pip install -e ".[mysql]"
```

`.env`：

```env
DATABASE_URL=mysql+asyncmy://user:pass@127.0.0.1:3306/map_platform?charset=utf8mb4
```

> 当前用 `Base.metadata.create_all()` 快速建表；生产建议接入 Alembic 迁移（延续爬虫系统的 Alembic 约定）。

## 接口

| 类型 | 路径 |
|---|---|
| 登录 | `POST /prod-api/login` |
| 用户信息 | `GET /prod-api/getInfo` |
| 分类 | `/prod-api/map/category/list`、`POST/PUT/DELETE` |
| 标签 | `/prod-api/map/label/list`、`GET/{id}`、`POST/PUT/DELETE` |
| 路线/区域 | `/prod-api/map/route/*`、`/area/*` |
| 发布 | `POST /prod-api/map/release/publish`、`GET /prod-api/map/release/list` |
| 上传 | `POST /prod-api/common/upload` |
| 公开数据 | `GET /map-api/v1/bootstrap`、`/labels`、`/labels/{id}` |

## 发布快照

点击发布后，后端会：

1. 校验已发布标签（坐标必须在贵州范围内）；
2. 生成 `map.json` + `manifest.json` 到 `MAP_PUBLISH_DIR`（默认 `apps/map-web/data`）；
3. 写入 `map_release` 版本记录。

H5 的 `config.js` 可配置：

```js
showPois: true,
showRoutes: true,
showAreas: true,
poisApi: './data/map.json'
```

## 目录

```text
app/
├── main.py            # FastAPI 入口
├── config.py          # 配置
├── database.py        # SQLAlchemy async
├── deps.py            # 登录依赖
├── seed.py            # 种子数据
├── core/              # 安全 / 响应
├── models/            # ORM
├── schemas/           # Pydantic
├── services/          # 业务逻辑
└── api/               # 管理 / 公开路由
alembic/
├── env.py             # 迁移环境（复用 app.config.settings 连接串）
└── versions/          # 迁移脚本
scripts/
├── init_db.py         # alembic upgrade head + 种子数据
└── publish_snapshot.py
```

## 安全提示

- 修改 `JWT_SECRET` 与默认管理员密码；
- 富文本正文发布前做白名单过滤（生产接入 bleach/类似库）；
- 上传目录禁止执行脚本；
- 公开接口只读，生产建议直接用静态快照。
