async def test_granted_permission_allows(client, limited_auth):
    resp = await client.get("/prod-api/map/label/list", headers=limited_auth)
    assert resp.status_code == 200


async def test_missing_permission_denies(client, limited_auth):
    create = await client.post(
        "/prod-api/map/label",
        json={"name": "越权点位", "lng": 106.63, "lat": 26.647},
        headers=limited_auth,
    )
    assert create.status_code == 403
    assert create.json()["msg"] == "没有操作权限"

    category = await client.get("/prod-api/map/category/list", headers=limited_auth)
    assert category.status_code == 403

    publish = await client.post(
        "/prod-api/map/release/publish", json={"note": "越权"}, headers=limited_auth
    )
    assert publish.status_code == 403


async def test_super_permission_allows_all(client, auth):
    for path in (
        "/prod-api/map/category/list",
        "/prod-api/map/label/list",
        "/prod-api/map/route/list",
        "/prod-api/map/area/list",
        "/prod-api/map/release/list",
    ):
        resp = await client.get(path, headers=auth)
        assert resp.status_code == 200, path
