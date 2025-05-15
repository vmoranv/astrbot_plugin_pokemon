import json # Import json for potential future use or consistency, though repo handles it now
from typing import Optional, List
from backend.models.player import Player
from backend.models.pokemon import Pokemon # Import Pokemon model for type hinting
from backend.data_access.repositories.player_repository import PlayerRepository
from backend.data_access.repositories.pokemon_repository import PokemonRepository # Need PokemonRepository to fetch full Pokemon objects
from backend.utils.exceptions import PlayerNotFoundException, PokemonNotFoundException, PartyFullException, PokemonNotInCollectionException, InvalidPartyOrderException, CannotReleaseLastPokemonException # Import new exception
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class PlayerService:
    """Service for Player related business logic."""

    def __init__(self):
        self.player_repo = PlayerRepository()
        self.pokemon_repo = PokemonRepository() # Initialize PokemonRepository

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
        Retrieves a player by ID. Creates a new player if not found.
        """
        player = await self.player_repo.get_player_by_id(player_id)
        if player is None:
            # Create a new player if not found
            # For now, using player_id as name, can be changed later
            player = await self.player_repo.create_player(player_id, player_id)
            logger.info(f"Created new player with ID: {player_id}")
        return player

    async def save_player(self, player: Player) -> None:
        """
        Saves the player's current state to the database.
        """
        await self.player_repo.update_player(player)

    async def get_player_party(self, player_id: str) -> List[Pokemon]:
        """
        Retrieves the full Pokemon objects for the player's current party.
        """
        player = await self.get_player(player_id)
        party_pokemon = []
        for pokemon_id in player.party_pokemon_ids:
            try:
                pokemon = await self.pokemon_repo.get_pokemon_instance_by_id(pokemon_id)
                if pokemon:
                    party_pokemon.append(pokemon)
                else:
                    logger.error(f"Pokemon instance {pokemon_id} in player {player_id}'s party not found.")
                    # TODO: Handle orphaned pokemon IDs in player data (S1 refinement)
            except PokemonNotFoundException:
                 logger.error(f"Pokemon instance {pokemon_id} in player {player_id}'s party not found.")
                 # TODO: Handle orphaned pokemon IDs in player data (S1 refinement)

        return party_pokemon

    async def get_player_box(self, player_id: str) -> List[Pokemon]:
        """
        Retrieves the full Pokemon objects for the player's current box.
        """
        player = await self.get_player(player_id)
        box_pokemon = []
        for pokemon_id in player.box_pokemon_ids:
            try:
                pokemon = await self.pokemon_repo.get_pokemon_instance_by_id(pokemon_id)
                if pokemon:
                    box_pokemon.append(pokemon)
                else:
                    logger.error(f"Pokemon instance {pokemon_id} in player {player_id}'s box not found.")
                    # TODO: Handle orphaned pokemon IDs in player data (S1 refinement)
            except PokemonNotFoundException:
                 logger.error(f"Pokemon instance {pokemon_id} in player {player_id}'s box not found.")
                 # TODO: Handle orphaned pokemon IDs in player data (S1 refinement)

        return box_pokemon

    async def add_pokemon_to_player(self, player_id: str, pokemon_instance_id: int) -> Player:
        """
        Adds a caught pokemon instance to the player's party if space is available,
        otherwise adds it to the box.
        Returns the updated Player object.
        """
        player = await self.get_player(player_id)

        # Check if the pokemon instance already belongs to this player (shouldn't happen with new catches, but good check)
        if pokemon_instance_id in player.party_pokemon_ids or pokemon_instance_id in player.box_pokemon_ids:
            logger.warning(f"Attempted to add pokemon instance {pokemon_instance_id} that player {player_id} already owns.")
            return player # Or raise an exception

        # S1: Implement logic to add to party if space, otherwise to box
        party_limit = 6 # Define party limit (can be moved to config)
        if len(player.party_pokemon_ids) < party_limit:
            player.party_pokemon_ids.append(pokemon_instance_id)
            location = "party"
            logger.info(f"Added pokemon instance {pokemon_instance_id} to player {player_id}'s party.")
        else:
            player.box_pokemon_ids.append(pokemon_instance_id)
            location = "box"
            logger.info(f"Added pokemon instance {pokemon_instance_id} to player {player_id}'s box.")

        await self.save_player(player)
        return player

    async def remove_pokemon_from_player(self, player_id: str, pokemon_instance_id: int) -> Player:
        """
        Removes a pokemon instance from a player's party or box.
        Raises PokemonNotInCollectionException if the pokemon is not found in the player's collection.
        Raises CannotReleaseLastPokemonException if attempting to release the last pokemon.
        Returns the updated Player object.
        """
        player = await self.get_player(player_id)

        # Check if the pokemon is in the party
        if pokemon_instance_id in player.party_pokemon_ids:
            # S1 refinement: Prevent releasing the last pokemon
            if len(player.party_pokemon_ids) + len(player.box_pokemon_ids) <= 1:
                 raise CannotReleaseLastPokemonException(f"Player {player_id} cannot release their last pokemon.")

            player.party_pokemon_ids.remove(pokemon_instance_id)
            logger.info(f"Removed pokemon instance {pokemon_instance_id} from player {player_id}'s party.")
        # Check if the pokemon is in the box
        elif pokemon_instance_id in player.box_pokemon_ids:
             # S1 refinement: Prevent releasing the last pokemon
            if len(player.party_pokemon_ids) + len(player.box_pokemon_ids) <= 1:
                 raise CannotReleaseLastPokemonException(f"Player {player_id} cannot release their last pokemon.")

            player.box_pokemon_ids.remove(pokemon_instance_id)
            logger.info(f"Removed pokemon instance {pokemon_instance_id} from player {player_id}'s box.")
        else:
            raise PokemonNotInCollectionException(f"Pokemon instance {pokemon_instance_id} not found in player {player_id}'s collection.")

        await self.save_player(player)
        return player

    async def swap_party_pokemon(self, player_id: str, pokemon_instance_id_1: int, pokemon_instance_id_2: int) -> Player:
        """
        Swaps the positions of two pokemon in the player's party.
        Raises PokemonNotInCollectionException if either pokemon is not in the party.
        Raises InvalidPartyOrderException if the swap is invalid (e.g., trying to swap with a box pokemon).
        Returns the updated Player object.
        """
        player = await self.get_player(player_id)

        # Check if both pokemon are in the party
        if pokemon_instance_id_1 not in player.party_pokemon_ids or pokemon_instance_id_2 not in player.party_pokemon_ids:
            raise PokemonNotInCollectionException(f"One or both pokemon ({pokemon_instance_id_1}, {pokemon_instance_id_2}) not found in player {player_id}'s party.")

        # Get their current indices
        try:
            index1 = player.party_pokemon_ids.index(pokemon_instance_id_1)
            index2 = player.party_pokemon_ids.index(pokemon_instance_id_2)
        except ValueError:
            # This should not happen if the above check passes, but as a safeguard
            raise InvalidPartyOrderException(f"Could not find indices for pokemon {pokemon_instance_id_1} or {pokemon_instance_id_2} in player {player_id}'s party.")

        # Swap the IDs in the list
        player.party_pokemon_ids[index1], player.party_pokemon_ids[index2] = player.party_pokemon_ids[index2], player.party_pokemon_ids[index1]

        await self.save_player(player)
        logger.info(f"Swapped pokemon {pokemon_instance_id_1} and {pokemon_instance_id_2} in player {player_id}'s party.")
        return player

    async def move_pokemon_to_box(self, player_id: str, pokemon_instance_id: int) -> Player:
        """
        Moves a pokemon from the player's party to the box.
        Raises PokemonNotInCollectionException if the pokemon is not in the party.
        Raises CannotReleaseLastPokemonException if attempting to move the last pokemon from party.
        Returns the updated Player object.
        """
        player = await self.get_player(player_id)

        if pokemon_instance_id not in player.party_pokemon_ids:
            raise PokemonNotInCollectionException(f"Pokemon instance {pokemon_instance_id} not found in player {player_id}'s party.")

        # S1 refinement: Prevent moving the last pokemon from party if it's the only one left
        if len(player.party_pokemon_ids) == 1 and len(player.box_pokemon_ids) == 0:
             raise CannotReleaseLastPokemonException(f"Player {player_id} cannot move their last pokemon from the party.")

        player.party_pokemon_ids.remove(pokemon_instance_id)
        player.box_pokemon_ids.append(pokemon_instance_id)

        await self.save_player(player)
        logger.info(f"Moved pokemon instance {pokemon_instance_id} from player {player_id}'s party to box.")
        return player

    async def move_pokemon_to_party(self, player_id: str, pokemon_instance_id: int) -> Player:
        """
        Moves a pokemon from the player's box to the party.
        Raises PokemonNotInCollectionException if the pokemon is not in the box.
        Raises PartyFullException if the player's party is full.
        Returns the updated Player object.
        """
        player = await self.get_player(player_id)

        if pokemon_instance_id not in player.box_pokemon_ids:
            raise PokemonNotInCollectionException(f"Pokemon instance {pokemon_instance_id} not found in player {player_id}'s box.")

        party_limit = 6 # Define party limit (can be moved to config)
        if len(player.party_pokemon_ids) >= party_limit:
            raise PartyFullException(f"Player {player_id}'s party is full.")

        player.box_pokemon_ids.remove(pokemon_instance_id)
        player.party_pokemon_ids.append(pokemon_instance_id)

        await self.save_player(player)
        logger.info(f"Moved pokemon instance {pokemon_instance_id} from player {player_id}'s box to party.")
        return player

    async def sort_party(self, player_id: str, ordered_pokemon_ids: List[int]) -> str:
        """
        Sorts the player's party according to the provided list of Pokemon instance IDs.

        Args:
            player_id: The ID of the player.
            ordered_pokemon_ids: A list of Pokemon instance IDs representing the desired order.

        Returns:
            A message indicating the result of the operation.

        Raises:
            PlayerNotFoundException: If the player is not found.
            InvalidPartyOrderException: If the provided list does not match the current party.
        """
        player = await self.get_player(player_id)

        # Validate that the provided list contains the same Pokemon instances as the current party
        current_party_ids_set = set(player.party_pokemon_ids)
        ordered_ids_set = set(ordered_pokemon_ids)

        if current_party_ids_set != ordered_ids_set or len(current_party_ids_set) != len(ordered_pokemon_ids):
            raise InvalidPartyOrderException("Provided list of Pokemon IDs does not match the current party.")

        # Update the player's party with the new order
        player.party_pokemon_ids = ordered_pokemon_ids
        await self.save_player(player)

        logger.info(f"Player {player_id}'s party sorted.")
        return "Your party has been sorted."

    async def release_pokemon(self, player_id: str, pokemon_id: int) -> str:
        """
        Releases a Pokemon instance from the player's collection (party or box).

        Args:
            player_id: The ID of the player.
            pokemon_id: The instance ID of the Pokemon to release.

        Returns:
            A message indicating the result of the operation.

        Raises:
            PlayerNotFoundException: If the player is not found.
            PokemonNotInCollectionException: If the Pokemon is not found in the player's collection.
            CannotReleaseLastPokemonException: If trying to release the last Pokemon in the party.
        """
        player = await self.get_player(player_id)

        # Check if the pokemon is in the party
        if pokemon_id in player.party_pokemon_ids:
            # S1.1: Prevent releasing the last pokemon in the party
            if len(player.party_pokemon_ids) == 1:
                 raise CannotReleaseLastPokemonException("You cannot release your last Pokemon in the party.")
            player.party_pokemon_ids.remove(pokemon_id)
            location = "party"
        # Check if the pokemon is in the box
        elif pokemon_id in player.box_pokemon_ids:
            player.box_pokemon_ids.remove(pokemon_id)
            location = "box"
        else:
            raise PokemonNotInCollectionException(f"Pokemon instance {pokemon_id} not found in player {player_id}'s collection.")

        # Remove the pokemon instance from the database
        await self.pokemon_repo.delete_pokemon_instance(pokemon_id)

        # Save the updated player data
        await self.save_player(player)

        logger.info(f"Player {player_id} released Pokemon instance {pokemon_id} from {location}.")
        return f"You have released Pokemon {pokemon_id} from your {location}."

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
