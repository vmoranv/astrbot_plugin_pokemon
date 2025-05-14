import aiosqlite
from typing import List, Dict, Any, Optional

from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.event import Event

logger = get_logger(__name__)

class EventRepository:
    """
    Repository for events table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入事件数据到数据库。

        Args:
            data_list: 包含事件数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into events.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO events ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into events.")

    @staticmethod
    async def get_by_event_id(event_id: int) -> Optional[Event]:
        """
        根据 event_id 获取事件条目。

        Args:
            event_id: 要查找的事件 ID。

        Returns:
            对应的 Event 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM events WHERE event_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (event_id,))
            row = await cursor.fetchone()
            if row:
                return Event.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[Event]:
        """
        获取所有事件条目。

        Returns:
            包含所有 Event 模型实例的列表。
        """
        sql = "SELECT * FROM events"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [Event.model_validate(row) for row in data]

    # 您可以在这里添加其他与 events 表相关的数据库操作方法 