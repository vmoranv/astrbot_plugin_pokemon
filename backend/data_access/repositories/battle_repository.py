from typing import Optional, Dict, Any, List, Tuple
import json
import aiosqlite
from backend.models.battle import Battle
from backend.utils.exceptions import BattleNotFoundException
from backend.utils.logger import get_logger
from backend.config.settings import settings

logger = get_logger(__name__)

class BattleRepository:
    """仓库类，负责Battle数据的存储和检索。"""

    def __init__(self):
        self.db_path = settings.database_path

    async def get_active_battle(self, player_id: str) -> Optional[Battle]:
        """
        获取玩家当前的活跃战斗。
        
        Args:
            player_id: 玩家ID
            
        Returns:
            Optional[Battle]: 如果存在活跃战斗，则返回战斗对象；否则返回None
        """
        async with aiosqlite.connect(self.db_path) as db:
            # 确保表存在
            await db.execute("""
                CREATE TABLE IF NOT EXISTS battles (
                    battle_id TEXT PRIMARY KEY,
                    player_id TEXT NOT NULL,
                    battle_type TEXT NOT NULL,
                    player_pokemon_ids TEXT NOT NULL, -- 存储为JSON字符串
                    opponent_pokemon_ids TEXT NOT NULL, -- 存储为JSON字符串
                    current_player_pokemon_id INTEGER,
                    current_opponent_pokemon_id INTEGER,
                    battle_state TEXT NOT NULL, -- 例如 "active", "completed", "player_won", "player_lost"
                    turn_number INTEGER DEFAULT 1,
                    battle_data TEXT, -- 存储其他战斗数据为JSON字符串
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
            
            # 查询玩家当前活跃的战斗
            cursor = await db.execute(
                "SELECT * FROM battles WHERE player_id = ? AND battle_state = 'active' ORDER BY updated_at DESC LIMIT 1",
                (player_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                # 将数据库行转换为Battle对象
                return await self._row_to_battle(row)
            
            return None

    async def save_battle(self, battle: Battle) -> None:
        """
        保存或更新战斗数据。
        
        Args:
            battle: 要保存的战斗对象
        """
        async with aiosqlite.connect(self.db_path) as db:
            # 检查战斗是否已存在
            cursor = await db.execute(
                "SELECT 1 FROM battles WHERE battle_id = ?",
                (battle.battle_id,)
            )
            exists = await cursor.fetchone() is not None
            
            # 准备要保存的数据
            player_pokemon_ids = json.dumps(battle.player_pokemon_ids)
            opponent_pokemon_ids = json.dumps(battle.opponent_pokemon_ids)
            battle_data = json.dumps(battle.battle_data) if battle.battle_data else None
            
            if exists:
                # 更新现有战斗
                await db.execute(
                    """
                    UPDATE battles SET
                        battle_type = ?,
                        player_pokemon_ids = ?,
                        opponent_pokemon_ids = ?,
                        current_player_pokemon_id = ?,
                        current_opponent_pokemon_id = ?,
                        battle_state = ?,
                        turn_number = ?,
                        battle_data = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE battle_id = ?
                    """,
                    (
                        battle.battle_type,
                        player_pokemon_ids,
                        opponent_pokemon_ids,
                        battle.current_player_pokemon_id,
                        battle.current_opponent_pokemon_id,
                        battle.battle_state,
                        battle.turn_number,
                        battle_data,
                        battle.battle_id
                    )
                )
            else:
                # 创建新战斗
                await db.execute(
                    """
                    INSERT INTO battles (
                        battle_id,
                        player_id,
                        battle_type,
                        player_pokemon_ids,
                        opponent_pokemon_ids,
                        current_player_pokemon_id,
                        current_opponent_pokemon_id,
                        battle_state,
                        turn_number,
                        battle_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        battle.battle_id,
                        battle.player_id,
                        battle.battle_type,
                        player_pokemon_ids,
                        opponent_pokemon_ids,
                        battle.current_player_pokemon_id,
                        battle.current_opponent_pokemon_id,
                        battle.battle_state,
                        battle.turn_number,
                        battle_data
                    )
                )
            
            await db.commit()
            logger.debug(f"保存战斗 {battle.battle_id} 的数据 (状态: {battle.battle_state})")

    async def delete_battle(self, battle_id: str) -> bool:
        """
        删除战斗数据。
        
        Args:
            battle_id: 要删除的战斗ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM battles WHERE battle_id = ?", (battle_id,))
                await db.commit()
                logger.debug(f"删除战斗 {battle_id} 的数据")
                return True
        except Exception as e:
            logger.error(f"删除战斗数据失败: {e}", exc_info=True)
            return False

    async def get_battle_history(self, player_id: str, limit: int = 10) -> List[Battle]:
        """
        获取玩家的战斗历史记录。
        
        Args:
            player_id: 玩家ID
            limit: 返回记录的最大数量
            
        Returns:
            List[Battle]: 战斗历史记录列表
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM battles WHERE player_id = ? AND battle_state != 'active' ORDER BY updated_at DESC LIMIT ?",
                (player_id, limit)
            )
            rows = await cursor.fetchall()
            
            battles = []
            for row in rows:
                battle = await self._row_to_battle(row)
                if battle:
                    battles.append(battle)
            
            return battles

    async def _row_to_battle(self, row) -> Battle:
        """
        将数据库行转换为Battle对象。
        
        Args:
            row: 数据库查询返回的行
            
        Returns:
            Battle: 转换后的Battle对象
        """
        # 获取列名
        column_names = ['battle_id', 'player_id', 'battle_type', 'player_pokemon_ids', 
                        'opponent_pokemon_ids', 'current_player_pokemon_id', 
                        'current_opponent_pokemon_id', 'battle_state', 'turn_number', 
                        'battle_data', 'created_at', 'updated_at']
        
        # 创建行数据字典
        row_dict = {}
        for i, column in enumerate(column_names):
            if i < len(row):
                row_dict[column] = row[i]
        
        # 解析JSON字符串
        player_pokemon_ids = json.loads(row_dict['player_pokemon_ids']) if row_dict.get('player_pokemon_ids') else []
        opponent_pokemon_ids = json.loads(row_dict['opponent_pokemon_ids']) if row_dict.get('opponent_pokemon_ids') else []
        battle_data = json.loads(row_dict['battle_data']) if row_dict.get('battle_data') else {}
        
        # 创建Battle对象
        return Battle(
            battle_id=row_dict['battle_id'],
            player_id=row_dict['player_id'],
            battle_type=row_dict['battle_type'],
            player_pokemon_ids=player_pokemon_ids,
            opponent_pokemon_ids=opponent_pokemon_ids,
            current_player_pokemon_id=row_dict['current_player_pokemon_id'],
            current_opponent_pokemon_id=row_dict['current_opponent_pokemon_id'],
            battle_state=row_dict['battle_state'],
            turn_number=row_dict['turn_number'],
            battle_data=battle_data
        ) 