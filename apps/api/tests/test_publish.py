import json
import os
from pathlib import Path


async def _current_version(client, auth) -> int:
    resp = await client.get("/prod-api/map/release/list", headers=auth)
    versions = [row["version"] for row in resp.json()["data"]]
    return max(versions, default=0)


async def test_publish_creates_snapshot_and_increments(client, auth):
    start = await _current_version(client, auth)
    publish_dir = Path(os.environ["MAP_PUBLISH_DIR"])

    first = await client.post(
        "/prod-api/map/release/publish", json={"note": "pytest"}, headers=auth
    )
    assert first.status_code == 200
    assert first.json()["data"]["version"] == start + 1

    map_data = json.loads((publish_dir / "map.json").read_text(encoding="utf-8"))
    manifest = json.loads((publish_dir / "manifest.json").read_text(encoding="utf-8"))
    assert map_data["version"] == manifest["version"] == start + 1
    assert manifest["pois"] == len(map_data["pois"])
    assert manifest["hash"].startswith("sha256:")
    assert not (publish_dir / ".publish.lock").exists()

    second = await client.post(
        "/prod-api/map/release/publish", json={"note": "pytest-2"}, headers=auth
    )
    assert second.status_code == 200
    assert second.json()["data"]["version"] == start + 2

    public_manifest = await client.get("/map-api/v1/manifest")
    assert public_manifest.status_code == 200
    assert public_manifest.json()["version"] >= start + 2


async def test_public_bootstrap_shape(client):
    resp = await client.get("/map-api/v1/bootstrap")
    assert resp.status_code == 200
    data = resp.json()
    assert {"version", "categories", "pois", "routes", "areas"} <= set(data)
    assert len(data["categories"]) >= 4
    assert all("lng" in poi and "lat" in poi for poi in data["pois"])
