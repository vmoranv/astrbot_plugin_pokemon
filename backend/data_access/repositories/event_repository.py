import aiosqlite
from typing import List
from backend.models.event import Event # 假设您有 Event 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class EventRepository:
    @staticmethod
    async def insert_many(events: List[Event]) -> None:
        """
        批量插入事件数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 events 表有 event_id, name, description, reward_item_id, dialog_id, pet_id 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO events (event_id, name, description, reward_item_id, dialog_id, pet_id) VALUES (?, ?, ?, ?, ?, ?)",
                [(e.event_id, e.name, e.description, e.reward_item_id, e.dialog_id, e.pet_id) for e in events]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 events 表相关的数据库操作方法 