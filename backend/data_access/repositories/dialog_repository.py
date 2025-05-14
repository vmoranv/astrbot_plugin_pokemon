import aiosqlite
from typing import List, Dict, Any, Optional

from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.dialog import Dialog

logger = get_logger(__name__)

class DialogRepository:
    """
    Repository for dialogs table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入对话数据到数据库。

        Args:
            data_list: 包含对话数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into dialogs.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO dialogs ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into dialogs.")

    @staticmethod
    async def get_by_dialog_id(dialog_id: int) -> Optional[Dialog]:
        """
        根据 dialog_id 获取对话条目。

        Args:
            dialog_id: 要查找的对话 ID。

        Returns:
            对应的 Dialog 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM dialogs WHERE dialog_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (dialog_id,))
            row = await cursor.fetchone()
            if row:
                return Dialog.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[Dialog]:
        """
        获取所有对话条目。

        Returns:
            包含所有 Dialog 模型实例的列表。
        """
        sql = "SELECT * FROM dialogs"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [Dialog.model_validate(row) for row in data]

    # 您可以在这里添加其他与 dialogs 表相关的数据库操作方法 