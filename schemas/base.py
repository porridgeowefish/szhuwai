"""
Base Data Models
===============

Basic data structures used throughout the system.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class Point3D(BaseModel):
    """三维空间点基类"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    lat: float = Field(..., description="纬度 (WGS84)", ge=-90, le=90)
    lon: float = Field(..., description="经度 (WGS84)", ge=-180, le=180)
    elevation: float = Field(..., description="海拔高度 (米)", ge=-500, le=9000)
    timestamp: Optional[datetime] = Field(None, description="时间戳（如轨迹点自带）")

    @field_validator('elevation')
    @classmethod
    def validate_elevation(cls, v: float) -> float:
        """验证海拔范围（死海到珠峰）"""
        if v < -500 or v > 9000:
            raise ValueError("海拔超出有效范围")
        return v

    def __str__(self):
        return f"Point3D(lat={self.lat}, lon={self.lon}, elev={self.elevation}m)"

    def __hash__(self):
        return hash((self.lat, self.lon, self.elevation))