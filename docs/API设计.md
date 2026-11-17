# API 设计

## 1. 约定

- 管理接口：`/prod-api/**`，需要 `Authorization: Bearer <token>`
- 管理接口按 `模块:实体:操作` 校验权限（`require_permission`），`*:*:*` 为超级权限；无权限返回 `403 {code:403,msg:"没有操作权限"}`
- 公开接口：`/map-api/v1/**`，只读、无登录
- 统一响应：

```json
{ "code": 200, "msg": "ok", "success": true, "data": {} }
```

分页：

```json
{ "code": 200, "msg": "ok", "success": true, "rows": [], "total": 0 }
```

> `/map-api/v1/bootstrap` 例外：直接返回地图 H5 需要的原始 JSON。

## 2. 管理 API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/prod-api/login` | 登录，body `{username,password}` |
| GET | `/prod-api/getInfo` | 当前用户、角色、权限 |
| GET | `/prod-api/getRouters` | 菜单 |
| GET | `/prod-api/dashboard/summary` | 首页统计 |
| GET | `/prod-api/map/category/list` | 分类列表 |
| POST | `/prod-api/map/category` | 新增分类 |
| PUT | `/prod-api/map/category/{id}` | 修改分类 |
| DELETE | `/prod-api/map/category/{id}` | 删除分类 |
| GET | `/prod-api/map/label/list` | 标签分页：`category_id,status,keyword,page_no,page_size` |
| GET | `/prod-api/map/label/{id}` | 标签详情 |
| POST | `/prod-api/map/label` | 新增标签 |
| PUT | `/prod-api/map/label/{id}` | 修改标签 |
| PUT | `/prod-api/map/label/{id}/status?status=1` | 上下架 |
| DELETE | `/prod-api/map/label/{id}` | 删除标签 |
| GET | `/prod-api/map/route/list` | 路线列表 |
| POST/PUT/DELETE | `/prod-api/map/route...` | 路线 CRUD |
| GET | `/prod-api/map/area/list` | 区域列表 |
| POST/PUT/DELETE | `/prod-api/map/area...` | 区域 CRUD |
| POST | `/prod-api/map/release/publish` | 发布快照，body `{note}` |
| GET | `/prod-api/map/release/list` | 发布记录 |
| POST | `/prod-api/common/upload` | 上传文件（multipart） |

### 登录示例

```bash
curl -X POST http://127.0.0.1:8000/prod-api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'
```

```json
{ "code": 200, "data": { "access_token": "...", "token_type": "bearer" } }
```

### 新增标签示例

```bash
curl -X POST http://127.0.0.1:8000/prod-api/map/label \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "category_id": 1,
    "name": "甲秀楼",
    "lng": 106.7167,
    "lat": 26.5686,
    "address": "南明区翠微巷8号",
    "summary": "南明河上的明代三层楼阁",
    "status": "1"
  }'
```

## 3. 公开 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/map-api/v1/bootstrap` | 分类 + 标签 + 路线 + 区域 + 版本（H5 首版使用） |
| GET | `/map-api/v1/manifest` | 版本与数量 |
| GET | `/map-api/v1/labels?bbox=&category=&keyword=&page_no=&page_size=` | 已发布标签筛选 |
| GET | `/map-api/v1/labels/{id}` | 已发布标签详情 |

### bootstrap 返回

```json
{
  "version": 3,
  "generated_at": "2026-11-17T...",
  "categories": [
    { "key": "scenic", "name": "景点", "color": "#00e5ff" }
  ],
  "pois": [
    {
      "id": 1,
      "name": "甲秀楼",
      "category": "scenic",
      "lng": 106.7167,
      "lat": 26.5686,
      "address": "南明区翠微巷8号",
      "desc": "南明河上的明代三层楼阁",
      "images": [],
      "tags": []
    }
  ],
  "routes": [],
  "areas": []
}
```

## 4. 发布接口

`POST /prod-api/map/release/publish`

```json
{ "note": "新增甲秀楼、喷水池点位" }
```

返回：

```json
{
  "code": 200,
  "data": {
    "id": 3,
    "version": 3,
    "snapshot_path": ".../apps/map-web/data/map.json",
    "manifest": {
      "version": 3,
      "pois": 7,
      "routes": 1,
      "areas": 1,
      "hash": "sha256:..."
    }
  }
}
```
