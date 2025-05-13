import aiosqlite
from typing import List
from backend.models.pet_learnable_skill import PetLearnableSkill # 假设您有 PetLearnableSkill 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class PetLearnableSkillsRepository:
    @staticmethod
    async def insert_many(pet_learnable_skills: List[PetLearnableSkill]) -> None:
        """
        批量插入宝可梦可学习技能数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 pet_learnable_skills 表有 pet_id, skill_id, level_learned, learn_method 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO pet_learnable_skills (pet_id, skill_id, level_learned, learn_method) VALUES (?, ?, ?, ?)",
                [(pls.pet_id, pls.skill_id, pls.level_learned, pls.learn_method) for pls in pet_learnable_skills]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 pet_learnable_skills 表相关的数据库操作方法 