import aiosqlite
from typing import List
from backend.models.dialog import Dialog # 假设您有 Dialog 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class DialogRepository:
    @staticmethod
    async def insert_many(dialogs: List[Dialog]) -> None:
        """
        批量插入对话数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 dialogs 表有 dialog_id, text, next_dialog_id, options 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO dialogs (dialog_id, text, next_dialog_id, options) VALUES (?, ?, ?, ?)",
                [(d.dialog_id, d.text, d.next_dialog_id, d.options) for d in dialogs]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 dialogs 表相关的数据库操作方法 