# 部署

## 目标服务器布局

```text
/data/map-platform/
├── apps/
│   ├── api/                # FastAPI 后端，127.0.0.1:11000
│   ├── admin-web/dist/     # Vue 管理后台静态文件
│   └── map-web/            # 地图 H5 静态站点
└── ...
```

## 组件

| 组件 | 路径/端口 |
|---|---|
| 后端 | `apps/api`，uvicorn 11000 |
| 管理端 | `apps/admin-web/dist`，`map-admin.mengyu.live` |
| 地图 H5 | `apps/map-web`，`tianmap.mengyu.live` |
| 发布快照 | `apps/map-web/data/map.json` |

## 步骤

1. `deploy/systemd/map-platform-api.service` → `/etc/systemd/system/`；
2. `systemctl daemon-reload && systemctl enable --now map-platform-api`；
3. `deploy/nginx/map-platform.conf` 合并到 Nginx；
4. `certbot --nginx -d map-admin.mengyu.live`；
5. 前端 `npm run build`，上传 `dist`；
6. 地图 H5 上传 `apps/map-web`；
7. 后台发布一次快照，确认 `map.json` 生成。

完整说明见 `docs/部署指南.md`。
