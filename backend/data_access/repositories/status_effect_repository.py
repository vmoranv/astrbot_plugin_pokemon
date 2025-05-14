import aiosqlite
from typing import List, Dict, Any, Optional

from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.status_effect import StatusEffect

logger = get_logger(__name__)

class StatusEffectRepository:
    """
    Repository for status_effects table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入状态效果数据到数据库。

        Args:
            data_list: 包含状态效果数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into status_effects.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO status_effects ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into status_effects.")

    @staticmethod
    async def get_by_status_effect_id(status_effect_id: int) -> Optional[StatusEffect]:
        """
        根据 status_effect_id 获取状态效果条目。

        Args:
            status_effect_id: 要查找的状态效果 ID。

        Returns:
            对应的 StatusEffect 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM status_effects WHERE status_effect_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (status_effect_id,))
            row = await cursor.fetchone()
            if row:
                return StatusEffect.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[StatusEffect]:
        """
        获取所有状态效果条目。

        Returns:
            包含所有 StatusEffect 模型实例的列表。
        """
        sql = "SELECT * FROM status_effects"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [StatusEffect.model_validate(row) for row in data]

    # 您可以在这里添加其他与 status_effects 表相关的数据库操作方法