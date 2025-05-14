import aiosqlite
from typing import List, Dict, Any, Optional

from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.field_effect import FieldEffect

logger = get_logger(__name__)

class FieldEffectRepository:
    """
    Repository for field_effects table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入场地效果数据到数据库。

        Args:
            data_list: 包含场地效果数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into field_effects.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO field_effects ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into field_effects.")

    @staticmethod
    async def get_by_field_effect_id(field_effect_id: int) -> Optional[FieldEffect]:
        """
        根据 field_effect_id 获取场地效果条目。

        Args:
            field_effect_id: 要查找的场地效果 ID。

        Returns:
            对应的 FieldEffect 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM field_effects WHERE field_effect_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (field_effect_id,))
            row = await cursor.fetchone()
            if row:
                return FieldEffect.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[FieldEffect]:
        """
        获取所有场地效果条目。

        Returns:
            包含所有 FieldEffect 模型实例的列表。
        """
        sql = "SELECT * FROM field_effects"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [FieldEffect.model_validate(row) for row in data]

    # 您可以在这里添加其他与 field_effects 表相关的数据库操作方法 