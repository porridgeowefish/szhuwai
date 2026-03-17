"""
坐标转换工具模块

提供 WGS-84 与 GCJ-02 (火星坐标系) 之间的转换功能。
主要用于解决两步路 GPX (WGS84) 与高德地图 (GCJ-02) 之间的坐标偏移问题。

参考标准：
- WGS-84: 国际标准 GPS 坐标系
- GCJ-02: 中国国测局坐标系（火星坐标系）

算法来源: 中国国测局标准转换算法
"""

from __future__ import annotations

import math
from typing import Tuple


# 克拉索夫斯基椭球体参数
_SEMI_MAJOR_AXIS = 6378245.0  # 长半轴 (单位: 米)
_ECCENTRICITY_SQUARED = 0.00669342162296594323  # 第一偏心率平方

# 经度范围
_LON_MIN = 72.004
_LON_MAX = 137.8347

# 纬度范围
_LAT_MIN = 0.8293
_LAT_MAX = 55.8271


def _is_in_china(lat: float, lon: float) -> bool:
    """
    判断坐标是否在中国境内（粗略判断）。

    Args:
        lat: 纬度
        lon: 经度

    Returns:
        是否在中国境内
    """
    return _LON_MIN < lon < _LON_MAX and _LAT_MIN < lat < _LAT_MAX


def _transform_lat(lon: float, lat: float) -> float:
    """
    计算纬度的变换量。

    Args:
        lon: 经度（偏移后的）
        lat: 纬度

    Returns:
        纬度变换量
    """
    ret = (
        -100.0
        + 2.0 * lon
        + 3.0 * lat
        + 0.2 * lat * lat
        + 0.1 * lon * lat
        + 0.2 * math.sqrt(math.fabs(lon))
    )
    ret += (
        20.0 * math.sin(6.0 * lon * math.pi)
        + 20.0 * math.sin(2.0 * lon * math.pi)
    ) * 2.0 / 3.0
    ret += (
        20.0 * math.sin(lat * math.pi) + 40.0 * math.sin(lat / 3.0 * math.pi)
    ) * 2.0 / 3.0
    ret += (
        160.0 * math.sin(lat / 12.0 * math.pi)
        + 320.0 * math.sin(lat * math.pi / 30.0)
    ) * 2.0 / 3.0
    return ret


def _transform_lon(lon: float, lat: float) -> float:
    """
    计算经度的变换量。

    Args:
        lon: 经度（偏移后的）
        lat: 纬度

    Returns:
        经度变换量
    """
    ret = (
        300.0
        + lon
        + 2.0 * lat
        + 0.1 * lon * lon
        + 0.1 * lon * lat
        + 0.1 * math.sqrt(math.fabs(lon))
    )
    ret += (
        20.0 * math.sin(6.0 * lon * math.pi)
        + 20.0 * math.sin(2.0 * lon * math.pi)
    ) * 2.0 / 3.0
    ret += (
        20.0 * math.sin(lon * math.pi) + 40.0 * math.sin(lon / 3.0 * math.pi)
    ) * 2.0 / 3.0
    ret += (
        150.0 * math.sin(lon / 12.0 * math.pi)
        + 300.0 * math.sin(lon / 30.0 * math.pi)
    ) * 2.0 / 3.0
    return ret


def _calculate_delta(lon: float, lat: float) -> Tuple[float, float]:
    """
    计算 GCJ-02 相对于 WGS-84 的偏移量。

    Args:
        lon: 经度
        lat: 纬度

    Returns:
        (经度偏移量, 纬度偏移量)
    """
    if not _is_in_china(lat, lon):
        return 0.0, 0.0

    d_lat = _transform_lat(lon - 105.0, lat - 35.0)
    d_lon = _transform_lon(lon - 105.0, lat - 35.0)

    rad_lat = lat / 180.0 * math.pi
    magic = math.sin(rad_lat)
    magic = 1.0 - _ECCENTRICITY_SQUARED * magic * magic
    sqrt_magic = math.sqrt(magic)

    d_lat = (
        d_lat
        * 180.0
        / (
            _SEMI_MAJOR_AXIS
            * (1.0 - _ECCENTRICITY_SQUARED)
            / (magic * sqrt_magic)
            * math.pi
        )
    )
    d_lon = (
        d_lon * 180.0 / (_SEMI_MAJOR_AXIS / sqrt_magic * math.cos(rad_lat) * math.pi)
    )

    return d_lon, d_lat


def wgs84_to_gcj02(lon: float, lat: float) -> Tuple[float, float]:
    """
    将 WGS-84 坐标转换为 GCJ-02 坐标。

    Args:
        lon: WGS-84 经度
        lat: WGS-84 纬度

    Returns:
        (GCJ-02 经度, GCJ-02 纬度)

    Example:
        >>> wgs84_to_gcj02(116.404, 39.915)  # 北京天安门附近
        (116.410244..., 39.916027...)
    """
    d_lon, d_lat = _calculate_delta(lon, lat)

    return lon + d_lon, lat + d_lat


def gcj02_to_wgs84(lon: float, lat: float) -> Tuple[float, float]:
    """
    将 GCJ-02 坐标转换为 WGS-84 坐标。

    使用迭代方法反向计算，精度足够满足一般应用需求。

    Args:
        lon: GCJ-02 经度
        lat: GCJ-02 纬度

    Returns:
        (WGS-84 经度, WGS-84 纬度)

    Example:
        >>> gcj02_to_wgs84(116.410244, 39.916027)  # 反向转换
        (116.404000..., 39.915000...)
    """
    if not _is_in_china(lat, lon):
        return lon, lat

    # 迭代逼近
    wgs_lon, wgs_lat = wgs84_to_gcj02(lon, lat)
    d_lon = wgs_lon - lon
    d_lat = wgs_lat - lat

    return lon - d_lon, lat - d_lat


__all__ = [
    "wgs84_to_gcj02",
    "gcj02_to_wgs84",
]
