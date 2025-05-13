import aiosqlite
from typing import List
from backend.models.pet_system_data import PetSystemData # 假设您有这个模型
# from backend.data_access.database import get_db # 假设您有获取数据库连接的函数
from backend.data_access.db_manager import get_cursor # 从 db_manager 导入 get_cursor

class PetSystemRepository:
    @staticmethod
    async def insert_many(pet_systems: List[PetSystemData]) -> None:
        """
        批量插入宠物系统数据到数据库。
        """
        # async with get_db() as db: # 修改为使用 get_cursor
        async with get_cursor() as cursor:
            # 假设 pet_system_data 表有 system_id, system_name, system_description, system_effect 列
            await cursor.executemany( # 使用 cursor 对象执行操作
                "INSERT INTO pet_system_data (system_id, system_name, system_description, system_effect) VALUES (?, ?, ?, ?)",
                [(ps.system_id, ps.system_name, ps.system_description, ps.system_effect) for ps in pet_systems]
            )
            # await db.commit() # commit 已经在 get_cursor 上下管理器中处理

    # 您可以在这里添加其他与 pet_system_data 表相关的数据库操作方法（例如 get_by_id, get_all 等） 