from typing import Optional
from backend.models.player import Player
from backend.data_access.repositories.player_repository import PlayerRepository
from backend.utils.exceptions import PlayerNotFoundException
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class PlayerService:
    """Service for Player related business logic."""

    def __init__(self):
        self.player_repo = PlayerRepository()

    async def get_or_create_player(self, player_id: str, player_name: str) -> Player:
        """
        Retrieves an existing player or creates a new one if not found.
        """
        player = await self.player_repo.get_player_by_id(player_id)
        if player is None:
            logger.info(f"Player {player_id} not found, creating new player.")
            player = await self.player_repo.create_player(player_id, player_name)
        return player

    async def get_player(self, player_id: str) -> Player:
        """
        Retrieves an existing player. Raises PlayerNotFoundException if not found.
        """
        player = await self.player_repo.get_player_by_id(player_id)
        if player is None:
            raise PlayerNotFoundException(f"Player with ID {player_id} not found.")
        return player

    async def save_player(self, player: Player) -> None:
        """
        Saves a player's data.
        """
        await self.player_repo.save_player(player)
        logger.debug(f"Player {player.player_id} data saved.")

    # Add other player related business logic methods (e.g., update_location, add_item, remove_item)
    # async def update_player_location(self, player_id: str, new_location_id: str) -> Player:
    #     player = await self.get_player(player_id)
    #     player.location_id = new_location_id
    #     await self.save_player(player)
    #     logger.info(f"Player {player_id} moved to {new_location_id}")
    #     return player

    # async def add_item_to_player(self, player_id: str, item_id: int, quantity: int = 1) -> Player:
    #     player = await self.get_player(player_id)
    #     player.add_item(item_id, quantity) # Assuming add_item method in Player model
    #     await self.save_player(player)
    #     logger.info(f"Added {quantity} of item {item_id} to player {player_id}")
    #     return player
