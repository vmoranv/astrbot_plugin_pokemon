import aiosqlite
from typing import List
from backend.models.field_effect import FieldEffect # 假设您有 FieldEffect 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class FieldEffectRepository:
    @staticmethod
    async def insert_many(field_effects: List[FieldEffect]) -> None:
        """
        批量插入场地效果数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 field_effects 表有 field_effect_id, name, description, effect_logic_key, length 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO field_effects (field_effect_id, name, description, effect_logic_key, length) VALUES (?, ?, ?, ?, ?)",
                [(fe.field_effect_id, fe.name, fe.description, fe.effect_logic_key, fe.length) for fe in field_effects]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 field_effects 表相关的数据库操作方法 