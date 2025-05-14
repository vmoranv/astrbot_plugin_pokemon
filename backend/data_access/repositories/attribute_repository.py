import aiosqlite
from typing import List, Dict, Any, Optional

# 从 db_manager 导入 get_cursor
from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.attribute import Attribute

logger = get_logger(__name__)

class AttributeRepository:
    """
    Repository for attributes table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入属性数据到数据库。

        Args:
            data_list: 包含属性数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into attributes.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO attributes ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into attributes.")

    @staticmethod
    async def get_by_attribute_id(attribute_id: int) -> Optional[Attribute]: 
        """
        根据 attribute_id 获取属性条目。

        Args:
            attribute_id: 要查找的属性 ID。

        Returns:
            对应的 Attribute 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM attributes WHERE attribute_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (attribute_id,))
            row = await cursor.fetchone()
            if row:
                return Attribute.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[Attribute]:
        """
        获取所有属性条目。

        Returns:
            包含所有 Attribute 模型实例的列表。
        """
        sql = "SELECT * FROM attributes"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [Attribute.model_validate(row) for row in data]

    # 您可以在这里添加其他与 attributes 表相关的数据库操作方法 