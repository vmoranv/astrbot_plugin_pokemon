import aiosqlite
from typing import List, Dict, Any, Optional

# 从 db_manager 导入 get_cursor
from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.pet_system import PetSystem # 请确保此模型文件存在

logger = get_logger(__name__)

class PetSystemRepository:
    """
    Repository for pet_system table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入宠物系统数据到数据库。

        Args:
            data_list: 包含宠物系统数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into pet_system.")
            return

        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO pet_system ({column_names}) VALUES ({placeholders})"
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into pet_system.")

    @staticmethod
    async def get_by_system_id(system_id: int) -> Optional[PetSystem]:
        """
        根据 system_id 获取宠物系统条目。

        Args:
            system_id: 要查找的系统 ID。

        Returns:
            对应的 PetSystem 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM pet_system WHERE system_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (system_id,))
            row = await cursor.fetchone()
            if row:
                return PetSystem.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[PetSystem]:
        """
        获取所有宠物系统条目。

        Returns:
            包含所有 PetSystem 模型实例的列表。
        """
        sql = "SELECT * FROM pet_system"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            return [PetSystem.model_validate(row) for row in data]

    # 您可以在这里添加其他与 pet_system 表相关的数据库操作方法

    # 您可以在这里添加其他与 pet_system_data 表相关的数据库操作方法（例如 get_by_id, get_all 等） 