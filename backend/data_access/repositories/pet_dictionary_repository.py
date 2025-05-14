import aiosqlite
from typing import List, Dict, Any, Optional
# 从 db_manager 导入 get_cursor，用于获取数据库游标
from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
# 导入新创建的 PetDictionaryData 模型
from backend.models.pet_dictionary import PetDictionary

logger = get_logger(__name__)

class PetDictionaryRepository:
    """
    Repository for pet_dictionary table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入宠物字典数据到数据库。

        Args:
            data_list: 包含宠物字典数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into pet_dictionary.")
            return

        # Assuming all dictionaries in the list have the same keys
        columns = data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO pet_dictionary ({column_names}) VALUES ({placeholders})"
        # 准备插入的值列表，确保顺序与列名一致
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into pet_dictionary.")

    @staticmethod
    async def get_by_race_id(race_id: int) -> Optional[PetDictionary]:
        """
        根据 race_id 获取宠物字典条目。

        Args:
            race_id: 要查找的宠物的种族 ID。

        Returns:
            对应的 PetDictionaryData 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM pet_dictionary WHERE race_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (race_id,))
            row = await cursor.fetchone()
            if row:
                # 使用 PetDictionary.model_validate() 将 Row 对象转换为模型实例
                return PetDictionary.model_validate(row)
            return None

    @staticmethod
    async def get_all() -> List[PetDictionary]:
        """
        获取所有宠物字典条目。

        Returns:
            包含所有 PetDictionaryData 模型实例的列表。
        """
        sql = "SELECT * FROM pet_dictionary"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            # 使用列表推导式和 PetDictionary.model_validate() 转换所有 Row 对象
            return [PetDictionary.model_validate(row) for row in data]

    # 您可以在这里添加其他方法来查询宠物字典数据，例如 get_by_race_id, get_all 等。
    # 例如：
    # @staticmethod
    # async def get_by_race_id(race_id: int) -> Optional[Dict[str, Any]]:
    #     """
    #     根据 race_id 获取宠物字典条目。
    #     """
    #     sql = "SELECT * FROM pet_dictionary WHERE race_id = ?"
    #     row = await get_cursor().execute(sql, (race_id,))
    #     data = await row.fetchone()
    #     return dict(data) if data else None