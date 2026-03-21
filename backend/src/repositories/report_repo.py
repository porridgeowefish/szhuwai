"""
报告数据仓库
============
"""

from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId
from loguru import logger
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from src.schemas.report import ReportCreate, ReportDetail, ReportListItem


class ReportRepository:
    """报告数据仓库

    提供报告数据的 CRUD 操作。

    Attributes:
        collection: MongoDB 集合对象
    """

    COLLECTION_NAME = "reports"

    def __init__(self, db: Database[Any]) -> None:
        """初始化仓库

        Args:
            db: MongoDB 数据库对象
        """
        self.collection = db[self.COLLECTION_NAME]

    def create(self, data: ReportCreate) -> str:
        """创建报告

        Args:
            data: 创建报告的数据

        Returns:
            str: 创建的报告 ID
        """
        now = datetime.utcnow()
        doc = {
            "user_id": data.user_id,
            "plan_name": data.plan_name,
            "trip_date": data.trip_date,
            "overall_rating": data.overall_rating,
            "content": data.content,
            "created_at": now,
            "deleted_at": None,
        }

        result = self.collection.insert_one(doc)
        report_id = str(result.inserted_id)

        logger.info(f"创建报告成功: {report_id}, user_id={data.user_id}")
        return report_id

    def get_by_id(
        self, report_id: str, user_id: Optional[int] = None
    ) -> Optional[ReportDetail]:
        """获取报告详情

        Args:
            report_id: 报告 ID
            user_id: 如果提供，只返回该用户的报告（鉴权）

        Returns:
            报告详情或 None
        """
        try:
            oid = ObjectId(report_id)
        except InvalidId:
            return None

        query: dict[str, Any] = {"_id": oid, "deleted_at": None}

        # 如果提供 user_id，进行鉴权
        if user_id is not None:
            query["user_id"] = user_id

        doc = self.collection.find_one(query)
        if doc is None:
            return None

        return ReportDetail(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            plan_name=doc["plan_name"],
            trip_date=doc["trip_date"],
            overall_rating=doc["overall_rating"],
            content=doc["content"],
            created_at=doc["created_at"],
        )

    def list_by_user(
        self, user_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[ReportListItem], int]:
        """获取用户报告列表（分页）

        Args:
            user_id: 用户 ID
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            (报告列表, 总数)
        """
        # 查询条件：用户 ID 且未删除
        query = {"user_id": user_id, "deleted_at": None}

        # 获取总数
        total = self.collection.count_documents(query)

        # 分页查询
        skip = (page - 1) * page_size
        cursor = (
            self.collection.find(query)
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(page_size)
        )

        items: list[ReportListItem] = []
        for doc in cursor:
            items.append(
                ReportListItem(
                    id=str(doc["_id"]),
                    plan_name=doc["plan_name"],
                    trip_date=doc["trip_date"],
                    overall_rating=doc["overall_rating"],
                    created_at=doc["created_at"],
                )
            )

        return items, total

    def delete(self, report_id: str, user_id: int) -> bool:
        """软删除报告（鉴权）

        Args:
            report_id: 报告 ID
            user_id: 用户 ID（鉴权）

        Returns:
            是否删除成功
        """
        try:
            oid = ObjectId(report_id)
        except InvalidId:
            return False

        # 更新条件：ID 匹配、用户 ID 匹配、未删除
        result = self.collection.update_one(
            {"_id": oid, "user_id": user_id, "deleted_at": None},
            {"$set": {"deleted_at": datetime.utcnow()}},
        )

        success = int(result.modified_count) > 0
        if success:
            logger.info(f"软删除报告成功: {report_id}, user_id={user_id}")
        else:
            logger.warning(f"软删除报告失败: {report_id}, user_id={user_id}")

        return success

    def hard_delete(self, report_id: str) -> bool:
        """物理删除报告（管理员）

        Args:
            report_id: 报告 ID

        Returns:
            是否删除成功
        """
        try:
            oid = ObjectId(report_id)
        except InvalidId:
            return False

        result = self.collection.delete_one({"_id": oid})
        success = int(result.deleted_count) > 0

        if success:
            logger.info(f"物理删除报告成功: {report_id}")
        else:
            logger.warning(f"物理删除报告失败: {report_id}")

        return success

    def ensure_indexes(self) -> None:
        """创建索引

        创建用户查询和软删除过滤所需的索引。
        """
        # 用户 ID + 创建时间复合索引（用于用户报告列表查询）
        self.collection.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        # 软删除索引（用于过滤已删除报告）
        self.collection.create_index([("deleted_at", ASCENDING)])

        logger.debug("报告集合索引创建完成")
