import aiosqlite
from typing import List
from backend.models.task import Task # 假设您有 Task 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class TaskRepository:
    @staticmethod
    async def insert_many(tasks: List[Task]) -> None:
        """
        批量插入任务数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 tasks 表有 task_id, name, description, type, goal, reward_item_id, reward_pet_id 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO tasks (task_id, name, description, type, goal, reward_item_id, reward_pet_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(t.task_id, t.name, t.description, t.type, t.goal, t.reward_item_id, t.reward_pet_id) for t in tasks]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 tasks 表相关的数据库操作方法 