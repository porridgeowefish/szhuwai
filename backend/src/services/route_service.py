"""路线业务逻辑"""

from typing import List, Optional
from src.repositories.route_repo import RouteRepository
from src.models.route import RouteModel


class RouteService:
    def __init__(self, route_repo: RouteRepository):
        self.repo = route_repo

    async def save_route(self, user_id: int, route_data: dict) -> int:
        route_data["user_id"] = user_id
        return await self.repo.create(route_data)

    async def get_user_routes(self, user_id: int) -> List[RouteModel]:
        return await self.repo.find_by_user(user_id)

    async def search_nearby(
        self, lon: float, lat: float, radius_km: float = 50
    ) -> List[RouteModel]:
        return await self.repo.find_nearby(lon, lat, radius_km)

    async def search_by_difficulty(self, difficulty: str) -> List[RouteModel]:
        return await self.repo.find_by_difficulty(difficulty)
