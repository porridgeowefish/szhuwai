"""匿名户外策划接口。"""

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
import os
from time import perf_counter
from typing import Callable, Literal, TypeVar
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from src.schemas.planning_run import PlanningRunReport, PlanningStageLog, StageStatus
from src.schemas.output import OutdoorActivityPlan, WebReference
from src.schemas.search import WebSearchInsight
from src.schemas.runtime_config import RuntimeAPIConfig
from src.schemas.track import TrackAnalysisResult
from src.schemas.transport import TransportRoutes
from src.schemas.weather import WeatherSummary
from src.services.fast_plan_service import FastPlanService
from src.services.search_service import SearchService
from src.services.track_service import TrackService
from src.services.transport_service import TransportService
from src.services.two_bulu_browser_service import session_manager
from src.services.two_bulu_service import TwoBuluError, TwoBuluService
from src.services.weather_service import WeatherService

router = APIRouter(prefix="/plan", tags=["策划生成"])
T = TypeVar("T")


class PlanGenerateRequest(BaseModel):
    """使用已授权下载的两步路轨迹生成策划。"""

    two_bulu_url: HttpUrl
    two_bulu_session_id: str = Field(min_length=1, max_length=64)
    trip_date: str | None = None
    departure_point: str | None = None
    additional_info: str = Field(default="", max_length=2000)
    api_config: RuntimeAPIConfig = Field(default_factory=RuntimeAPIConfig)
    generation_mode: Literal["fast"] = "fast"


class PlanGenerateResponse(BaseModel):
    """完整策划或仅轨迹分析结果。"""

    mode: Literal["track_only", "quick_plan", "full_plan"]
    track_analysis: TrackAnalysisResult
    plan: OutdoorActivityPlan | None = None
    message: str
    run_report: PlanningRunReport


@router.post(
    "/generate",
    response_model=PlanGenerateResponse,
    response_model_by_alias=True,
)
def generate_plan(payload: PlanGenerateRequest) -> PlanGenerateResponse:
    """消费真实浏览器下载文件；缺少日期或出发地时只分析轨迹。"""

    run_id = f"run_{uuid4().hex[:12]}"
    run_started = perf_counter()
    stages: list[PlanningStageLog] = []
    warnings: list[str] = []

    try:
        track_id = TwoBuluService.extract_track_id(str(payload.two_bulu_url))
        track_path = session_manager.get_download_path(
            payload.two_bulu_session_id,
            expected_track_id=track_id,
        )
    except TwoBuluError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    track_service = TrackService()  # type: ignore[no-untyped-call]
    try:
        track_analysis = _record_stage(
            stages,
            stage="track_parse",
            title="轨迹解析",
            action=lambda: track_service.analyze(str(track_path)),
            success_message="已读取真实轨迹文件",
        )
    except (OSError, ValueError) as exc:
        _append_stage(stages, "track_parse", "轨迹解析", "failed", 0, str(exc))
        raise HTTPException(status_code=502, detail=f"轨迹解析失败：{exc}") from exc

    if not payload.trip_date or not payload.departure_point:
        warnings.append("缺少出行日期或出发地，本次只返回轨迹分析。")
        return PlanGenerateResponse(
            mode="track_only",
            track_analysis=track_analysis,
            message="已完成轨迹分析；填写出行日期和出发地点后可生成行前策划。",
            run_report=_build_run_report(run_id, payload.generation_mode, run_started, stages, warnings),
        )

    plan = _generate_quick_plan(
        track_service=track_service,
        track_analysis=track_analysis,
        trip_date=payload.trip_date,
        departure_point=payload.departure_point,
        api_config=payload.api_config,
        stages=stages,
        warnings=warnings,
    )
    return PlanGenerateResponse(
        mode="quick_plan",
        track_analysis=track_analysis,
        plan=plan,
        message="极速策划生成成功；外部数据缺失时已按保守原则降级。",
        run_report=_build_run_report(run_id, payload.generation_mode, run_started, stages, warnings),
    )


def _generate_quick_plan(
    *,
    track_service: TrackService,
    track_analysis: TrackAnalysisResult,
    trip_date: str,
    departure_point: str,
    api_config: RuntimeAPIConfig,
    stages: list[PlanningStageLog],
    warnings: list[str],
) -> OutdoorActivityPlan:
    """生成默认 V2 极速策划，不让外部 API 或 LLM 阻塞主结果。"""

    api_client_config = api_config.to_api_config()

    key_points = _record_stage(
        stages,
        stage="coordinate_fix",
        title="坐标纠偏",
        action=lambda: track_service.correct_coordinates(track_analysis),
        success_message="已生成地图 API 使用的 GCJ02 坐标",
    )
    start_point = key_points.get("start", track_analysis.start_point)
    destination_coord = f"{start_point.lon},{start_point.lat}"

    weather_data: WeatherSummary | None = None
    transport_data: TransportRoutes | None = None
    rescue_points: list[dict[str, object]] = []
    scenic_context: list[str] = []
    web_references: list[WebReference] = []
    web_insight: WebSearchInsight | None = None

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_stage: dict[Future[object], tuple[str, str, float]] = {}

        if api_client_config.WEATHER_API_KEY:
            weather_service = WeatherService(api_client_config)  # type: ignore[no-untyped-call]
            additional_points: list[tuple[float, float, str]] = []
            future_to_stage[
                executor.submit(
                    weather_service.get_summary,
                    track_analysis.start_point.lon,
                    track_analysis.start_point.lat,
                    trip_date,
                    True,
                    True,
                    additional_points,
                )
            ] = ("weather_fetch", "天气增强", perf_counter())
        else:
            warnings.append("未配置天气 API Key，已跳过真实天气查询。")
            _append_stage(stages, "weather_fetch", "天气增强", "skipped", 0, "未配置天气 API Key")

        if api_client_config.MAP_API_KEY:
            transport_service = TransportService(api_client_config)  # type: ignore[no-untyped-call]
            future_to_stage[
                executor.submit(transport_service.plan, departure_point, destination_coord)
            ] = ("transport_fetch", "交通增强", perf_counter())
            future_to_stage[
                executor.submit(transport_service.search_around_rescue, start_point.lon, start_point.lat)
            ] = ("rescue_fetch", "救援点查询", perf_counter())
            future_to_stage[
                executor.submit(transport_service.collect_scenic_context, start_point.lon, start_point.lat)
            ] = ("scenic_context", "景观线索", perf_counter())
        else:
            warnings.append("未配置高德地图 API Key，已跳过交通与周边救援查询。")
            _append_stage(stages, "transport_fetch", "交通增强", "skipped", 0, "未配置高德地图 API Key")
            _append_stage(stages, "rescue_fetch", "救援点查询", "skipped", 0, "未配置高德地图 API Key")
            _append_stage(stages, "scenic_context", "景观线索", "skipped", 0, "未配置高德地图 API Key")

        # 网络搜索：与天气/交通并行拉取，不阻塞主结果。SearchClient 会在 Jina 缺 key 时
        # 自动降级到 Tavily，故只要存在任一搜索 key 即可触发。
        has_search_key = bool(api_client_config.SEARCH_API_KEY or os.getenv("TAVILY_API_KEY"))
        if has_search_key:
            search_keywords = (track_analysis.track_name or "户外徒步").strip()
            search_service = SearchService(api_client_config)  # type: ignore[no-untyped-call]
            future_to_stage[
                executor.submit(search_service.search_with_insight, search_keywords)
            ] = ("search_fetch", "网络搜索", perf_counter())
        else:
            warnings.append("未配置搜索 API Key，已跳过网络搜索。")
            _append_stage(stages, "search_fetch", "网络搜索", "skipped", 0, "未配置搜索 API Key")

        for future in as_completed(future_to_stage):
            stage, title, started = future_to_stage[future]
            try:
                result = future.result()
            except Exception as exc:
                warnings.append(f"{title}失败，已降级：{exc}")
                _append_stage(stages, stage, title, "degraded", _elapsed_ms(started), str(exc))
                continue

            if stage == "weather_fetch":
                weather_data = result if isinstance(result, WeatherSummary) else None
                _append_stage(stages, stage, title, "success", _elapsed_ms(started), "已取得天气数据")
            elif stage == "transport_fetch":
                transport_data = result if isinstance(result, TransportRoutes) else None
                if transport_data and not transport_data.outbound:
                    warnings.append("交通路线接口不可用，已返回人工确认提示。")
                    _append_stage(stages, stage, title, "degraded", _elapsed_ms(started), "交通接口不可用，已降级为人工确认")
                else:
                    _append_stage(stages, stage, title, "success", _elapsed_ms(started), "已取得交通数据")
            elif stage == "rescue_fetch":
                if isinstance(result, list):
                    rescue_points = [item for item in result if isinstance(item, dict)]
                _append_stage(stages, stage, title, "success", _elapsed_ms(started), f"找到 {len(rescue_points)} 个周边救援点")
            elif stage == "scenic_context":
                if isinstance(result, list):
                    scenic_context = [str(item) for item in result if str(item).strip()]
                _append_stage(stages, stage, title, "success", _elapsed_ms(started), f"收集 {len(scenic_context)} 条高德景观线索")
            elif stage == "search_fetch":
                if isinstance(result, tuple) and len(result) == 2:
                    responses, insight = result
                    web_references = _flatten_search_results(responses) if isinstance(responses, list) else []
                    web_insight = insight if isinstance(insight, WebSearchInsight) else None
                elif isinstance(result, list):
                    web_references = _flatten_search_results(result)
                _append_stage(
                    stages,
                    stage,
                    title,
                    "success",
                    _elapsed_ms(started),
                    f"找到 {len(web_references)} 条网络参考，并完成摘要提炼" if web_insight else f"找到 {len(web_references)} 条网络参考",
                )

        if web_insight and scenic_context and "高德周边线索" not in web_insight.summary:
            scenic_text = "高德周边线索：" + "、".join(scenic_context[:6])
            web_insight.summary = f"{scenic_text}；{web_insight.summary}" if web_insight.summary else scenic_text
        elif scenic_context and web_insight is None:
            web_insight = WebSearchInsight(summary="高德周边线索：" + "、".join(scenic_context[:6]))

    return _record_stage(
        stages,
        stage="quick_synthesis",
        title="极速策划",
        action=lambda: FastPlanService().generate(
            track=track_analysis,
            trip_date=trip_date,
            weather=weather_data,
            transport=transport_data,
            rescue_points=rescue_points,
            plan_title=track_analysis.track_name or "户外线路策划",
            warnings=warnings,
            web_references=web_references,
            web_insight=web_insight,
        ),
        success_message="已基于已知事实生成保守行前策划",
    )


def _flatten_search_results(responses: list[object]) -> list[WebReference]:
    """把多组搜索响应展平、按 URL 去重、截断为网络参考列表（最多 8 条）。"""
    refs: list[WebReference] = []
    seen: set[str] = set()
    for resp in responses:
        for item in getattr(resp, "results", None) or []:
            url = getattr(item, "url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            refs.append(WebReference(
                title=getattr(item, "title", "") or url,
                url=url,
                snippet=getattr(item, "content", ""),
                source=getattr(item, "source", ""),
            ))
            if len(refs) >= 8:
                return refs
    return refs


def _record_stage(
    stages: list[PlanningStageLog],
    *,
    stage: str,
    title: str,
    action: Callable[[], T],
    success_message: str,
) -> T:
    started = perf_counter()
    try:
        result = action()
    except Exception as exc:
        _append_stage(stages, stage, title, "failed", _elapsed_ms(started), str(exc))
        raise
    _append_stage(stages, stage, title, "success", _elapsed_ms(started), success_message)
    return result


def _append_stage(
    stages: list[PlanningStageLog],
    stage: str,
    title: str,
    status: StageStatus,
    duration_ms: int,
    message: str,
) -> None:
    stages.append(PlanningStageLog(
        stage=stage,
        title=title,
        status=status,
        duration_ms=duration_ms,
        message=message,
    ))


def _elapsed_ms(started: float) -> int:
    return max(0, round((perf_counter() - started) * 1000))


def _build_run_report(
    run_id: str,
    strategy: Literal["fast", "ai"],
    run_started: float,
    stages: list[PlanningStageLog],
    warnings: list[str],
) -> PlanningRunReport:
    return PlanningRunReport(
        run_id=run_id,
        strategy=strategy,
        total_duration_ms=_elapsed_ms(run_started),
        stages=stages,
        warnings=warnings,
    )
