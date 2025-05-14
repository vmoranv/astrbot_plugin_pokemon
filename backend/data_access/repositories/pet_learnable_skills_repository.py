import aiosqlite
from typing import List, Dict, Any, Optional
# from backend.models.pet_learnable_skill import PetLearnableSkill # 假设您有 PetLearnableSkill 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor
from backend.utils.logger import get_logger # 导入 logger
from backend.models.pet_learnable_skill import PetLearnableSkill # 导入 PetLearnableSkill 模型

logger = get_logger(__name__) # 初始化 logger

class PetLearnableSkillsRepository:
    """
    Repository for pet_learnable_skills table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入宠物可学习技能数据到数据库。

        Args:
            data_list: 包含宠物可学习技能数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into pet_learnable_skills.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO pet_learnable_skills ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into pet_learnable_skills.")

    @staticmethod
    async def get_by_race_id_and_skill_id_and_learn_method(
        race_id: int, skill_id: int, learn_method: str
    ) -> Optional[PetLearnableSkill]:
        """
        根据 race_id, skill_id 和 learn_method 获取宠物可学习技能条目。

        Args:
            race_id: 种族 ID。
            skill_id: 技能 ID。
            learn_method: 学习方法。

        Returns:
            对应的 PetLearnableSkill 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM pet_learnable_skills WHERE race_id = ? AND skill_id = ? AND learn_method = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (race_id, skill_id, learn_method))
            row = await cursor.fetchone()
            if row:
                return PetLearnableSkill.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[PetLearnableSkill]:
        """
        获取所有宠物可学习技能条目。

        Returns:
            包含所有 PetLearnableSkill 模型实例的列表。
        """
        sql = "SELECT * FROM pet_learnable_skills"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [PetLearnableSkill.model_validate(row) for row in data]

    # 您可以在这里添加其他与 pet_learnable_skills 表相关的数据库操作方法 