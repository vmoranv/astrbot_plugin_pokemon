import aiosqlite
import json # 导入 json 模块
from typing import List, Dict, Any, Optional

from backend.data_access.db_manager import get_cursor
from backend.utils.logger import get_logger
from backend.models.map import Map

logger = get_logger(__name__)

class MapRepository:
    """
    Repository for maps table data access.
    """

    @staticmethod
    async def insert_many(data_list: List[Dict[str, Any]]) -> None:
        """
        批量插入地图数据到数据库。

        Args:
            data_list: 包含地图数据的字典列表。
        """
        if not data_list:
            logger.info("No data to insert into maps.")
            return

        # 在插入前将 adjacent_maps 列表序列化为 JSON 字符串
        processed_data_list = []
        for item in data_list:
            processed_item = item.copy() # 创建副本以避免修改原始数据
            if 'adjacent_maps' in processed_item and isinstance(processed_item['adjacent_maps'], list):
                processed_item['adjacent_maps'] = json.dumps(processed_item['adjacent_maps'])
            else:
                 # 如果 adjacent_maps 不存在或不是列表，将其设置为 JSON 空列表字符串
                 processed_item['adjacent_maps'] = json.dumps([])
            processed_data_list.append(processed_item)


        columns = processed_data_list[0].keys()
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        query = f"INSERT INTO maps ({column_names}) VALUES ({placeholders})"
        # 准备插入的值列表，确保顺序与列名一致
        values_to_insert = [[item.get(col) for col in columns] for item in processed_data_list]


        async with get_cursor() as cursor:
            await cursor.executemany(query, values_to_insert)
        logger.info(f"Successfully inserted {len(data_list)} rows into maps.")

    @staticmethod
    async def get_by_map_id(map_id: int) -> Optional[Map]:
        """
        根据 map_id 获取地图条目。

        Args:
            map_id: 要查找的地图 ID。

        Returns:
            对应的 Map 模型实例，如果不存在则返回 None。
        """
        sql = "SELECT * FROM maps WHERE map_id = ?"
        async with get_cursor() as cursor:
            await cursor.execute(sql, (map_id,))
            row = await cursor.fetchone()
            if row:
                row_dict = dict(row)
                # 从数据库读取时将 adjacent_maps JSON 字符串反序列化为 Python 列表
                if 'adjacent_maps' in row_dict and row_dict['adjacent_maps'] is not None:
                    try:
                        row_dict['adjacent_maps'] = json.loads(row_dict['adjacent_maps'])
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode adjacent_maps JSON for map ID {map_id}. Setting to empty list.")
                        row_dict['adjacent_maps'] = []
                else:
                    row_dict['adjacent_maps'] = [] # 如果 adjacent_maps 为 None 或不存在，默认为空列表

                return Map.from_dict(row_dict)
            return None

    @staticmethod
    async def get_all() -> List[Map]:
        """
        获取所有地图条目。

        Returns:
            包含所有 Map 模型实例的列表。
        """
        sql = "SELECT * FROM maps"
        async with get_cursor() as cursor:
            await cursor.execute(sql)
            data = await cursor.fetchall()
            # 遍历所有行，对 adjacent_maps 进行反序列化
            maps_list = []
            for row in data:
                row_dict = dict(row)
                if 'adjacent_maps' in row_dict and row_dict['adjacent_maps'] is not None:
                    try:
                        row_dict['adjacent_maps'] = json.loads(row_dict['adjacent_maps'])
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode adjacent_maps JSON for map ID {row_dict.get('map_id')}. Skipping this map.")
                        continue # 跳过解码失败的行
                else:
                    row_dict['adjacent_maps'] = []

                maps_list.append(Map.from_dict(row_dict))
            return maps_list

    # 您可以在这里添加其他与 maps 表相关的数据库操作方法
    # 例如，一个用于更新单个地图条目的方法
    @staticmethod
    async def update_map(map_data: Map) -> None:
        """
        Updates a map entry in the database.

        Args:
            map_data: The Map model instance to update.
        """
        sql = """
        UPDATE maps
        SET name = ?, description = ?, encounter_rate = ?, background_image_path = ?,
            common_pet_id = ?, common_pet_rate = ?, rare_pet_id = ?, rare_pet_rate = ?,
            rare_pet_time = ?, adjacent_maps = ?
        WHERE map_id = ?
        """
        # 在更新前将 adjacent_maps 列表序列化为 JSON 字符串
        adjacent_maps_json = json.dumps(map_data.adjacent_maps) if map_data.adjacent_maps is not None else json.dumps([])

        params = (
            map_data.name,
            map_data.description,
            map_data.encounter_rate,
            map_data.background_image_path,
            map_data.common_pet_id,
            map_data.common_pet_rate,
            map_data.rare_pet_id,
            map_data.rare_pet_rate,
            map_data.rare_pet_time,
            adjacent_maps_json, # 插入 JSON 字符串
            map_data.map_id,
        )
        async with get_cursor() as cursor:
            await cursor.execute(sql, params)
        logger.debug(f"Updated map: {map_data.map_id}") 