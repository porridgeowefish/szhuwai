"""
报告业务服务
===========
"""

from typing import Any

from src.repositories.report_repo import ReportRepository
from src.schemas.report import ReportCreate, ReportDetail, ReportListItem


class ReportService:
    """报告业务服务

    封装报告的 CRUD 逻辑，提供权限校验。
    """

    def __init__(self, report_repo: ReportRepository) -> None:
        """初始化服务

        Args:
            report_repo: 报告数据仓库
        """
        self.report_repo = report_repo

    def create(self, user_id: int, plan_data: dict[str, Any]) -> str:
        """创建报告

        Args:
            user_id: 用户 ID
            plan_data: 完整的计划数据

        Returns:
            报告 ID
        """
        # 提取报告信息
        plan_name, trip_date, overall_rating = self._extract_report_info(plan_data)

        # 创建报告
        report_create = ReportCreate(
            user_id=user_id,
            plan_name=plan_name,
            trip_date=trip_date,
            overall_rating=overall_rating,
            content=plan_data,
        )

        return self.report_repo.create(report_create)

    def get_by_id(self, report_id: str, user_id: int) -> ReportDetail | None:
        """获取报告详情（鉴权）

        只能获取自己的报告。

        Args:
            report_id: 报告 ID
            user_id: 当前用户 ID

        Returns:
            报告详情或 None
        """
        report = self.report_repo.get_by_id(report_id, user_id=user_id)
        if report and report.user_id != user_id:
            return None
        return report

    def list_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ReportListItem], dict[str, Any]]:
        """获取用户报告列表

        Args:
            user_id: 用户 ID
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            (报告列表, 分页信息)
        """
        items, total = self.report_repo.list_by_user(user_id, page, page_size)

        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        pagination = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

        return items, pagination

    def delete(self, report_id: str, user_id: int) -> bool:
        """删除报告（鉴权）

        只能删除自己的报告。

        Args:
            report_id: 报告 ID
            user_id: 当前用户 ID

        Returns:
            是否删除成功
        """
        # 先检查报告是否存在且属于该用户
        report = self.report_repo.get_by_id(report_id, user_id=user_id)
        if not report:
            return False

        return self.report_repo.delete(report_id, user_id)

    def _extract_report_info(
        self, plan_data: dict[str, Any]
    ) -> tuple[str, str, str]:
        """从计划数据中提取报告信息

        Args:
            plan_data: 计划数据

        Returns:
            (plan_name, trip_date, overall_rating)
        """
        plan_name = plan_data.get("plan_name", "未命名计划")
        trip_date = plan_data.get("trip_date", "")
        overall_rating = plan_data.get("overall_rating", "")

        return plan_name, trip_date, overall_rating
