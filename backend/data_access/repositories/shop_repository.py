import aiosqlite
from typing import List
from backend.models.shop import Shop # 假设您有 Shop 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class ShopRepository:
    @staticmethod
    async def insert_many(shops: List[Shop]) -> None:
        """
        批量插入商店数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 shops 表有 shop_id, name, description, inventory 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO shops (shop_id, name, description, inventory) VALUES (?, ?, ?, ?)",
                [(s.shop_id, s.name, s.description, s.inventory) for s in shops] # 假设 inventory 是可以直接存储的格式
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 shops 表相关的数据库操作方法 