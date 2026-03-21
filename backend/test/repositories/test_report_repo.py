"""
报告仓库单元测试
================
"""

from typing import Any, Generator

import mongomock
import pytest
from bson import ObjectId
from pymongo.database import Database

from src.repositories.report_repo import ReportRepository
from src.schemas.report import ReportCreate


@pytest.fixture  # type: ignore[misc]
def mongo_db() -> Generator[Database[Any], None, None]:
    """创建模拟 MongoDB 数据库"""
    client = mongomock.MongoClient()
    db = client.db
    yield db
    client.drop_database(db.name)


class TestReportRepository:
    """报告仓库测试"""

    def test_create_report(self, mongo_db: Database[Any]) -> None:
        """测试创建报告"""
        # Arrange
        repo = ReportRepository(mongo_db)
        data = ReportCreate(
            user_id=1,
            plan_name="周末徒步计划",
            trip_date="2024-03-16",
            overall_rating="推荐",
            content={"route": "香山", "distance": "5km"},
        )

        # Act
        report_id = repo.create(data)

        # Assert
        assert report_id is not None
        assert isinstance(report_id, str)

        # 验证数据库中的数据
        doc = mongo_db[repo.COLLECTION_NAME].find_one({"_id": ObjectId(report_id)})
        assert doc is not None
        assert doc["user_id"] == 1
        assert doc["plan_name"] == "周末徒步计划"
        assert doc["deleted_at"] is None

    def test_get_by_id_success(self, mongo_db: Database[Any]) -> None:
        """测试获取报告成功"""
        # Arrange
        repo = ReportRepository(mongo_db)
        data = ReportCreate(
            user_id=1,
            plan_name="周末徒步计划",
            trip_date="2024-03-16",
            overall_rating="推荐",
            content={"route": "香山"},
        )
        report_id = repo.create(data)

        # Act
        result = repo.get_by_id(report_id)

        # Assert
        assert result is not None
        assert result.id == report_id
        assert result.plan_name == "周末徒步计划"
        assert result.user_id == 1

    def test_get_by_id_not_found(self, mongo_db: Database[Any]) -> None:
        """测试获取不存在的报告"""
        # Arrange
        repo = ReportRepository(mongo_db)
        fake_id = str(ObjectId())

        # Act
        result = repo.get_by_id(fake_id)

        # Assert
        assert result is None

    def test_get_by_id_with_auth(self, mongo_db: Database[Any]) -> None:
        """测试带鉴权的获取"""
        # Arrange
        repo = ReportRepository(mongo_db)
        data = ReportCreate(
            user_id=1,
            plan_name="周末徒步计划",
            trip_date="2024-03-16",
            overall_rating="推荐",
            content={"route": "香山"},
        )
        report_id = repo.create(data)

        # Act - 使用正确的 user_id
        result = repo.get_by_id(report_id, user_id=1)

        # Assert
        assert result is not None
        assert result.user_id == 1

    def test_get_by_id_wrong_user(self, mongo_db: Database[Any]) -> None:
        """测试获取其他用户的报告返回 None"""
        # Arrange
        repo = ReportRepository(mongo_db)
        data = ReportCreate(
            user_id=1,
            plan_name="周末徒步计划",
            trip_date="2024-03-16",
            overall_rating="推荐",
            content={"route": "香山"},
        )
        report_id = repo.create(data)

        # Act - 使用错误的 user_id
        result = repo.get_by_id(report_id, user_id=999)

        # Assert
        assert result is None

    def test_list_by_user(self, mongo_db: Database[Any]) -> None:
        """测试用户报告列表"""
        # Arrange
        repo = ReportRepository(mongo_db)

        # 创建用户 1 的报告
        repo.create(
            ReportCreate(
                user_id=1,
                plan_name="计划1",
                trip_date="2024-03-16",
                overall_rating="推荐",
                content={},
            )
        )
        repo.create(
            ReportCreate(
                user_id=1,
                plan_name="计划2",
                trip_date="2024-03-17",
                overall_rating="一般",
                content={},
            )
        )

        # 创建用户 2 的报告（不应该出现在用户 1 的列表中）
        repo.create(
            ReportCreate(
                user_id=2,
                plan_name="其他用户计划",
                trip_date="2024-03-16",
                overall_rating="推荐",
                content={},
            )
        )

        # Act
        items, total = repo.list_by_user(user_id=1)

        # Assert
        assert total == 2
        assert len(items) == 2
        assert items[0].plan_name in ("计划1", "计划2")
        assert items[1].plan_name in ("计划1", "计划2")

    def test_list_pagination(self, mongo_db: Database[Any]) -> None:
        """测试分页"""
        # Arrange
        repo = ReportRepository(mongo_db)

        # 创建 5 个报告
        for i in range(5):
            repo.create(
                ReportCreate(
                    user_id=1,
                    plan_name=f"计划{i}",
                    trip_date="2024-03-16",
                    overall_rating="推荐",
                    content={},
                )
            )

        # Act - 第 1 页，每页 2 条
        items1, total1 = repo.list_by_user(user_id=1, page=1, page_size=2)

        # Act - 第 2 页，每页 2 条
        items2, total2 = repo.list_by_user(user_id=1, page=2, page_size=2)

        # Assert
        assert total1 == 5
        assert len(items1) == 2
        assert total2 == 5
        assert len(items2) == 2

    def test_delete_success(self, mongo_db: Database[Any]) -> None:
        """测试软删除成功"""
        # Arrange
        repo = ReportRepository(mongo_db)
        data = ReportCreate(
            user_id=1,
            plan_name="周末徒步计划",
            trip_date="2024-03-16",
            overall_rating="推荐",
            content={"route": "香山"},
        )
        report_id = repo.create(data)

        # Act
        result = repo.delete(report_id, user_id=1)

        # Assert
        assert result is True

        # 验证软删除标记
        doc = mongo_db[repo.COLLECTION_NAME].find_one({"_id": ObjectId(report_id)})
        assert doc is not None
        assert doc["deleted_at"] is not None

    def test_delete_wrong_user(self, mongo_db: Database[Any]) -> None:
        """测试删除其他用户的报告失败"""
        # Arrange
        repo = ReportRepository(mongo_db)
        data = ReportCreate(
            user_id=1,
            plan_name="周末徒步计划",
            trip_date="2024-03-16",
            overall_rating="推荐",
            content={"route": "香山"},
        )
        report_id = repo.create(data)

        # Act - 使用错误的 user_id
        result = repo.delete(report_id, user_id=999)

        # Assert
        assert result is False

        # 验证未被删除
        doc = mongo_db[repo.COLLECTION_NAME].find_one({"_id": ObjectId(report_id)})
        assert doc is not None
        assert doc["deleted_at"] is None

    def test_list_excludes_deleted(self, mongo_db: Database[Any]) -> None:
        """测试列表不包含已删除报告"""
        # Arrange
        repo = ReportRepository(mongo_db)

        # 创建 3 个报告
        id1 = repo.create(
            ReportCreate(
                user_id=1,
                plan_name="计划1",
                trip_date="2024-03-16",
                overall_rating="推荐",
                content={},
            )
        )
        repo.create(
            ReportCreate(
                user_id=1,
                plan_name="计划2",
                trip_date="2024-03-17",
                overall_rating="推荐",
                content={},
            )
        )
        repo.create(
            ReportCreate(
                user_id=1,
                plan_name="计划3",
                trip_date="2024-03-18",
                overall_rating="推荐",
                content={},
            )
        )

        # 删除第一个
        repo.delete(id1, user_id=1)

        # Act
        items, total = repo.list_by_user(user_id=1)

        # Assert
        assert total == 2
        assert len(items) == 2
        assert all(item.plan_name != "计划1" for item in items)

    def test_hard_delete(self, mongo_db: Database[Any]) -> None:
        """测试物理删除"""
        # Arrange
        repo = ReportRepository(mongo_db)
        data = ReportCreate(
            user_id=1,
            plan_name="周末徒步计划",
            trip_date="2024-03-16",
            overall_rating="推荐",
            content={"route": "香山"},
        )
        report_id = repo.create(data)

        # Act
        result = repo.hard_delete(report_id)

        # Assert
        assert result is True

        # 验证已被物理删除
        doc = mongo_db[repo.COLLECTION_NAME].find_one({"_id": ObjectId(report_id)})
        assert doc is None

    def test_ensure_indexes(self, mongo_db: Database[Any]) -> None:
        """测试创建索引"""
        # Arrange
        repo = ReportRepository(mongo_db)

        # Act
        repo.ensure_indexes()

        # Assert
        indexes = mongo_db[repo.COLLECTION_NAME].list_indexes()
        index_names = [idx["name"] for idx in indexes]

        # 验证索引存在
        assert "user_id_1_created_at_-1" in index_names
        assert "deleted_at_1" in index_names
