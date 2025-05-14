import aiosqlite
from typing import List, Dict, Any, Optional

from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.shop import Shop

logger = get_logger(__name__)

class ShopRepository:
    """
    Repository for shops table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入商店数据到数据库。

        Args:
            data_list: 包含商店数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into shops.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO shops ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into shops.")

    @staticmethod
    async def get_by_shop_id(shop_id: int) -> Optional[Shop]:
        """
        根据 shop_id 获取商店条目。

        Args:
            shop_id: 要查找的商店 ID。

        Returns:
            对应的 Shop 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM shops WHERE shop_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (shop_id,))
            row = await cursor.fetchone()
            if row:
                return Shop.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[Shop]:
        """
        获取所有商店条目。

        Returns:
            包含所有 Shop 模型实例的列表。
        """
        sql = "SELECT * FROM shops"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [Shop.model_validate(row) for row in data]

    # 您可以在这里添加其他与 shops 表相关的数据库操作方法 