import aiosqlite
from typing import List, Dict, Any, Optional

# 从 db_manager 导入 get_cursor
from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.achievement import Achievement

logger = get_logger(__name__)

class AchievementRepository:
    """
    Repository for achievements table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入成就数据到数据库。

        Args:
            data_list: 包含成就数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into achievements.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO achievements ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into achievements.")

    @staticmethod
    async def get_by_achievement_id(achievement_id: int) -> Optional[Any]: # 将 Any 替换为 Achievement
        """
        根据 achievement_id 获取成就条目。

        Args:
            achievement_id: 要查找的成就 ID。

        Returns:
            对应的 Achievement 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM achievements WHERE achievement_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (achievement_id,))
            row = await cursor.fetchone()
            if row:
                return Achievement.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[Achievement]:
        """
        获取所有成就条目。

        Returns:
            包含所有 Achievement 模型实例的列表。
        """
        sql = "SELECT * FROM achievements"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [Achievement.model_validate(row) for row in data]

    # 您可以在这里添加其他与 achievements 表相关的数据库操作方法 