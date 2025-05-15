from typing import Optional, Dict, Any
from backend.models.player import Player
from backend.models.item import Item
from backend.data_access.repositories.metadata_repository import MetadataRepository
from backend.utils.exceptions import ItemNotFoundException, InsufficientItemException, PokemonNotFoundException
from backend.utils.logger import get_logger
# from backend.core.pet import pet_item # Example core dependency
from backend.core.services.player_service import PlayerService
from backend.core.services.pokemon_service import PokemonService

logger = get_logger(__name__)

class ItemService:
    """Service for Item related business logic."""

    def __init__(self):
        self.metadata_repo = MetadataRepository()
        self.player_service = PlayerService()
        self.pokemon_service = PokemonService()

    async def get_item_data(self, item_id: int) -> Item:
        """
        Retrieves item metadata. Raises ItemNotFoundException if not found.
        """
        item_data = await self.metadata_repo.get_item_data(item_id)
        if not item_data:
            raise ItemNotFoundException(f"Item metadata not found for item_id: {item_id}")
        return Item(**item_data)

    async def get_player_item_quantity(self, player_id: str, item_id: int) -> int:
        """
        Retrieves the quantity of a specific item a player has.
        """
        player = await self.player_service.get_player(player_id)
        return player.items.get(item_id, 0)

    async def add_item_to_player(self, player_id: str, item_id: int, quantity: int = 1) -> Player:
        """
        Adds a specified quantity of an item to a player's inventory.
        Returns the updated Player object.
        """
        if quantity <= 0:
            logger.warning(f"Attempted to add non-positive quantity ({quantity}) of item {item_id} to player {player_id}.")
            return await self.player_service.get_player(player_id)

        player = await self.player_service.get_player(player_id)
        player.items[item_id] = player.items.get(item_id, 0) + quantity

        await self.player_service.save_player(player)
        logger.info(f"Added {quantity} of item {item_id} to player {player_id}. New quantity: {player.items[item_id]}")
        return player

    async def remove_item_from_player(self, player_id: str, item_id: int, quantity: int = 1) -> Player:
        """
        Removes a specified quantity of an item from a player's inventory.
        Raises InsufficientItemException if the player does not have enough items.
        Returns the updated Player object.
        """
        if quantity <= 0:
            logger.warning(f"Attempted to remove non-positive quantity ({quantity}) of item {item_id} from player {player_id}.")
            return await self.player_service.get_player(player_id)

        player = await self.player_service.get_player(player_id)
        current_quantity = player.items.get(item_id, 0)

        if current_quantity < quantity:
            logger.warning(f"Player {player_id} attempted to remove {quantity} of item {item_id} but only has {current_quantity}.")
            raise InsufficientItemException(f"Player {player_id} does not have enough of item {item_id}.")

        player.items[item_id] -= quantity
        if player.items[item_id] <= 0:
            del player.items[item_id]

        await self.player_service.save_player(player)
        logger.info(f"Removed {quantity} of item {item_id} from player {player_id}. Remaining quantity: {player.items.get(item_id, 0)}")
        return player

    async def use_item(self, player: Player, item_id: int, target_id: Optional[int] = None) -> str:
        """
        Uses an item from the player's inventory.
        target_id could be a pokemon_id, player_id, or map_id depending on item type.
        Returns a message describing the result.
        """
        try:
            # S3 refinement: Get item data to check item type and name for messages
            item_data = await self.get_item_data(item_id)

            await self.remove_item_from_player(player.player_id, item_id, quantity=1)
            logger.debug(f"Item {item_id} removed from player {player.player_id} for usage.")

            # TODO: Implement item effect logic based on item type and target (S3 refinement)
            # Example:
            # if item_data.item_type == "consumable":
            #     if target_id is not None:
            #         # Apply effect to target (e.g., heal pokemon)
            #         pass
            #     else:
            #         # S3 refinement: Message for item requiring target but none provided
            #         return f"使用 {item_data.name} 需要指定一个目标。"
            # elif item_data.item_type == "pokeball":
            #     # Pokeball usage is handled in PokemonService.catch_wild_pokemon
            #     # This use_item method might not be called directly for pokeballs in catch scenarios.
            #     pass # Or handle other pokeball related effects if any

            # For now, just confirm item was used
            # S3 refinement: Use item name in success message
            return f"你使用了 {item_data.name}。"

        except InsufficientItemException:
            logger.warning(f"Player {player.player_id} attempted to use item {item_id} but does not have enough.")
            # S3 refinement: Return a specific message to the user indicating insufficient items
            # Attempt to get item name for better message, but fallback if not found
            try:
                item_data = await self.get_item_data(item_id)
                item_name = item_data.name
            except ItemNotFoundException:
                item_name = f"ID为 {item_id} 的道具"
            return f"你没有足够的 {item_name}。"
        except ItemNotFoundException:
            logger.error(f"Attempted to use non-existent item {item_id} by player {player.player_id}.")
            # S3 refinement: Return a specific message for non-existent item
            return f"ID为 {item_id} 的道具不存在。"
        except PokemonNotFoundException:
            logger.warning(f"Player {player.player_id} attempted to use item {item_id} on non-existent pokemon {target_id}.")
            return "未能找到你想要使用道具的宝可梦。"
        except Exception as e:
            logger.error(f"An error occurred while using item {item_id} for player {player.player_id}: {e}", exc_info=True)
            # S3 refinement: Return a generic error message to the user
            return "使用道具时发生未知错误。"

    # Add other item related business logic methods (e.g., buy_item, sell_item, get_player_inventory)
