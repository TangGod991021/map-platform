import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.map import MapRelease
from app.services.map_service import build_public_data


def release_to_dict(release: MapRelease) -> dict:
    return {
        "id": release.id,
        "version": release.version,
        "note": release.note,
        "snapshot_path": release.snapshot_path,
        "created_by": release.created_by,
        "created_at": release.created_at.isoformat() if release.created_at else None,
    }


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(content, encoding="utf-8")
    os.replace(temp_path, path)


async def publish_snapshot(db: AsyncSession, note: str, username: str) -> dict:
    latest = await db.scalar(select(func.max(MapRelease.version))) or 0
    version = latest + 1

    data = await build_public_data(db)
    data["version"] = version
    data["generated_at"] = datetime.now(timezone.utc).isoformat()

    publish_dir = Path(settings.map_publish_dir)
    publish_dir.mkdir(parents=True, exist_ok=True)
    map_path = publish_dir / "map.json"

    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    write_text_atomic(map_path, body)

    manifest = {
        "version": version,
        "generated_at": data["generated_at"],
        "hash": "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "categories": len(data["categories"]),
        "pois": len(data["pois"]),
        "routes": len(data["routes"]),
        "areas": len(data["areas"]),
        "file": "map.json",
    }
    write_text_atomic(
        publish_dir / "manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2),
    )

    release = MapRelease(
        version=version,
        note=note or "",
        snapshot_path=str(map_path),
        created_by=username,
    )
    db.add(release)
    await db.commit()
    await db.refresh(release)

    result = release_to_dict(release)
    result["manifest"] = manifest
    return result


async def list_releases(db: AsyncSession) -> list[dict]:
    rows = (
        await db.scalars(select(MapRelease).order_by(MapRelease.version.desc()))
    ).all()
    return [release_to_dict(row) for row in rows]
