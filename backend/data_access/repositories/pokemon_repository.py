from typing import Optional, List, Dict, Any
import json
from backend.models.pokemon import Pokemon
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
        Saves or updates a pokemon instance's data.
        Returns the pokemon_id (useful for new instances).
        """
        pokemon_data = pokemon.to_dict()
        pokemon_data['skills'] = json.dumps(pokemon_data['skills'])
        pokemon_data['status_effects'] = json.dumps(pokemon_data['status_effects'])
        pokemon_data['individual_values'] = json.dumps(pokemon_data['individual_values'])
        pokemon_data['effort_values'] = json.dumps(pokemon_data['effort_values'])

        if pokemon.pokemon_id is None:
            sql = """
            INSERT INTO pokemon_instances (race_id, owner_id, nickname, level, current_hp, experience, max_hp, attack, defense, special_attack, special_defense, speed, skills, status_effects, nature_id, ability_id, individual_values, effort_values)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                pokemon.race_id, pokemon.owner_id, pokemon.nickname, pokemon.level,
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
            SET race_id = ?, owner_id = ?, nickname = ?, level = ?, current_hp = ?, experience = ?,
                max_hp = ?, attack = ?, defense = ?, special_attack = ?, special_defense = ?, speed = ?,
                skills = ?, status_effects = ?, nature_id = ?, ability_id = ?, individual_values = ?, effort_values = ?
            WHERE pokemon_id = ?
            """
            params = (
                pokemon.race_id, pokemon.owner_id, pokemon.nickname, pokemon.level,
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

    # 您可以在这里添加其他与 races 表相关的数据库操作方法 