async def test_health(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


async def test_login_success(client):
    resp = await client.post(
        "/prod-api/login", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["access_token"]


async def test_login_wrong_password(client):
    resp = await client.post(
        "/prod-api/login", json={"username": "admin", "password": "wrong"}
    )
    assert resp.status_code == 400
    assert resp.json()["success"] is False


async def test_admin_api_requires_auth(client):
    resp = await client.get("/prod-api/map/label/list")
    assert resp.status_code == 401


async def test_get_info_and_routers(client, auth):
    info = await client.get("/prod-api/getInfo", headers=auth)
    assert info.status_code == 200
    assert info.json()["data"]["username"] == "admin"

    routers = await client.get("/prod-api/getRouters", headers=auth)
    paths = set()

    def walk(items):
        for item in items:
            paths.add(item["path"])
            walk(item.get("children") or [])

    walk(routers.json()["data"])
    assert {"/map/category", "/map/label", "/map/route", "/map/area", "/map/release"} <= paths
