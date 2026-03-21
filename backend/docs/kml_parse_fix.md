# KML 解析逻辑修复方案

## 问题
当前 `track_parser.py` 只支持标准 KML `<coordinates>` 格式，不支持 Google Earth 扩展格式 `<gx:Track>` + `<gx:coord>`。

## 修改方案

在 `_parse_kml` 方法中增加对 `gx:coord` 的支持：

```python
def _parse_kml(self, file_path: Path, track_name: str) -> TrackAnalysisResult:
    """解析 KML 文件（支持标准格式和 gx:Track 格式）"""
    import xml.etree.ElementTree as ET

    with open(file_path, 'rb') as f:
        kml_content = f.read()

    tree = ET.fromstring(kml_content)

    # KML namespace（包含 gx 扩展）
    ns = {
        'kml': 'http://www.opengis.net/kml/2.2',
        'gx': 'http://www.google.com/kml/ext/2.2'
    }

    points: List[Point3D] = []

    # 1. 尝试解析 gx:coord 格式（优先）
    for coord_elem in tree.findall('.//gx:coord', ns):
        if coord_elem.text:
            parts = coord_elem.text.strip().split()
            if len(parts) >= 2:
                try:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    elev = float(parts[2]) if len(parts) > 2 else 0
                    points.append(Point3D(
                        lat=lat,
                        lon=lon,
                        elevation=elev,
                        timestamp=None
                    ))
                except (ValueError, IndexError):
                    continue

    # 2. 如果没有找到 gx:coord，尝试标准 coordinates 格式
    if not points:
        for coord_text in tree.findall('.//kml:coordinates', ns):
            if coord_text.text:
                for coord_pair in coord_text.text.strip().split():
                    parts = coord_pair.split(',')
                    if len(parts) >= 2:
                        try:
                            lon = float(parts[0])
                            lat = float(parts[1])
                            elev = float(parts[2]) if len(parts) > 2 else 0
                            points.append(Point3D(
                                lat=lat,
                                lon=lon,
                                elevation=elev,
                                timestamp=None
                            ))
                        except (ValueError, IndexError):
                            continue

    if not points:
        raise TrackParseError("KML 文件中未找到轨迹点")

    logger.info(f"从 {file_path} 解析到 {len(points)} 个轨迹点")

    # 后续处理保持不变
    smoothed_points = self._smooth_elevation(points)
    return self._analyze_points(smoothed_points, track_name)
```

## 关键修改点

1. **增加 gx namespace**：`'gx': 'http://www.google.com/kml/ext/2.2'`
2. **优先解析 gx:coord**：空格分隔的 `lon lat elev`
3. **降级到标准格式**：如果没找到 gx:coord，尝试解析 `<coordinates>`
4. **错误处理**：保留原有的异常处理逻辑

## 测试建议

创建两种格式的测试文件：
- 标准 KML 格式（LineString + coordinates）
- Google Earth 扩展格式（gx:Track + gx:coord）
