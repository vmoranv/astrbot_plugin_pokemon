import aiosqlite
from typing import List, Dict, Any, Optional

from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.npc import Npc

logger = get_logger(__name__)

class NpcRepository:
    """
    Repository for npcs table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入 NPC 数据到数据库。

        Args:
            data_list: 包含 NPC 数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into npcs.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO npcs ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into npcs.")

    @staticmethod
    async def get_by_npc_id(npc_id: int) -> Optional[Npc]:
        """
        根据 npc_id 获取 NPC 条目。

        Args:
            npc_id: 要查找的 NPC ID。

        Returns:
            对应的 Npc 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM npcs WHERE npc_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (npc_id,))
            row = await cursor.fetchone()
            if row:
                return Npc.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[Npc]:
        """
        获取所有 NPC 条目。

        Returns:
            包含所有 Npc 模型实例的列表。
        """
        sql = "SELECT * FROM npcs"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [Npc.model_validate(row) for row in data]

    # 您可以在这里添加其他与 npcs 表相关的数据库操作方法 