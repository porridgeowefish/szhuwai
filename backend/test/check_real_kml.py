"""检查实际KML文件的解析结果"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.track_parser import TrackParser

parser = TrackParser()
result = parser.parse_file('2026-01-02重装南风面酃峰.kml')

print(f'轨迹点数: {result.track_points_count}')
print(f'大爬升段: {len([t for t in result.terrain_analysis if t.change_type == "大爬升"])}')
print(f'大下降段: {len([t for t in result.terrain_analysis if t.change_type == "大下降"])}')

print('\n地形变化段详情:')
for i, t in enumerate(result.terrain_analysis, 1):
    print(f'{i}. {t.change_type}: 海拔变化{t.elevation_diff:.1f}m, 距离{t.distance_m:.1f}m, 坡度{t.gradient_percent:.2f}%')
