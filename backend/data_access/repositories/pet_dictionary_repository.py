import aiosqlite
from typing import List, Dict, Any
# 从 db_manager 导入 get_cursor，用于获取数据库游标
from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger

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

        # Prepare the data for executemany
        values_to_insert = [[item[col] for col in columns] for item in data_list]

        async with get_cursor() as cursor:
            try:
                # Construct the INSERT query dynamically based on dictionary keys
                query = f"INSERT INTO pet_dictionary ({column_names}) VALUES ({placeholders})"
                await cursor.executemany(query, values_to_insert)
                # The commit is handled by the get_cursor context manager
                logger.info(f"Successfully inserted {len(data_list)} entries into pet_dictionary.")
            except aiosqlite.Error as e:
                logger.error(f"Database error during bulk insert into pet_dictionary: {e}")
                # Depending on your error handling, you might want to raise
                raise
            except Exception as e:
                logger.error(f"An unexpected error occurred during pet_dictionary insert: {e}")
                raise

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