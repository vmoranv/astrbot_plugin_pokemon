from typing import Optional, Dict, Any
from backend.models.player import Player
from backend.data_access.repositories.map_repository import MapRepository # 导入 MapRepository
from backend.data_access.repositories.player_repository import PlayerRepository # 导入 PlayerRepository (假设存在)
from backend.data_access.repositories.metadata_repository import MetadataRepository
from backend.utils.exceptions import PlayerNotFoundException, MapNotFoundException, LocationNotFoundException # 导入 MapNotFoundException
from backend.utils.logger import get_logger
from backend.models.map import Map # 导入 Map 模型

logger = get_logger(__name__)

class MapService:
    """Service for Map related business logic."""

    def __init__(self):
        self.map_repo = MapRepository() # 实例化 MapRepository
        self.player_repo = PlayerRepository() # 实例化 PlayerRepository (假设存在)
        self.metadata_repo = MetadataRepository()
        # self.player_service = PlayerService() # Example dependency

    async def get_map_data(self, map_id: int) -> Optional[Map]: # 将 map_id 类型提示改为 int
        """
        Retrieves map data by map ID.
        """
        return await self.map_repo.get_by_map_id(map_id) # 直接传递 int 类型的 map_id


    async def get_location_name(self, location_id: str) -> str:
        """
        Retrieves the name of a location from metadata.
        """
        location_data = await self.metadata_repo.get_location_data(location_id)
        if location_data and 'name' in location_data:
            return location_data['name']
        else:
            logger.warning(f"Location name not found for location_id: {location_id}. Using ID as name.")
            return location_id

    async def move_player_to_location(self, player_id: str, location_id: str) -> str:
        """
        Moves a player to a new location.
        Raises PlayerNotFoundException if player not found.
        Raises LocationNotFoundException if location metadata not found.
        Returns a message indicating the result.
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        # Check if location exists in metadata
        location_data = await self.metadata_repo.get_location_data(location_id)
        if not location_data:
            raise LocationNotFoundException(f"Location metadata not found for location_id: {location_id}")

        player.location_id = location_id
        await self.player_repo.save_player(player)

        location_name = await self.get_location_name(location_id)
        logger.info(f"Player {player_id} moved to location: {location_id}")
        return f"你移动到了 {location_name}。"

    async def move_player_to_map(self, player: Player, target_map_id: str) -> str:
        """
        Moves a player to a new map if it's adjacent to their current location.
        Returns a message describing the result.
        """
        logger.info(f"Attempting to move player {player.player_id} from {player.location_id} to {target_map_id}")

        try:
            # 1. Get current map data for the player's location.
            # 确保 player.location_id 是整数类型，如果不是，需要在这里转换或在 Player 模型中处理
            if player.location_id is None:
                 return "你当前位置未知，无法移动。" # 处理玩家位置未知的情况

            try:
                current_map_id_int = int(player.location_id)
            except ValueError:
                 logger.error(f"Invalid current map ID format for player {player.player_id}: {player.location_id}")
                 return "你的当前位置数据异常，无法移动。"

            current_map = await self.get_map_data(current_map_id_int) # 传递整数 ID
            if not current_map:
                logger.warning(f"Current map {player.location_id} not found for player {player.player_id}.")
                # 理论上玩家应该总在一个有效的地图上，如果出现这种情况可能是数据问题
                raise MapNotFoundException(f"Current map {player.location_id} not found.")

            # 2. Get target map data to confirm it exists.
            try:
                target_map_id_int = int(target_map_id)
            except ValueError:
                 logger.error(f"Invalid target map ID format: {target_map_id}")
                 return f"错误: 目标地图 ID 格式无效。"

            target_map = await self.get_map_data(target_map_id_int) # 传递整数 ID
            if not target_map:
                logger.warning(f"Target map {target_map_id} not found for player {player.player_id}.")
                raise MapNotFoundException(f"目标地图 {target_map_id} 不存在。")

            # 3. Check if target_map_id is in the adjacent_maps list of the current map.
            # adjacent_maps 字段在 Map 模型中应该是存储相邻地图ID的列表或类似结构
            # 假设 Map.adjacent_maps 是一个包含相邻地图ID（整数）的列表

            if target_map_id_int in current_map.adjacent_maps:
                # 4. Update player's location (update Player model and save via PlayerRepository).
                # 假设 PlayerRepository 有一个 update_player_location 方法
                # await self.player_service.update_player_location(player.player_id, target_map_id) # Assuming method in PlayerService
                # 修改玩家对象的 location_id
                player.location_id = target_map_id_int # 将玩家位置更新为整数 ID
                # 调用 PlayerRepository 更新玩家数据
                await self.player_repo.save_player(player) # 修改为调用 save_player 方法

                logger.info(f"Player {player.player_id} successfully moved to {target_map_id}")
                return f"你到达了 {target_map.name}。" # 使用目标地图的名称

            else:
                logger.info(f"Player {player.player_id} attempted to move from {current_map.name} to non-adjacent {target_map.name}.")
                return f"你无法从 {current_map.name} 前往 {target_map.name}。" # 使用地图名称

        except MapNotFoundException as e:
            return f"错误：{e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred while handling player movement for {player.player_id}: {e}", exc_info=True)
            return "移动时发生未知错误。"

    # Add other map related business logic methods (e.g., get_map_description, list_adjacent_maps)
    async def get_map_description(self, map_id: int) -> str: # 将 map_id 类型提示改为 int
        """
        Retrieves the description of a map.
        """
        map_data = await self.get_map_data(map_id)
        if map_data:
            return map_data.description
        else:
            return "未知区域。"

    async def list_adjacent_maps(self, map_id: int) -> str: # 将 map_id 类型提示改为 int
        """
        Lists the names of adjacent maps.
        """
        current_map = await self.get_map_data(map_id)
        if not current_map:
            return "当前区域信息未知。"

        if not current_map.adjacent_maps:
            return f"{current_map.name} 没有相邻区域。"

        adjacent_map_names = []
        for adj_map_id in current_map.adjacent_maps:
            try:
                # get_map_data 现在期望整数 ID
                adj_map_data = await self.get_map_data(adj_map_id)
                if adj_map_data:
                    adjacent_map_names.append(adj_map_data.name)
                else:
                     # 如果相邻地图 ID 在数据库中找不到对应的地图
                     logger.warning(f"Adjacent map ID {adj_map_id} for map {map_id} not found in database.")
                     adjacent_map_names.append(f"未知区域 (ID: {adj_map_id})")
            except Exception as e:
                logger.warning(f"Could not retrieve data for adjacent map ID {adj_map_id} (from map {map_id}): {e}")
                adjacent_map_names.append(f"未知区域 (ID: {adj_map_id})")


        if adjacent_map_names:
            return f"{current_map.name} 的相邻区域有: {', '.join(adjacent_map_names)}。"
        else:
             return f"{current_map.name} 的相邻区域信息无法获取。"
