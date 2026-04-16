"""路线仓库"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.route import RouteModel


class RouteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, route_data: dict) -> int:
        route = RouteModel(**route_data)
        self.session.add(route)
        await self.session.commit()
        await self.session.refresh(route)
        return route.id

    async def find_by_user(self, user_id: int, limit: int = 20) -> List[RouteModel]:
        stmt = (
            select(RouteModel)
            .where(RouteModel.user_id == user_id)
            .order_by(RouteModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_nearby(
        self, lon: float, lat: float, radius_km: float = 50, limit: int = 20
    ) -> List[RouteModel]:
        """简化版：按坐标范围过滤（PostGIS 精确查询在 geoalchemy2 就绪后替换）"""
        import math
        delta = radius_km / 111.0  # 近似：1度 ≈ 111km
        stmt = (
            select(RouteModel)
            .where(
                and_(
                    RouteModel.start_point_lon.between(lon - delta, lon + delta),
                    RouteModel.start_point_lat.between(lat - delta, lat + delta),
                    RouteModel.is_public == 1,
                )
            )
            .order_by(RouteModel.usage_count.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_difficulty(
        self, difficulty: str, limit: int = 20
    ) -> List[RouteModel]:
        stmt = (
            select(RouteModel)
            .where(
                and_(
                    RouteModel.difficulty_level == difficulty,
                    RouteModel.is_public == 1,
                )
            )
            .order_by(RouteModel.usage_count.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, route_id: int) -> Optional[RouteModel]:
        return await self.session.get(RouteModel, route_id)
