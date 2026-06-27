"""基于已知结构化数据的极速策划生成。"""

from datetime import datetime
import re
from typing import Any

from src.schemas.output import (
    EmergencyRescueContact,
    EquipmentCategory,
    EquipmentItem,
    GridPointWeather,
    OutdoorActivityPlan,
    SafetyAssessment,
    SafetyIssue,
    SafetyIssueType,
    TrackDetailAnalysis,
    TerrainSegment,
    ElevationPoint,
    WebReference,
)
from src.schemas.track import TrackAnalysisResult
from src.schemas.weather import CityWeatherDaily, HourlyWeather, WeatherSummary, parse_wind_scale
from src.schemas.search import WebSearchInsight
from src.schemas.transport import TransportRoutes


class FastPlanService:
    """不依赖 LLM 的保守行前策划生成器。"""

    def generate(
        self,
        *,
        track: TrackAnalysisResult,
        trip_date: str,
        weather: WeatherSummary | None,
        transport: TransportRoutes | None,
        rescue_points: list[dict[str, Any]],
        plan_title: str,
        warnings: list[str],
        web_references: list[WebReference] | None = None,
        web_insight: WebSearchInsight | None = None,
    ) -> OutdoorActivityPlan:
        """用已知事实生成一份可降级的策划书。"""

        daily_weather = self._select_daily_weather(trip_date, weather)
        safety_issues = self._build_safety_issues(track, daily_weather, weather)
        risk_factors = self._build_risk_factors(track, daily_weather, warnings)
        overall_rating = self._decide_rating(safety_issues)
        plan_name = plan_title.strip() or track.track_name or "户外线路行前策划"

        return OutdoorActivityPlan(
            plan_id=f"fast_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now(),
            plan_name=plan_name,
            overall_rating=overall_rating,
            track_overview=self._track_overview(track),
            weather_overview=self._weather_overview(daily_weather, weather),
            transport_overview=self._transport_overview(transport, warnings),
            trip_date_weather=daily_weather,
            hourly_weather=self._select_daytime_hourly_weather(trip_date, weather),
            critical_grid_weather=self._grid_weather(weather, track, daily_weather),
            equipment_recommendations=self._equipment(track, daily_weather),
            scenic_spots=[],
            precautions=self._precautions(track, safety_issues, warnings),
            hiking_advice="",
            web_references=web_references or [],
            web_summary=web_insight.summary if web_insight else "",
            safety_assessment=SafetyAssessment(
                overall_risk=self._overall_risk(safety_issues),
                conditions=self._safety_conditions(track, daily_weather, warnings),
                recommendation=overall_rating,
                risk_level=self._overall_risk(safety_issues),
            ),
            safety_issues=safety_issues,
            risk_factors=risk_factors,
            emergency_rescue_contacts=self._rescue_contacts(rescue_points, web_insight),
            track_detail=self._track_detail(track),
            transport_scheme=transport,
        )

    def _select_daily_weather(self, trip_date: str, weather: WeatherSummary | None) -> CityWeatherDaily:
        if weather:
            candidates = []
            if weather.forecast_3d:
                candidates.extend(weather.forecast_3d.daily)
            if weather.forecast_7d:
                candidates.extend(weather.forecast_7d.daily)
            for daily in candidates:
                if daily.fxDate == trip_date:
                    return daily
            if candidates:
                return candidates[0]

        return CityWeatherDaily(
            fxDate=trip_date,
            tempMax=0,
            tempMin=0,
            textDay="暂无天气数据",
            windScaleDay="未知",
            windSpeedDay=0,
            humidity=0,
            precip=0,
            pressure=0,
        )

    def _select_daytime_hourly_weather(
        self,
        trip_date: str,
        weather: WeatherSummary | None,
    ) -> list[HourlyWeather]:
        """逐小时图只展示出行日白天窗口，避免凌晨预报被误读为活动高温。"""
        if not weather or not weather.hourly_24h:
            return []

        parsed: list[tuple[HourlyWeather, str | None, int | None]] = []
        for item in weather.hourly_24h.hourly:
            date_text, hour = self._parse_hourly_time(item.fxTime)
            parsed.append((item, date_text, hour))

        trip_daytime = [
            item
            for item, date_text, hour in parsed
            if date_text == trip_date and hour is not None and 6 <= hour <= 20
        ]
        if trip_daytime:
            return trip_daytime

        # 如果 24h 预报只覆盖了出行日凌晨，不展示曲线；日天气仍作为主要依据。
        if any(date_text == trip_date for _, date_text, _ in parsed):
            return []

        # 极少数供应商时间字段不可解析时，保留旧降级行为。
        if all(date_text is None and hour is None for _, date_text, hour in parsed):
            return weather.hourly_24h.hourly[:12]

        return []

    def _parse_hourly_time(self, fx_time: str) -> tuple[str | None, int | None]:
        try:
            normalized = fx_time.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            return parsed.date().isoformat(), parsed.hour
        except ValueError:
            match = re.search(r"(?:(\d{4}-\d{2}-\d{2})[T\s])?(\d{1,2}):\d{2}", fx_time)
            if not match:
                return None, None
            date_text = match.group(1)
            return date_text, int(match.group(2))

    def _build_safety_issues(
        self,
        track: TrackAnalysisResult,
        daily: CityWeatherDaily,
        weather: WeatherSummary | None,
    ) -> list[SafetyIssue]:
        issues: list[SafetyIssue] = []

        if track.total_distance_km >= 18 or track.estimated_duration_hours >= 8:
            issues.append(SafetyIssue(
                type=SafetyIssueType.PHYSICAL,
                severity="高" if track.estimated_duration_hours >= 9 else "中",
                description=f"线路约 {track.total_distance_km:.1f}km，预计 {track.estimated_duration_hours:.1f} 小时，对社团队伍体能和队形管理要求较高。",
                mitigation="设置收队和中途检查点，超过预设时间仍未到达关键点时直接缩短线路或下撤。",
            ))

        if track.total_ascent_m >= 800 or track.difficulty_level in {"困难", "极难"}:
            issues.append(SafetyIssue(
                type=SafetyIssueType.TERRAIN,
                severity="高" if track.total_ascent_m >= 1200 else "中",
                description=f"累计爬升约 {track.total_ascent_m:.0f}m，难度为{track.difficulty_level}。",
                mitigation="控制前半程速度，强制携带登山杖、防滑鞋和补给；新手比例高时不建议成行。",
            ))

        if track.terrain_analysis:
            warnings = track.get_segment_warnings()
            issues.append(SafetyIssue(
                type=SafetyIssueType.TERRAIN,
                severity="中" if len(track.terrain_analysis) <= 2 else "高",
                description="存在明显大爬升或大下降路段：" + "；".join(warnings[:3]),
                mitigation="雨后、夜间和队员膝盖不适时降低速度，必要时绕行或折返。",
            ))

        if weather is None:
            issues.append(SafetyIssue(
                type=SafetyIssueType.WEATHER,
                severity="中",
                description="本次未取得真实天气数据，不能判断降水、风力、低温和能见度风险。",
                mitigation="出发前 24 小时复核天气预警；无法确认天气时按保守装备准备并降低行程强度。",
            ))
        else:
            wind_scale = parse_wind_scale(daily.windScaleDay)
            if daily.precip >= 10 or wind_scale >= 5 or daily.tempMax >= 34 or daily.tempMin <= 0:
                severity = "高" if daily.precip >= 25 or wind_scale >= 6 else "中"
                issues.append(SafetyIssue(
                    type=SafetyIssueType.WEATHER,
                    severity=severity,
                    description=f"天气条件：{daily.textDay}，{daily.tempMin}~{daily.tempMax}°C，降水 {daily.precip}mm，风力 {daily.windScaleDay} 级。",
                    mitigation="根据实时天气决定是否延期；强降水、强风或低温条件下不组织新手队伍。",
                ))

        return issues

    def _build_risk_factors(
        self,
        track: TrackAnalysisResult,
        daily: CityWeatherDaily,
        warnings: list[str],
    ) -> list[str]:
        factors = [track.difficulty_level, track.safety_risk]
        if track.total_ascent_m >= 800:
            factors.append("大爬升")
        if track.estimated_duration_hours >= 8:
            factors.append("长时间行走")
        if daily.textDay != "暂无天气数据":
            if daily.precip >= 10:
                factors.append("降水")
            if parse_wind_scale(daily.windScaleDay) >= 5:
                factors.append("大风")
        if warnings:
            factors.append("部分数据降级")
        return list(dict.fromkeys(factors))

    def _decide_rating(self, _issues: list[SafetyIssue]) -> str:
        # 当前产品不做线路推荐判断，保留中性值以兼容既有响应契约。
        return "谨慎推荐"

    def _overall_risk(self, issues: list[SafetyIssue]) -> str:
        if any(issue.severity in {"高", "极高"} for issue in issues):
            return "高风险"
        if any(issue.severity == "中" for issue in issues):
            return "中等风险"
        return "低风险"

    def _track_overview(self, track: TrackAnalysisResult) -> str:
        return (
            f"{track.total_distance_km:.1f}km / 爬升{track.total_ascent_m:.0f}m / "
            f"预计{track.estimated_duration_hours:.1f}小时 / {track.difficulty_level}"
        )

    def _weather_overview(self, daily: CityWeatherDaily, weather: WeatherSummary | None) -> str:
        if weather is None:
            return "未取得天气数据，出发前必须复核天气预警"
        return f"{daily.textDay}，{daily.tempMin}~{daily.tempMax}°C，降水{daily.precip}mm，风力{daily.windScaleDay}级"

    def _transport_overview(self, transport: TransportRoutes | None, warnings: list[str]) -> str:
        if transport is None:
            return "未取得交通数据，需人工确认集合点、停车和返程方式"
        if transport.summary.total_distance and transport.summary.total_time:
            return f"{transport.recommended_mode or '建议路线'}：{transport.summary.total_distance}，约{transport.summary.total_time}"
        return transport.recommended_mode or "交通信息已获取，但缺少完整汇总"

    def _grid_weather(
        self,
        weather: WeatherSummary | None,
        track: TrackAnalysisResult,
        daily: CityWeatherDaily,
    ) -> list[GridPointWeather]:
        if not weather:
            return []
        base_raw = weather.grid_points[0] if weather.grid_points else {}
        base_temp = int(base_raw.get("temp", round((daily.tempMax + daily.tempMin) / 2)))
        wind_scale = str(base_raw.get("wind_scale", daily.windScaleDay))
        humidity = int(base_raw.get("humidity", daily.humidity))
        base_elevation = track.start_point.elevation or track.avg_elevation_m or track.min_elevation_m
        points: list[GridPointWeather] = [
            self._make_grid_weather(
                point_type="地区基准",
                temp=base_temp,
                wind_scale=wind_scale,
                humidity=humidity,
                daily=daily,
                estimated=False,
                note=str(base_raw.get("note", "使用线路所在地区/附近气象格点作为基准天气。")),
            )
        ]

        estimate_note = "按标准大气温度递减率 6.5°C/1000m 从地区基准天气和点位海拔估算，非实测格点。"
        points.append(self._estimated_point_weather(
            "起点", track.start_point.elevation, base_elevation, base_temp, wind_scale, humidity, daily, estimate_note
        ))
        if track.max_elev_point:
            points.append(self._estimated_point_weather(
                "最高点", track.max_elev_point.elevation, base_elevation, base_temp, wind_scale, humidity, daily, estimate_note
            ))
        if track.end_point:
            points.append(self._estimated_point_weather(
                "终点", track.end_point.elevation, base_elevation, base_temp, wind_scale, humidity, daily, estimate_note
            ))
        return points

    def _estimated_point_weather(
        self,
        point_type: str,
        elevation: float,
        base_elevation: float,
        base_temp: int,
        wind_scale: str,
        humidity: int,
        daily: CityWeatherDaily,
        note: str,
    ) -> GridPointWeather:
        temp = round(base_temp - 6.5 * ((elevation - base_elevation) / 1000))
        return self._make_grid_weather(point_type, temp, wind_scale, humidity, daily, True, note)

    def _make_grid_weather(
        self,
        point_type: str,
        temp: int,
        wind_scale: str,
        humidity: int,
        daily: CityWeatherDaily,
        estimated: bool,
        note: str,
    ) -> GridPointWeather:
        return GridPointWeather(
            point_type=point_type,
            temp=temp,
            wind_scale=wind_scale,
            humidity=humidity,
            feels_like=self._feels_like(temp, wind_scale, humidity),
            wind_chill=self._wind_chill(temp, wind_scale),
            uv_level=self._uv_level(daily.uvIndex),
            estimated=estimated,
            note=note,
        )

    def _uv_level(self, uv_index: int | None) -> str | None:
        if uv_index is None:
            return None
        if uv_index <= 2:
            return "低"
        if uv_index <= 5:
            return "中等"
        if uv_index <= 7:
            return "高"
        if uv_index <= 10:
            return "很高"
        return "极高"

    def _wind_speed_avg(self, wind_scale: str) -> float:
        scale = parse_wind_scale(wind_scale)
        ranges = {
            0: (0, 1),
            1: (1, 5),
            2: (6, 11),
            3: (12, 19),
            4: (20, 28),
            5: (29, 38),
            6: (39, 49),
            7: (50, 61),
            8: (62, 74),
            9: (75, 88),
            10: (89, 102),
            11: (103, 117),
            12: (118, 150),
        }
        low, high = ranges.get(scale, (0, 0))
        return (low + high) / 2

    def _wind_chill(self, temp: float, wind_scale: str) -> float | None:
        wind_speed = self._wind_speed_avg(wind_scale)
        if temp > 10 or wind_speed < 4.8:
            return None
        value = 13.12 + 0.6215 * temp - 11.37 * (wind_speed ** 0.16) + 0.3965 * temp * (wind_speed ** 0.16)
        return round(value, 1)

    def _feels_like(self, temp: float, wind_scale: str, humidity: int) -> float:
        wind_chill = self._wind_chill(temp, wind_scale)
        if wind_chill is not None:
            return wind_chill
        if temp >= 27 and humidity >= 40:
            heat_index = (
                -8.78469475556 + 1.61139411 * temp + 2.33854883889 * humidity
                - 0.14611605 * temp * humidity - 0.012308094 * temp * temp
                - 0.0164248277778 * humidity * humidity
                + 0.002211732 * temp * temp * humidity
                + 0.00072546 * temp * humidity * humidity
                - 0.000003582 * temp * temp * humidity * humidity
            )
            return round(heat_index, 1)
        return round(temp, 1)

    def _equipment(self, track: TrackAnalysisResult, daily: CityWeatherDaily) -> list[EquipmentItem]:
        items = [
            EquipmentItem(name="防滑徒步鞋", category=EquipmentCategory.FOOTWEAR, priority="必需", description="山路和下坡路段优先防滑"),
            EquipmentItem(name="离线轨迹与充电宝", category=EquipmentCategory.NAVIGATION, priority="必需", description="提前缓存轨迹，避免无信号迷路"),
            EquipmentItem(name="头灯", category=EquipmentCategory.SAFETY, priority="必需", description="预计用时偏长或可能延误时必须携带"),
            EquipmentItem(name="急救包", category=EquipmentCategory.SAFETY, priority="必需", description="含创可贴、绷带、碘伏和个人药品"),
            EquipmentItem(name="饮水和能量补给", category=EquipmentCategory.MISC, priority="必需", description="按个人体重和线路时长准备"),
        ]
        if track.total_ascent_m >= 600:
            items.append(EquipmentItem(name="登山杖", category=EquipmentCategory.SAFETY, priority="推荐", description="降低长下坡膝盖压力"))
        if daily.precip >= 1 or daily.textDay == "暂无天气数据":
            items.append(EquipmentItem(name="雨衣或冲锋衣", category=EquipmentCategory.CLOTHING, priority="推荐", description="天气不确定或有降水时携带"))
        return items

    def _precautions(
        self,
        track: TrackAnalysisResult,
        issues: list[SafetyIssue],
        warnings: list[str],
    ) -> list[str]:
        items = [
            "出发前将轨迹、集合点、撤退点同步给全体成员。",
            "队伍必须设置领队和收队，禁止单人脱离主队。",
            "天黑前无法完成下撤时，立即缩短线路或原路返回。",
        ]
        items.extend(issue.mitigation for issue in issues[:4])
        if track.estimated_duration_hours >= 7:
            items.append("预计用时较长，午后仍未完成主要爬升时应启动下撤判断。")
        items.extend(warnings)
        return list(dict.fromkeys(items))

    def _hiking_advice(
        self,
        track: TrackAnalysisResult,
        overall_rating: str,
        warnings: list[str],
    ) -> str:
        base = (
            f"这条线路的硬指标为 {track.total_distance_km:.1f}km、爬升 {track.total_ascent_m:.0f}m、"
            f"预计 {track.estimated_duration_hours:.1f} 小时。当前建议为“{overall_rating}”。"
        )
        if warnings:
            return base + " 部分外部数据未取得，本策划按保守原则生成，出发前需要人工复核天气、交通和救援信息。"
        return base + " 建议按社团标准流程组织，重点关注队伍节奏、下坡安全和返程时间。"

    def _safety_conditions(
        self,
        track: TrackAnalysisResult,
        daily: CityWeatherDaily,
        warnings: list[str],
    ) -> str:
        parts = [
            f"轨迹风险：{track.safety_risk}",
            f"难度：{track.difficulty_level}",
            f"天气：{daily.textDay}",
        ]
        if warnings:
            parts.append("存在数据降级")
        return "；".join(parts)

    def _rescue_contacts(
        self,
        rescue_points: list[dict[str, Any]],
        web_insight: WebSearchInsight | None = None,
    ) -> list[EmergencyRescueContact]:
        contacts = [
            EmergencyRescueContact(name="公安报警", phone="110", type="报警"),
            EmergencyRescueContact(name="医疗急救", phone="120", type="医疗"),
            EmergencyRescueContact(name="消防救援", phone="119", type="救援"),
        ]
        seen = {contact.phone for contact in contacts}
        if web_insight:
            for item in web_insight.emergency_contacts:
                tel = self._normalize_phone(item.phone)
                if not tel or tel in seen:
                    continue
                seen.add(tel)
                contact_type = item.contact_type if item.contact_type in {"医疗", "救援", "报警"} else "救援"
                contacts.append(EmergencyRescueContact(name=item.name, phone=tel, type=contact_type))
        for point in rescue_points[:5]:
            tel = self._normalize_phone(str(point.get("tel", "")).strip())
            if not tel or tel in seen:
                continue
            seen.add(tel)
            name = str(point.get("name", "周边救援点")).strip()
            poi_type = str(point.get("type", ""))
            contact_type = "医疗" if "医院" in poi_type or "诊所" in poi_type else "报警"
            contacts.append(EmergencyRescueContact(name=name, phone=tel, type=contact_type))
        return contacts

    def _normalize_phone(self, value: str) -> str:
        phones = re.findall(r"(?<!\d)(?:0\d{2,3}[- ]?\d{7,8}|1[3-9]\d{9}|1[1209]{2})(?!\d)", value)
        if not phones:
            return ""
        return re.sub(r"\s+", "", phones[0])

    def _track_detail(self, track: TrackAnalysisResult) -> TrackDetailAnalysis:
        return TrackDetailAnalysis(
            total_distance_km=round(track.total_distance_km, 1),
            total_ascent_m=round(track.total_ascent_m, 1),
            total_descent_m=round(track.total_descent_m, 1),
            max_elevation_m=round(track.max_elevation_m, 1),
            min_elevation_m=round(track.min_elevation_m, 1),
            avg_elevation_m=round(track.avg_elevation_m, 1),
            difficulty_level=track.difficulty_level,
            difficulty_score=round(track.difficulty_score, 1),
            estimated_duration_hours=round(track.estimated_duration_hours, 1),
            safety_risk=track.safety_risk,
            terrain_analysis=[
                TerrainSegment(
                    change_type=segment.change_type,
                    elevation_diff=round(segment.elevation_diff, 1),
                    distance_m=round(segment.distance_m, 1),
                    gradient_percent=round(segment.gradient_percent, 1),
                    start_distance_m=round(segment.start_distance_m, 1),
                )
                for segment in track.terrain_analysis
            ],
            elevation_points=[
                ElevationPoint(
                    distance_m=round(point.distance_m, 1),
                    elevation_m=round(point.elevation_m, 1),
                    is_key_point=point.is_key_point,
                    label=point.label,
                )
                for point in track.elevation_points
            ],
            track_points_gcj02=track.track_points_gcj02,
        )
