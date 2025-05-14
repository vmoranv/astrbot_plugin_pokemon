import aiosqlite
from typing import List, Dict, Any, Optional

from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.task import Task

logger = get_logger(__name__)

class TaskRepository:
    """
    Repository for tasks table data access.
    """
    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入任务数据到数据库。

        Args:
            data_list: 包含任务数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into tasks.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO tasks ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 tasks 表有 task_id, name, description, type, goal, reward_item_id, reward_pet_id 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                query, # 使用动态生成的 query
                values_to_insert # 使用动态生成的 values_to_insert
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理
        logger.info(f"Successfully inserted {len(data_list)} rows into tasks.")

    @staticmethod
    async def get_by_task_id(task_id: int) -> Optional[Task]:
        """
        根据 task_id 获取任务条目。

        Args:
            task_id: 要查找的任务 ID。

        Returns:
            对应的 Task 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM tasks WHERE task_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (task_id,))
            row = await cursor.fetchone()
            if row:
                return Task.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[Task]:
        """
        获取所有任务条目。

        Returns:
            包含所有 Task 模型实例的列表。
        """
        sql = "SELECT * FROM tasks"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [Task.model_validate(row) for row in data]

    # 您可以在这里添加其他与 tasks 表相关的数据库操作方法 