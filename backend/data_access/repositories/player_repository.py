from typing import Optional, Dict, Any, List
import json
from backend.models.player import Player
from backend.data_access.db_manager import fetch_one, execute_query
from backend.utils.exceptions import PlayerNotFoundException
from backend.utils.logger import get_logger
import aiosqlite
from backend.config.settings import settings # Assuming settings contains DB path

logger = get_logger(__name__)

class PlayerRepository:
    """Repository for Player data."""

    def __init__(self):
        self.db_path = settings.database_path # Get DB path from settings

    async def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """
        Retrieves a player by their ID.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Ensure the table exists (for initial setup or testing)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    location_id TEXT,
                    party_pokemon_ids TEXT, -- Store as JSON string
                    box_pokemon_ids TEXT -- Store as JSON string
                    -- Add other columns as needed
                )
            """)
            await db.commit()

            cursor = await db.execute("SELECT player_id, name, location_id, party_pokemon_ids, box_pokemon_ids FROM players WHERE player_id = ?", (player_id,))
            row = await cursor.fetchone()
        if row:
                # Deserialize JSON strings back to lists
                party_ids = json.loads(row[3]) if row[3] else []
                box_ids = json.loads(row[4]) if row[4] else []
                return Player(player_id=row[0], name=row[1], location_id=row[2], party_pokemon_ids=party_ids, box_pokemon_ids=box_ids)
        return None

    async def save_player(self, player: Player) -> None:
        """
        Saves or updates a player's data.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Serialize lists to JSON strings before saving
            party_ids_json = json.dumps(player.party_pokemon_ids)
            box_ids_json = json.dumps(player.box_pokemon_ids)

            await db.execute(
                "UPDATE players SET name = ?, location_id = ?, party_pokemon_ids = ?, box_pokemon_ids = ? WHERE player_id = ?",
                (player.name, player.location_id, party_ids_json, box_ids_json, player.player_id)
            )
            await db.commit()
            logger.debug(f"Saved player data for {player.player_id}")

    async def create_player(self, player_id: str, name: str) -> Player:
        """
        Creates a new player with default values.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Ensure the table exists
            await db.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    location_id TEXT,
                    party_pokemon_ids TEXT, -- Store as JSON string
                    box_pokemon_ids TEXT -- Store as JSON string
                    -- Add other columns as needed
                )
            """)
            await db.commit()

            # Serialize empty lists to JSON strings for new player
            initial_party_ids_json = json.dumps([])
            initial_box_ids_json = json.dumps([])

            await db.execute(
                "INSERT INTO players (player_id, name, location_id, party_pokemon_ids, box_pokemon_ids) VALUES (?, ?, ?, ?, ?)",
                (player_id, name, "starting_location", initial_party_ids_json, initial_box_ids_json) # Default location
            )
            await db.commit()
            logger.info(f"Created new player: {name} ({player_id})")
            # Return the newly created Player object
            return Player(player_id=player_id, name=name, location_id="starting_location", party_pokemon_ids=[], box_pokemon_ids=[])

    async def create_table(self):
        """Creates the players table if it doesn't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    current_map_id INTEGER,
                    current_location_x INTEGER,
                    current_location_y INTEGER,
                    inventory TEXT, -- JSON string of inventory dict {item_id: quantity}
                    -- Add other player attributes here (e.g., money, battle_id if in battle)
                    battle_id TEXT, -- Add battle_id column
                    FOREIGN KEY (current_map_id) REFERENCES maps (map_id),
                    FOREIGN KEY (battle_id) REFERENCES battles (battle_id)
                )
            """)
            await db.commit()
        logger.info("Players table checked/created.")

    async def save_player(self, player: Player):
        """Saves or updates a player in the database."""
        async with aiosqlite.connect(self.db_path) as db:
            # Serialize inventory dict to JSON string
            inventory_json = json.dumps(player.inventory)

            await db.execute("""
                INSERT OR REPLACE INTO players (
                    player_id, name, current_map_id, current_location_x,
                    current_location_y, inventory, battle_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                player.player_id,
                player.name,
                player.current_map_id,
                player.current_location_x,
                player.current_location_y,
                inventory_json, # Include inventory JSON
                player.battle_id, # Include battle_id
            ))
            await db.commit()
        logger.debug(f"Player {player.player_id} saved.")

    async def get_player(self, player_id: str) -> Optional[Player]:
        """Retrieves a player by their ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM players WHERE player_id = ?", (player_id,))
            row = await cursor.fetchone()
            if row:
                player_data = dict(row)
                # Deserialize inventory JSON string to dict
                if player_data.get("inventory"):
                    player_data["inventory"] = json.loads(player_data["inventory"])
                else:
                    player_data["inventory"] = {} # Default to empty dict if NULL

                return Player.from_dict(player_data)
            return None

    async def get_player_by_name(self, name: str) -> Optional[Player]:
        """Retrieves a player by their name."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM players WHERE name = ?", (name,))
            row = await cursor.fetchone()
            if row:
                player_data = dict(row)
                # Deserialize inventory JSON string to dict
                if player_data.get("inventory"):
                    player_data["inventory"] = json.loads(player_data["inventory"])
                else:
                    player_data["inventory"] = {} # Default to empty dict if NULL
                return Player.from_dict(player_data)
            return None

    async def update_player_location(self, player_id: str, location_id: str) -> bool:
        """
        更新玩家的位置信息。
        
        Args:
            player_id: 玩家ID
            location_id: 新的位置ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE players SET location_id = ? WHERE player_id = ?",
                    (location_id, player_id)
                )
                await db.commit()
                logger.debug(f"更新玩家 {player_id} 位置到 {location_id}")
                return True
        except Exception as e:
            logger.error(f"更新玩家位置失败: {e}", exc_info=True)
            return False

    async def add_pokemon_to_party(self, player_id: str, pokemon_instance_id: int) -> bool:
        """
        将宝可梦添加到玩家队伍中。
        
        Args:
            player_id: 玩家ID
            pokemon_instance_id: 宝可梦实例ID
            
        Returns:
            bool: 添加是否成功
        """
        try:
            # 获取玩家数据
            player = await self.get_player_by_id(player_id)
            if not player:
                logger.error(f"无法找到玩家 {player_id}")
                return False
            
            # 检查队伍是否已满
            if len(player.party_pokemon_ids) >= 6:
                logger.warning(f"玩家 {player_id} 的队伍已满，无法添加宝可梦")
                return False
            
            # 检查宝可梦是否已经在队伍中
            if pokemon_instance_id in player.party_pokemon_ids:
                logger.warning(f"宝可梦 {pokemon_instance_id} 已经在玩家 {player_id} 的队伍中")
                return True
            
            # 检查宝可梦是否在仓库中，如果在则移除
            if pokemon_instance_id in player.box_pokemon_ids:
                player.box_pokemon_ids.remove(pokemon_instance_id)
            
            # 添加宝可梦到队伍
            player.party_pokemon_ids.append(pokemon_instance_id)
            
            # 保存玩家数据
            await self.save_player(player)
            logger.debug(f"将宝可梦 {pokemon_instance_id} 添加到玩家 {player_id} 的队伍中")
            return True
        except Exception as e:
            logger.error(f"添加宝可梦到队伍失败: {e}", exc_info=True)
            return False

    async def move_pokemon_to_box(self, player_id: str, pokemon_instance_id: int) -> bool:
        """
        将宝可梦从队伍移动到仓库。
        
        Args:
            player_id: 玩家ID
            pokemon_instance_id: 宝可梦实例ID
            
        Returns:
            bool: 移动是否成功
        """
        try:
            # 获取玩家数据
            player = await self.get_player_by_id(player_id)
            if not player:
                logger.error(f"无法找到玩家 {player_id}")
                return False
            
            # 检查宝可梦是否在队伍中
            if pokemon_instance_id not in player.party_pokemon_ids:
                logger.warning(f"宝可梦 {pokemon_instance_id} 不在玩家 {player_id} 的队伍中")
                return False
            
            # 从队伍中移除宝可梦
            player.party_pokemon_ids.remove(pokemon_instance_id)
            
            # 添加宝可梦到仓库
            player.box_pokemon_ids.append(pokemon_instance_id)
            
            # 保存玩家数据
            await self.save_player(player)
            logger.debug(f"将宝可梦 {pokemon_instance_id} 从玩家 {player_id} 的队伍移动到仓库")
            return True
        except Exception as e:
            logger.error(f"移动宝可梦到仓库失败: {e}", exc_info=True)
            return False

    async def update_player_items(self, player_id: str, items: Dict[int, int]) -> bool:
        """
        更新玩家的道具列表。
        
        Args:
            player_id: 玩家ID
            items: 更新后的道具字典，键为道具ID，值为数量
            
        Returns:
            bool: 更新是否成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 获取玩家当前数据
                cursor = await db.execute(
                    "SELECT items FROM players WHERE player_id = ?",
                    (player_id,)
                )
                row = await cursor.fetchone()
                
                if not row:
                    logger.error(f"无法找到玩家 {player_id}")
                    return False
                    
                # 更新道具数据
                items_json = json.dumps(items)
                await db.execute(
                    "UPDATE players SET items = ? WHERE player_id = ?",
                    (items_json, player_id)
                )
                await db.commit()
                logger.debug(f"更新玩家 {player_id} 的道具列表")
                return True
        except Exception as e:
            logger.error(f"更新玩家道具列表失败: {e}", exc_info=True)
            return False

    async def update_player_name(self, player_id: str, new_name: str) -> bool:
        """
        更新玩家的名称。
        
        Args:
            player_id: 玩家ID
            new_name: 新的玩家名称
            
        Returns:
            bool: 更新是否成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE players SET name = ? WHERE player_id = ?",
                    (new_name, player_id)
                )
                await db.commit()
                logger.debug(f"更新玩家 {player_id} 的名称为 {new_name}")
                return True
        except Exception as e:
            logger.error(f"更新玩家名称失败: {e}", exc_info=True)
            return False

    async def update_player_progress(self, player_id: str, progress_data: Dict[str, Any]) -> bool:
        """
        更新玩家的游戏进度数据。
        
        Args:
            player_id: 玩家ID
            progress_data: 进度数据字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 序列化进度数据
                progress_json = json.dumps(progress_data)
                
                await db.execute(
                    "UPDATE players SET progress = ? WHERE player_id = ?",
                    (progress_json, player_id)
                )
                await db.commit()
                logger.debug(f"更新玩家 {player_id} 的游戏进度")
                return True
        except Exception as e:
            logger.error(f"更新玩家游戏进度失败: {e}", exc_info=True)
            return False

