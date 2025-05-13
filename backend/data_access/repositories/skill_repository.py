import aiosqlite
from typing import List
from backend.models.skill import Skill # 假设您有 Skill 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class SkillRepository:
    @staticmethod
    async def insert_many(skills: List[Skill]) -> None:
        """
        批量插入技能数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 skills 表有 skill_id, name, type, power, accuracy, critical_rate, pp, category, priority, target_type, effect_logic_key, description 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO skills (skill_id, name, type, power, accuracy, critical_rate, pp, category, priority, target_type, effect_logic_key, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(s.skill_id, s.name, s.type, s.power, s.accuracy, s.critical_rate, s.pp, s.category, s.priority, s.target_type, s.effect_logic_key, s.description) for s in skills]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 skills 表相关的数据库操作方法 