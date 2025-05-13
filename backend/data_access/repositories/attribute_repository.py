import aiosqlite
from typing import List
from backend.models.attribute import Attribute # 假设您有 Attribute 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class AttributeRepository:
    @staticmethod
    async def insert_many(attributes: List[Attribute]) -> None:
        """
        批量插入属性数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 attributes 表有 attribute_id, name, description 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO attributes (attribute_id, name, description) VALUES (?, ?, ?)",
                [(a.attribute_id, a.name, a.description) for a in attributes]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 attributes 表相关的数据库操作方法（例如 get_by_id, get_all 等） 