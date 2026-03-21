"""
报告服务单元测试
================
"""

from datetime import datetime
from unittest.mock import MagicMock

from src.schemas.report import ReportCreate, ReportDetail, ReportListItem
from src.services.report_service import ReportService


class TestReportService:
    """报告服务测试"""

    def test_create_report(self) -> None:
        """测试创建报告成功"""
        # Arrange
        mock_report_repo = MagicMock()
        mock_report_repo.create.return_value = "507f1f77bcf86cd799439011"

        service = ReportService(report_repo=mock_report_repo)

        plan_data = {
            "plan_name": "测试计划",
            "trip_date": "2026-03-21",
            "overall_rating": "5",
            "some_field": "value",
        }

        # Act
        result = service.create(user_id=1, plan_data=plan_data)

        # Assert
        assert result == "507f1f77bcf86cd799439011"
        mock_report_repo.create.assert_called_once()

        # 验证传递的数据
        call_args = mock_report_repo.create.call_args[0][0]
        assert isinstance(call_args, ReportCreate)
        assert call_args.user_id == 1
        assert call_args.plan_name == "测试计划"
        assert call_args.trip_date == "2026-03-21"
        assert call_args.overall_rating == "5"
        assert call_args.content == plan_data

    def test_create_report_with_missing_fields(self) -> None:
        """测试创建报告时缺少字段使用默认值"""
        # Arrange
        mock_report_repo = MagicMock()
        mock_report_repo.create.return_value = "507f1f77bcf86cd799439011"

        service = ReportService(report_repo=mock_report_repo)

        plan_data = {
            "some_field": "value",
            # 缺少 plan_name, trip_date, overall_rating
        }

        # Act
        result = service.create(user_id=1, plan_data=plan_data)

        # Assert
        assert result == "507f1f77bcf86cd799439011"

        # 验证传递的数据使用默认值
        call_args = mock_report_repo.create.call_args[0][0]
        assert call_args.plan_name == "未命名计划"
        assert call_args.trip_date == ""
        assert call_args.overall_rating == ""

    def test_get_by_id_success(self) -> None:
        """测试获取自己的报告成功"""
        # Arrange
        mock_report_repo = MagicMock()
        mock_report = ReportDetail(
            id="507f1f77bcf86cd799439011",
            user_id=1,
            plan_name="测试计划",
            trip_date="2026-03-21",
            overall_rating="5",
            content={"key": "value"},
            created_at=datetime.utcnow(),
        )
        mock_report_repo.get_by_id.return_value = mock_report

        service = ReportService(report_repo=mock_report_repo)

        # Act
        result = service.get_by_id(report_id="507f1f77bcf86cd799439011", user_id=1)

        # Assert
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.user_id == 1
        mock_report_repo.get_by_id.assert_called_once_with(
            "507f1f77bcf86cd799439011", user_id=1
        )

    def test_get_by_id_not_owner(self) -> None:
        """测试获取他人报告返回 None"""
        # Arrange
        mock_report_repo = MagicMock()
        # 报告存在但属于用户 2
        mock_report = ReportDetail(
            id="507f1f77bcf86cd799439011",
            user_id=2,
            plan_name="测试计划",
            trip_date="2026-03-21",
            overall_rating="5",
            content={"key": "value"},
            created_at=datetime.utcnow(),
        )
        mock_report_repo.get_by_id.return_value = mock_report

        service = ReportService(report_repo=mock_report_repo)

        # Act - 用户 1 尝试获取用户 2 的报告
        result = service.get_by_id(report_id="507f1f77bcf86cd799439011", user_id=1)

        # Assert
        assert result is None
        mock_report_repo.get_by_id.assert_called_once_with(
            "507f1f77bcf86cd799439011", user_id=1
        )

    def test_get_by_id_not_found(self) -> None:
        """测试获取不存在的报告返回 None"""
        # Arrange
        mock_report_repo = MagicMock()
        mock_report_repo.get_by_id.return_value = None

        service = ReportService(report_repo=mock_report_repo)

        # Act
        result = service.get_by_id(report_id="507f1f77bcf86cd799439011", user_id=1)

        # Assert
        assert result is None

    def test_list_by_user(self) -> None:
        """测试获取报告列表正确"""
        # Arrange
        mock_report_repo = MagicMock()
        mock_items = [
            ReportListItem(
                id="507f1f77bcf86cd799439011",
                plan_name="测试计划1",
                trip_date="2026-03-21",
                overall_rating="5",
                created_at=datetime.utcnow(),
            ),
            ReportListItem(
                id="507f1f77bcf86cd799439012",
                plan_name="测试计划2",
                trip_date="2026-03-22",
                overall_rating="4",
                created_at=datetime.utcnow(),
            ),
        ]
        mock_report_repo.list_by_user.return_value = (mock_items, 2)

        service = ReportService(report_repo=mock_report_repo)

        # Act
        items, pagination = service.list_by_user(user_id=1, page=1, page_size=20)

        # Assert
        assert len(items) == 2
        assert items[0].plan_name == "测试计划1"
        assert items[1].plan_name == "测试计划2"
        assert pagination == {
            "page": 1,
            "page_size": 20,
            "total": 2,
            "total_pages": 1,
        }
        mock_report_repo.list_by_user.assert_called_once_with(1, 1, 20)

    def test_list_by_user_empty(self) -> None:
        """测试获取空报告列表"""
        # Arrange
        mock_report_repo = MagicMock()
        mock_report_repo.list_by_user.return_value = ([], 0)

        service = ReportService(report_repo=mock_report_repo)

        # Act
        items, pagination = service.list_by_user(user_id=1, page=1, page_size=20)

        # Assert
        assert len(items) == 0
        assert pagination == {
            "page": 1,
            "page_size": 20,
            "total": 0,
            "total_pages": 0,
        }

    def test_list_by_user_pagination(self) -> None:
        """测试分页计算正确"""
        # Arrange
        mock_report_repo = MagicMock()
        mock_report_repo.list_by_user.return_value = ([], 25)

        service = ReportService(report_repo=mock_report_repo)

        # Act
        items, pagination = service.list_by_user(user_id=1, page=2, page_size=10)

        # Assert
        assert pagination == {
            "page": 2,
            "page_size": 10,
            "total": 25,
            "total_pages": 3,
        }

    def test_delete_success(self) -> None:
        """测试删除自己的报告成功"""
        # Arrange
        mock_report_repo = MagicMock()
        mock_report = ReportDetail(
            id="507f1f77bcf86cd799439011",
            user_id=1,
            plan_name="测试计划",
            trip_date="2026-03-21",
            overall_rating="5",
            content={"key": "value"},
            created_at=datetime.utcnow(),
        )
        mock_report_repo.get_by_id.return_value = mock_report
        mock_report_repo.delete.return_value = True

        service = ReportService(report_repo=mock_report_repo)

        # Act
        result = service.delete(report_id="507f1f77bcf86cd799439011", user_id=1)

        # Assert
        assert result is True
        mock_report_repo.get_by_id.assert_called_once_with(
            "507f1f77bcf86cd799439011", user_id=1
        )
        mock_report_repo.delete.assert_called_once_with(
            "507f1f77bcf86cd799439011", 1
        )

    def test_delete_not_owner(self) -> None:
        """测试删除他人报告失败"""
        # Arrange
        mock_report_repo = MagicMock()
        mock_report_repo.get_by_id.return_value = None  # 鉴权后不存在

        service = ReportService(report_repo=mock_report_repo)

        # Act
        result = service.delete(report_id="507f1f77bcf86cd799439011", user_id=1)

        # Assert
        assert result is False
        mock_report_repo.get_by_id.assert_called_once_with(
            "507f1f77bcf86cd799439011", user_id=1
        )
        mock_report_repo.delete.assert_not_called()

    def test_delete_not_found(self) -> None:
        """测试删除不存在的报告失败"""
        # Arrange
        mock_report_repo = MagicMock()
        mock_report_repo.get_by_id.return_value = None

        service = ReportService(report_repo=mock_report_repo)

        # Act
        result = service.delete(report_id="507f1f77bcf86cd799439011", user_id=1)

        # Assert
        assert result is False
        mock_report_repo.delete.assert_not_called()

    def test_extract_report_info(self) -> None:
        """测试从计划数据中提取报告信息"""
        # Arrange
        mock_report_repo = MagicMock()
        service = ReportService(report_repo=mock_report_repo)

        plan_data = {
            "plan_name": "测试计划",
            "trip_date": "2026-03-21",
            "overall_rating": "5",
            "other_field": "value",
        }

        # Act
        plan_name, trip_date, overall_rating = service._extract_report_info(plan_data)

        # Assert
        assert plan_name == "测试计划"
        assert trip_date == "2026-03-21"
        assert overall_rating == "5"

    def test_extract_report_info_with_defaults(self) -> None:
        """测试提取报告信息时使用默认值"""
        # Arrange
        mock_report_repo = MagicMock()
        service = ReportService(report_repo=mock_report_repo)

        plan_data = {"other_field": "value"}

        # Act
        plan_name, trip_date, overall_rating = service._extract_report_info(plan_data)

        # Assert
        assert plan_name == "未命名计划"
        assert trip_date == ""
        assert overall_rating == ""
