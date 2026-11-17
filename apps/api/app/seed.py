import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.admin import SysUser
from app.models.map import MapArea, MapCategory, MapLabel, MapRoute


async def seed_data(db: AsyncSession) -> None:
    await _seed_admin(db)
    await _seed_map(db)


async def _seed_admin(db: AsyncSession) -> None:
    exists = await db.scalar(select(SysUser).where(SysUser.username == "admin"))
    if exists:
        return
    db.add(
        SysUser(
            username="admin",
            password_hash=hash_password("admin123"),
            nickname="系统管理员",
            role="admin",
            permissions='["*:*:*"]',
            status="0",
        )
    )
    await db.commit()


async def _seed_map(db: AsyncSession) -> None:
    category_count = await db.scalar(select(func.count()).select_from(MapCategory)) or 0
    if category_count == 0:
        db.add_all(
            [
                MapCategory(code="scenic", name="景点", color="#00e5ff", sort=10),
                MapCategory(code="food", name="美食", color="#f59e0b", sort=20),
                MapCategory(code="specialty", name="特产", color="#10b981", sort=30),
                MapCategory(code="heritage", name="非遗", color="#8b5cf6", sort=40),
            ]
        )
        await db.commit()

    categories = {
        row.code: row.id
        for row in (await db.scalars(select(MapCategory))).all()
    }

    label_count = await db.scalar(select(func.count()).select_from(MapLabel)) or 0
    if label_count == 0:
        samples = [
            ("甲秀楼", "scenic", 106.7167, 26.5686, "南明区翠微巷8号", "南明河上的明代三层楼阁。"),
            ("黔灵山公园", "scenic", 106.6170, 26.6250, "云岩区枣山路187号", "城市北部的山体公园与猕猴栖息地。"),
            ("喷水池", "food", 106.6302, 26.6470, "云岩区中华中路", "老城中心商圈，小吃与夜市聚集地。"),
            ("花果园美食街", "food", 106.6860, 26.5730, "南明区花果园", "高密度居住区里的夜宵与小吃街。"),
            ("贵州特产集市", "specialty", 106.6302, 26.6460, "云岩区中华中路", "刺梨、辣椒、茶叶、蜡染等贵州特产。"),
            ("苗绣工坊", "heritage", 106.7155, 26.5710, "南明区甲秀楼片区", "苗族刺绣技艺展示与体验。"),
            ("蜡染体验馆", "heritage", 106.6300, 26.6450, "云岩区老城", "贵州蜡染技艺体验与文创。"),
        ]
        for name, code, lng, lat, address, desc in samples:
            db.add(
                MapLabel(
                    category_id=categories.get(code),
                    name=name,
                    lng=lng,
                    lat=lat,
                    address=address,
                    summary=desc,
                    description=f"<p>{desc}</p>",
                    status="1",
                    sort=10,
                )
            )
        await db.commit()

    route_count = await db.scalar(select(func.count()).select_from(MapRoute)) or 0
    if route_count == 0:
        db.add(
            MapRoute(
                name="老城漫步线",
                color="#00e5ff",
                weight=4,
                description="甲秀楼—河滨公园—大十字—喷水池",
                points=json.dumps(
                    [
                        [106.7167, 26.5686],
                        [106.7120, 26.5650],
                        [106.6340, 26.6430],
                        [106.6302, 26.6470],
                    ],
                    ensure_ascii=False,
                ),
                status="0",
            )
        )
        await db.commit()

    area_count = await db.scalar(select(func.count()).select_from(MapArea)) or 0
    if area_count == 0:
        db.add(
            MapArea(
                name="老城核心商圈",
                color="#8b5cf6",
                description="喷水池—大十字核心商业区",
                polygon=json.dumps(
                    [
                        [106.6245, 26.6385],
                        [106.6425, 26.6385],
                        [106.6425, 26.6525],
                        [106.6245, 26.6525],
                    ],
                    ensure_ascii=False,
                ),
                status="0",
            )
        )
        await db.commit()
