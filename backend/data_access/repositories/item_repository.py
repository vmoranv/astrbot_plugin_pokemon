import aiosqlite
from typing import List, Dict, Any, Optional

from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.item import Item

logger = get_logger(__name__)

class ItemRepository:
    """
    Repository for items table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入道具数据到数据库。

        Args:
            data_list: 包含道具数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into items.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO items ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into items.")

    @staticmethod
    async def get_by_item_id(item_id: int) -> Optional[Item]:
        """
        根据 item_id 获取道具条目。

        Args:
            item_id: 要查找的道具 ID。

        Returns:
            对应的 Item 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM items WHERE item_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (item_id,))
            row = await cursor.fetchone()
            if row:
                return Item.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[Item]:
        """
        获取所有道具条目。

        Returns:
            包含所有 Item 模型实例的列表。
        """
        sql = "SELECT * FROM items"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [Item.model_validate(row) for row in data]

    # 您可以在这里添加其他与 items 表相关的数据库操作方法 