"""Route ORM 模型 — PostGIS 空间数据"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from datetime import datetime

# Note: geoalchemy2 dependency will be added in requirements.txt
# For now, use raw SQL for geometry columns if geoalchemy2 is not available
try:
    from geoalchemy2 import Geometry
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

from src.infrastructure.postgres_client import PostgresBase


class RouteModel(PostgresBase):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")

    # 核心指标
    total_distance_km = Column(Float, nullable=False)
    total_ascent_m = Column(Float, default=0)
    total_descent_m = Column(Float, default=0)
    max_elevation_m = Column(Float, nullable=False)
    min_elevation_m = Column(Float, nullable=False)
    difficulty_level = Column(String(20), nullable=False)
    estimated_duration_hours = Column(Float, nullable=False)

    # 空间数据（使用 geometry 类型）
    start_point_lon = Column(Float, nullable=False)
    start_point_lat = Column(Float, nullable=False)
    # track_linestring 将在 create_tables 时通过 raw SQL 添加

    # 轨迹文件和采样点
    original_file_path = Column(String(500), nullable=True)
    track_points_json = Column(JSON, nullable=True)

    # 元数据
    region = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    is_public = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
