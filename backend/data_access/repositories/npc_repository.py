import aiosqlite
from typing import List
from backend.models.npc import NPC # 假设您有 NPC 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class NpcRepository:
    @staticmethod
    async def insert_many(npcs: List[NPC]) -> None:
        """
        批量插入 NPC 数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 npcs 表有 npc_id, name, description, dialog_id 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO npcs (npc_id, name, description, dialog_id) VALUES (?, ?, ?, ?)",
                [(npc.npc_id, npc.name, npc.description, npc.dialog_id) for npc in npcs]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 npcs 表相关的数据库操作方法 