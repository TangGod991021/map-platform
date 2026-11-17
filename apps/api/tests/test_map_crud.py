import uuid


def _code(prefix: str = "t") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


async def test_category_crud(client, auth):
    code = _code("cat")
    created = await client.post(
        "/prod-api/map/category",
        json={"code": code, "name": "测试分类"},
        headers=auth,
    )
    assert created.status_code == 200
    category_id = created.json()["data"]["id"]

    updated = await client.put(
        f"/prod-api/map/category/{category_id}",
        json={"name": "测试分类改"},
        headers=auth,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "测试分类改"

    listed = await client.get("/prod-api/map/category/list", headers=auth)
    assert any(row["id"] == category_id for row in listed.json()["data"])

    deleted = await client.delete(
        f"/prod-api/map/category/{category_id}", headers=auth
    )
    assert deleted.status_code == 200


async def test_route_point_validation(client, auth):
    bad = await client.post(
        "/prod-api/map/route",
        json={"name": "单点路线", "points": [[106.60, 26.60]]},
        headers=auth,
    )
    assert bad.status_code == 400
    assert "至少需要 2 个顶点" in bad.json()["msg"]

    good = await client.post(
        "/prod-api/map/route",
        json={"name": "两点路线", "points": [[106.60, 26.60], [106.61, 26.61]]},
        headers=auth,
    )
    assert good.status_code == 200
    route_id = good.json()["data"]["id"]
    assert len(good.json()["data"]["points"]) == 2

    upd_bad = await client.put(
        f"/prod-api/map/route/{route_id}",
        json={"points": [[106.60, 26.60]]},
        headers=auth,
    )
    assert upd_bad.status_code == 400

    listed = await client.get("/prod-api/map/route/list", headers=auth)
    assert any(row["id"] == route_id for row in listed.json()["data"])

    deleted = await client.delete(f"/prod-api/map/route/{route_id}", headers=auth)
    assert deleted.status_code == 200


async def test_area_point_validation(client, auth):
    bad = await client.post(
        "/prod-api/map/area",
        json={"name": "两点区域", "polygon": [[106.60, 26.60], [106.62, 26.60]]},
        headers=auth,
    )
    assert bad.status_code == 400
    assert "至少需要 3 个顶点" in bad.json()["msg"]

    good = await client.post(
        "/prod-api/map/area",
        json={
            "name": "三点区域",
            "polygon": [[106.60, 26.60], [106.62, 26.60], [106.61, 26.62]],
        },
        headers=auth,
    )
    assert good.status_code == 200
    area_id = good.json()["data"]["id"]

    deleted = await client.delete(f"/prod-api/map/area/{area_id}", headers=auth)
    assert deleted.status_code == 200


async def test_label_coordinate_and_public_visibility(client, auth):
    outside = await client.post(
        "/prod-api/map/label",
        json={"name": "省外点", "lng": 120.0, "lat": 31.0},
        headers=auth,
    )
    assert outside.status_code == 400
    assert "贵州省" in outside.json()["msg"]

    name = f"测试点位-{uuid.uuid4().hex[:6]}"
    created = await client.post(
        "/prod-api/map/label",
        json={"name": name, "lng": 106.63, "lat": 26.647, "status": "0"},
        headers=auth,
    )
    assert created.status_code == 200
    label_id = created.json()["data"]["id"]

    draft = await client.get("/map-api/v1/labels", params={"keyword": name})
    assert all(item["id"] != label_id for item in draft.json()["pois"])

    published = await client.put(
        f"/prod-api/map/label/{label_id}/status",
        params={"status": "1"},
        headers=auth,
    )
    assert published.status_code == 200

    after = await client.get("/map-api/v1/labels", params={"keyword": name})
    assert any(item["id"] == label_id for item in after.json()["pois"])

    detail = await client.get(f"/map-api/v1/labels/{label_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == name

    deleted = await client.delete(f"/prod-api/map/label/{label_id}", headers=auth)
    assert deleted.status_code == 200
