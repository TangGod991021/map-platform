import asyncio
import hashlib
import json
import os
import time
from contextlib import asynccontextmanager
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


LOCK_STALE_SECONDS = 60
LOCK_TIMEOUT_SECONDS = 10


@asynccontextmanager
async def publish_lock(publish_dir: Path, timeout: float = LOCK_TIMEOUT_SECONDS):
    """跨进程发布锁。

    用 O_CREAT|O_EXCL 创建锁文件，保证同一时刻只有一个发布在算版本号和写快照；
    锁文件超过 LOCK_STALE_SECONDS 视为进程崩溃留下的残留，自动清理。
    """
    lock_path = publish_dir / ".publish.lock"
    deadline = time.monotonic() + timeout
    fd: int | None = None

    while fd is None:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii"))
        except FileExistsError:
            try:
                if time.time() - lock_path.stat().st_mtime > LOCK_STALE_SECONDS:
                    lock_path.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise RuntimeError("另一次发布正在进行，请稍后重试") from None
            await asyncio.sleep(0.2)

    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


async def publish_snapshot(db: AsyncSession, note: str, username: str) -> dict:
    publish_dir = Path(settings.map_publish_dir)
    publish_dir.mkdir(parents=True, exist_ok=True)

    async with publish_lock(publish_dir):
        latest = await db.scalar(select(func.max(MapRelease.version))) or 0
        version = latest + 1

        data = await build_public_data(db)
        data["version"] = version
        data["generated_at"] = datetime.now(timezone.utc).isoformat()

        map_path = publish_dir / "map.json"
        manifest_path = publish_dir / "manifest.json"

        body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
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
        manifest_body = json.dumps(manifest, ensure_ascii=False, indent=2)

        # 旧快照留底：数据库提交失败时恢复，避免出现“文件已更新、版本记录没落库”
        previous = {
            path: (path.read_bytes() if path.exists() else None)
            for path in (map_path, manifest_path)
        }

        release = MapRelease(
            version=version,
            note=note or "",
            snapshot_path=str(map_path),
            created_by=username,
        )
        try:
            db.add(release)
            await db.flush()
            write_text_atomic(map_path, body)
            write_text_atomic(manifest_path, manifest_body)
            await db.commit()
            await db.refresh(release)
        except Exception:
            await db.rollback()
            for path, content in previous.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)
            raise

        result = release_to_dict(release)
        result["manifest"] = manifest
        return result


async def list_releases(db: AsyncSession) -> list[dict]:
    rows = (
        await db.scalars(select(MapRelease).order_by(MapRelease.version.desc()))
    ).all()
    return [release_to_dict(row) for row in rows]
