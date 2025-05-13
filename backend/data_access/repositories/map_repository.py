import aiosqlite
from typing import List
from backend.models.map import Map # 假设您有 Map 模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class MapRepository:
    @staticmethod
    async def insert_many(maps: List[Map]) -> None:
        """
        批量插入地图数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 maps 表有 map_id, name, description, encounter_rate, background_image_path, npc_id, common_pet_id, common_pet_rate, rare_pet_id, rare_pet_rate, rare_pet_time 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO maps (map_id, name, description, encounter_rate, background_image_path, npc_id, common_pet_id, common_pet_rate, rare_pet_id, rare_pet_rate, rare_pet_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(m.map_id, m.name, m.description, m.encounter_rate, m.background_image_path, m.npc_id, m.common_pet_id, m.common_pet_rate, m.rare_pet_id, m.rare_pet_rate, m.rare_pet_time) for m in maps]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 maps 表相关的数据库操作方法 