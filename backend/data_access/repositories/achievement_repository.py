import aiosqlite
from typing import List
from backend.models.achievement import Achievement # 假设您有 Achievement 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class AchievementRepository:
    @staticmethod
    async def insert_many(achievements: List[Achievement]) -> None:
        """
        批量插入成就数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 achievements 表有 achievement_id, name, description, type, goal, reward_item_id, reward_pet_id 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO achievements (achievement_id, name, description, type, goal, reward_item_id, reward_pet_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(a.achievement_id, a.name, a.description, a.type, a.goal, a.reward_item_id, a.reward_pet_id) for a in achievements]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 achievements 表相关的数据库操作方法 