"""Agent 工具注册表"""

from src.agent.tools.track import track_analyze
from src.agent.tools.weather import weather_query
from src.agent.tools.transport import transport_route
from src.agent.tools.search import web_search
from src.agent.tools.report import report_generate
from src.agent.tools.route import route_save, route_search


def get_all_tools() -> list:
    """返回所有已注册的 Agent 工具。"""
    return [track_analyze, weather_query, transport_route, web_search, report_generate, route_save, route_search]
