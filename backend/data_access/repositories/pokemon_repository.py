from typing import Optional, List, Dict, Any
import json
from backend.models.pokemon import Pokemon, PokemonSkill
from backend.data_access.db_manager import fetch_one, fetch_all, execute_query, get_db
from backend.utils.exceptions import PokemonNotFoundException
from backend.utils.logger import get_logger
import aiosqlite

logger = get_logger(__name__)

class PokemonRepository:
    """Repository for Pokemon instance data."""

    async def get_pokemon_instance_by_id(self, pokemon_id: int) -> Optional[Pokemon]:
        """
        Retrieves a pokemon instance by its ID.
        """
        sql = "SELECT * FROM pokemon_instances WHERE pokemon_id = ?"
        row = await fetch_one(sql, (pokemon_id,))
        if row:
            row_dict = dict(row)
            row_dict['skills'] = json.loads(row_dict.get('skills', '[]'))
            row_dict['status_effects'] = json.loads(row_dict.get('status_effects', '[]'))
            row_dict['individual_values'] = json.loads(row_dict.get('individual_values', '{}'))
            row_dict['effort_values'] = json.loads(row_dict.get('effort_values', '{}'))
            return Pokemon.from_dict(row_dict)
        return None

    async def get_player_pokemons(self, player_id: str) -> List[Pokemon]:
        """
        Retrieves all pokemon instances owned by a player.
        """
        sql = "SELECT * FROM pokemon_instances WHERE owner_id = ?"
        rows = await fetch_all(sql, (player_id,))
        pokemons = []
        for row in rows:
            row_dict = dict(row)
            row_dict['skills'] = json.loads(row_dict.get('skills', '[]'))
            row_dict['status_effects'] = json.loads(row_dict.get('status_effects', '[]'))
            row_dict['individual_values'] = json.loads(row_dict.get('individual_values', '{}'))
            row_dict['effort_values'] = json.loads(row_dict.get('effort_values', '{}'))
            pokemons.append(Pokemon.from_dict(row_dict))
        return pokemons

    async def save_pokemon_instance(self, pokemon: Pokemon) -> int:
        """
        Saves or updates a pokemon instance in the database.
        Returns the pokemon_id.
        """
        pokemon_data = pokemon.to_dict()
        pokemon_data['skills'] = json.dumps(pokemon_data['skills'])
        pokemon_data['status_effects'] = json.dumps(pokemon_data['status_effects'])
        pokemon_data['individual_values'] = json.dumps(pokemon_data['individual_values'])
        pokemon_data['effort_values'] = json.dumps(pokemon_data['effort_values'])

        if pokemon.pokemon_id is None:
            sql = """
            INSERT INTO pokemon_instances (
                instance_id, race_id, owner_id, nickname, level, current_hp, experience,
                max_hp, attack, defense, special_attack, special_defense, speed,
                skills, status_effects, nature_id, ability_id, individual_values, effort_values
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                pokemon.instance_id, pokemon.race_id, pokemon.owner_id, pokemon.nickname, pokemon.level,
                pokemon.current_hp, pokemon.experience, pokemon.max_hp, pokemon.attack,
                pokemon.defense, pokemon.special_attack, pokemon.special_defense,
                pokemon.speed, pokemon_data['skills'], pokemon_data['status_effects'],
                pokemon.nature_id, pokemon.ability_id, pokemon_data['individual_values'],
                pokemon_data['effort_values']
            )
            cursor = await execute_query(sql, params)
            pokemon.pokemon_id = cursor.lastrowid
            logger.debug(f"Created new pokemon instance with ID: {pokemon.pokemon_id}")
        else:
            sql = """
            UPDATE pokemon_instances
            SET instance_id = ?, race_id = ?, owner_id = ?, nickname = ?, level = ?, current_hp = ?, experience = ?,
                max_hp = ?, attack = ?, defense, special_attack = ?, special_defense = ?, speed = ?,
                skills = ?, status_effects = ?, nature_id = ?, ability_id = ?, individual_values = ?, effort_values = ?
            WHERE pokemon_id = ?
            """
            params = (
                pokemon.instance_id, pokemon.race_id, pokemon.owner_id, pokemon.nickname, pokemon.level,
                pokemon.current_hp, pokemon.experience, pokemon.max_hp, pokemon.attack,
                pokemon.defense, pokemon.special_attack, pokemon.special_defense,
                pokemon.speed, pokemon_data['skills'], pokemon_data['status_effects'],
                pokemon.nature_id, pokemon.ability_id, pokemon_data['individual_values'],
                pokemon_data['effort_values'], pokemon.pokemon_id
            )
            await execute_query(sql, params)
            logger.debug(f"Updated pokemon instance with ID: {pokemon.pokemon_id}")

        return pokemon.pokemon_id

    async def delete_pokemon_instance(self, pokemon_id: int) -> None:
        """
        Deletes a pokemon instance by its ID.
        """
        sql = "DELETE FROM pokemon_instances WHERE pokemon_id = ?"
        await execute_query(sql, (pokemon_id,))
        logger.debug(f"Deleted pokemon instance with ID: {pokemon_id}")

    async def mark_orphaned_pokemon_id(self, pokemon_instance_id: int, player_id: str) -> None:
        """
        标记孤立的宝可梦实例ID，用于后续清理。
        
        Args:
            pokemon_instance_id (int): 孤立的宝可梦实例ID
            player_id (str): 关联的玩家ID
        """
        # 检查orphaned_pokemon_ids表是否存在，不存在则创建
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS orphaned_pokemon_ids (
                pokemon_instance_id INTEGER PRIMARY KEY,
                player_id TEXT NOT NULL,
                marked_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入记录，如果已存在则忽略
        await self.db.execute('''
            INSERT OR IGNORE INTO orphaned_pokemon_ids (pokemon_instance_id, player_id)
            VALUES (?, ?)
        ''', (pokemon_instance_id, player_id))
        
        await self.db.commit()

    async def get_all_orphaned_pokemon_ids(self) -> List[Dict[str, Any]]:
        """
        获取所有标记为孤立的宝可梦实例ID。
        
        Returns:
            List[Dict[str, Any]]: 孤立ID的列表，每个条目包含pokemon_instance_id, player_id和marked_time
        """
        cursor = await self.db.execute('''
            SELECT pokemon_instance_id, player_id, marked_time
            FROM orphaned_pokemon_ids
        ''')
        
        results = await cursor.fetchall()
        
        return [
            {
                "pokemon_instance_id": row[0],
                "player_id": row[1],
                "marked_time": row[2]
            }
            for row in results
        ]

    async def pokemon_instance_exists(self, pokemon_instance_id: int) -> bool:
        """
        检查指定的宝可梦实例ID是否存在。
        
        Args:
            pokemon_instance_id (int): 要检查的宝可梦实例ID
            
        Returns:
            bool: 如果存在则返回True，否则返回False
        """
        cursor = await self.db.execute('''
            SELECT COUNT(*)
            FROM pokemon_instances
            WHERE instance_id = ?
        ''', (pokemon_instance_id,))
        
        result = await cursor.fetchone()
        return result[0] > 0

    async def delete_pokemon_instance(self, pokemon_instance_id: int) -> None:
        """
        删除指定的宝可梦实例。
        
        Args:
            pokemon_instance_id (int): 要删除的宝可梦实例ID
        """
        await self.db.execute('''
            DELETE FROM pokemon_instances
            WHERE instance_id = ?
        ''', (pokemon_instance_id,))
        
        await self.db.commit()

    async def remove_orphaned_pokemon_id(self, pokemon_instance_id: int) -> None:
        """
        从孤立ID表中移除指定的宝可梦实例ID。
        
        Args:
            pokemon_instance_id (int): 要移除的宝可梦实例ID
        """
        await self.db.execute('''
            DELETE FROM orphaned_pokemon_ids
            WHERE pokemon_instance_id = ?
        ''', (pokemon_instance_id,))
        
        await self.db.commit()

    # 您可以在这里添加其他与 races 表相关的数据库操作方法 