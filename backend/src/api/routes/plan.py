"""匿名户外策划接口。"""

import json
import queue
import threading
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
import os
from time import perf_counter
from typing import Callable, Iterator, Literal, TypeVar
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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


class InsightRequest(BaseModel):
    """AI 概括异步补充请求：基于主结果已返回的搜索参考资料提炼沿途攻略。"""

    keywords: str = Field(min_length=1, max_length=200)
    references: list[WebReference] = Field(default_factory=list)
    api_config: RuntimeAPIConfig = Field(default_factory=RuntimeAPIConfig)


class InsightResponse(BaseModel):
    """AI 概括结果。"""

    success: bool
    summary: str = ""
    message: str = ""


@router.post("/insight", response_model=InsightResponse)
def synthesize_insight(payload: InsightRequest) -> InsightResponse:
    """主结果返回后由前端单独调用，调 LLM 提炼沿途风光/攻略摘要（慢，不阻塞主流程）。"""
    if not payload.references:
        return InsightResponse(success=False, message="没有搜索参考资料，跳过 AI 提炼。")
    api_client_config = payload.api_config.to_api_config()
    if not api_client_config.LLM_API_KEY:
        return InsightResponse(success=False, message="未配置 AI Key，跳过 AI 提炼。")
    try:
        search_service = SearchService(api_client_config)  # type: ignore[no-untyped-call]
        insight = search_service.synthesize_from_references(payload.keywords, payload.references)
    except Exception as exc:  # noqa: BLE001 - AI 提炼失败不影响已展示的主结果
        return InsightResponse(success=False, message=f"AI 提炼失败：{exc}")
    if not insight.summary:
        return InsightResponse(success=False, message="AI 提炼未返回有效摘要。")
    return InsightResponse(success=True, summary=insight.summary)


@router.post("/generate")
def generate_plan(payload: PlanGenerateRequest) -> StreamingResponse:
    """SSE 流式生成：实时推送每个阶段进度，最后推送完整结果。

    事件流：
    - ``event: stage``  data: PlanningStageLog —— 某个阶段完成
    - ``event: result`` data: PlanGenerateResponse —— 最终完整结果
    - ``event: error``  data: {detail} —— 失败
    """
    q: "queue.Queue[tuple[str, object] | None]" = queue.Queue()

    def worker() -> None:
        try:
            result = _run_generate(payload, on_stage=lambda s: q.put(("stage", s)))
            q.put(("result", result))
        except HTTPException as exc:
            q.put(("error", {"status": exc.status_code, "detail": exc.detail}))
        except Exception as exc:  # noqa: BLE001 - 任何异常都通过事件流告知前端
            q.put(("error", {"detail": str(exc)}))
        finally:
            q.put(None)

    threading.Thread(target=worker, daemon=True).start()

    def event_stream() -> Iterator[str]:
        while True:
            item = q.get()
            if item is None:
                break
            kind, data = item
            dumped = data.model_dump(mode="json", by_alias=True) if hasattr(data, "model_dump") else data
            yield f"event: {kind}\ndata: {json.dumps(dumped, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _run_generate(
    payload: PlanGenerateRequest,
    on_stage: Callable[[PlanningStageLog], None],
) -> PlanGenerateResponse:
    """实际生成逻辑：消费浏览器下载的轨迹文件，缺少日期或出发地时只分析轨迹。"""
    run_id = f"run_{uuid4().hex[:12]}"
    run_started = perf_counter()
    stages: _StageList = _StageList(on_stage)
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
    web_references: list[WebReference] = []
    web_insight: WebSearchInsight | None = None
    search_service: SearchService | None = None
    search_keywords: str = ""

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
        else:
            warnings.append("未配置高德地图 API Key，已跳过交通与周边救援查询。")
            _append_stage(stages, "transport_fetch", "交通增强", "skipped", 0, "未配置高德地图 API Key")
            _append_stage(stages, "rescue_fetch", "救援点查询", "skipped", 0, "未配置高德地图 API Key")

        # 网络搜索：与天气/交通并行拉取，不阻塞主结果。SearchClient 会在 Jina 缺 key 时
        # 自动降级到 Tavily，故只要存在任一搜索 key 即可触发。
        has_search_key = bool(api_client_config.SEARCH_API_KEY or os.getenv("TAVILY_API_KEY"))
        if has_search_key:
            search_keywords = (track_analysis.track_name or "户外徒步").strip()
            search_service = SearchService(api_client_config)  # type: ignore[no-untyped-call]
            future_to_stage[
                executor.submit(search_service.search, search_keywords)
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
            elif stage == "search_fetch":
                if isinstance(result, list):
                    web_references = _flatten_search_results(result)
                _append_stage(
                    stages,
                    stage,
                    title,
                    "success",
                    _elapsed_ms(started),
                    f"找到 {len(web_references)} 条网络参考",
                )

        # 搜索结果 + 高德周边线索统一交给 LLM 过滤提炼（高德线索也过 AI，避免 POI 等术语外漏）。
        # 仅在执行过网络搜索时触发；LLM 不可用时 synthesize_insight 内部降级为本地摘要。
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
    on_stage: Callable[[PlanningStageLog], None] | None = None,
) -> T:
    started = perf_counter()
    try:
        result = action()
    except Exception as exc:
        _append_stage(stages, stage, title, "failed", _elapsed_ms(started), str(exc), on_stage=on_stage)
        raise
    _append_stage(stages, stage, title, "success", _elapsed_ms(started), success_message, on_stage=on_stage)
    return result


class _StageList(list[PlanningStageLog]):
    """stage 列表：append 时自动触发 on_stage 回调（用于 SSE 实时推送每个阶段）。"""

    def __init__(self, on_stage: Callable[[PlanningStageLog], None] | None = None) -> None:
        super().__init__()
        self._on_stage = on_stage

    def append(self, log: PlanningStageLog) -> None:
        super().append(log)
        if self._on_stage is not None:
            self._on_stage(log)


def _append_stage(
    stages: list[PlanningStageLog],
    stage: str,
    title: str,
    status: StageStatus,
    duration_ms: int,
    message: str,
    on_stage: Callable[[PlanningStageLog], None] | None = None,
) -> None:
    log = PlanningStageLog(
        stage=stage,
        title=title,
        status=status,
        duration_ms=duration_ms,
        message=message,
    )
    stages.append(log)
    if on_stage is not None:
        on_stage(log)


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
