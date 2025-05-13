import aiosqlite
from typing import List
from backend.models.item import Item # 假设您有 Item 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class ItemRepository:
    @staticmethod
    async def insert_many(items: List[Item]) -> None:
        """
        批量插入物品数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 items 表有 item_id, name, description, effect_logic_key, category 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO items (item_id, name, description, effect_logic_key, category) VALUES (?, ?, ?, ?, ?)",
                [(item.item_id, item.name, item.description, item.effect_logic_key, item.category) for item in items]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 items 表相关的数据库操作方法 