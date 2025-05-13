from typing import Optional, Dict, Any
import json
from backend.models.player import Player
from backend.data_access.db_manager import fetch_one, execute_query
from backend.utils.exceptions import PlayerNotFoundException
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class PlayerRepository:
    """Repository for Player data."""

    async def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """
        Retrieves a player by their ID.
        """
        sql = "SELECT * FROM players WHERE player_id = ?"
        row = await fetch_one(sql, (player_id,))
        if row:
            # Deserialize JSON fields
            row_dict = dict(row)
            row_dict['inventory'] = json.loads(row_dict.get('inventory', '{}'))
            row_dict['pokemon_party'] = json.loads(row_dict.get('pokemon_party', '[]'))
            row_dict['pokemon_box'] = json.loads(row_dict.get('pokemon_box', '[]'))
            row_dict['tasks'] = json.loads(row_dict.get('tasks', '{}'))
            row_dict['achievements'] = json.loads(row_dict.get('achievements', '[]'))
            return Player.from_dict(row_dict)
        return None

    async def save_player(self, player: Player) -> None:
        """
        Saves or updates a player's data.
        """
        # Serialize JSON fields
        player_data = player.to_dict()
        player_data['inventory'] = json.dumps(player_data['inventory'])
        player_data['pokemon_party'] = json.dumps(player_data['pokemon_party'])
        player_data['pokemon_box'] = json.dumps(player_data['pokemon_box'])
        player_data['tasks'] = json.dumps(player_data['tasks'])
        player_data['achievements'] = json.dumps(player_data['achievements'])

        sql = """
        INSERT OR REPLACE INTO players (player_id, name, location_id, money, inventory, pokemon_party, pokemon_box, tasks, achievements)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            player.player_id,
            player.name,
            player.location_id,
            player.money,
            player_data['inventory'],
            player_data['pokemon_party'],
            player_data['pokemon_box'],
            player_data['tasks'],
            player_data['achievements'],
        )
        await execute_query(sql, params)
        logger.debug(f"Saved player: {player.player_id}")

    async def create_player(self, player_id: str, name: str) -> Player:
        """
        Creates a new player with default values.
        """
        from backend.config.settings import settings # Import here to avoid circular dependency if settings imports models
        new_player = Player(
            player_id=player_id,
            name=name,
            location_id=settings.PLAYER_START_LOCATION,
            money=settings.STARTING_MONEY,
            inventory={},
            pokemon_party=[],
            pokemon_box=[],
            tasks={},
            achievements=[]
        )
        await self.save_player(new_player)
        logger.info(f"Created new player: {player_id} with name {name}")
        return new_player 