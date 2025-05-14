import aiosqlite
from typing import List, Dict, Any, Optional

from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.map import Map

logger = get_logger(__name__)

class MapRepository:
    """
    Repository for maps table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入地图数据到数据库。

        Args:
            data_list: 包含地图数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into maps.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO maps ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into maps.")

    @staticmethod
    async def get_by_map_id(map_id: int) -> Optional[Map]:
        """
        根据 map_id 获取地图条目。

        Args:
            map_id: 要查找的地图 ID。

        Returns:
            对应的 Map 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM maps WHERE map_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (map_id,))
            row = await cursor.fetchone()
            if row:
                return Map.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[Map]:
        """
        获取所有地图条目。

        Returns:
            包含所有 Map 模型实例的列表。
        """
        sql = "SELECT * FROM maps"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [Map.model_validate(row) for row in data]

    # 您可以在这里添加其他与 maps 表相关的数据库操作方法 