from typing import Optional, List, Tuple, Dict, Any
from backend.models.pokemon import Pokemon
from backend.models.player import Player
from backend.models.item import Item
from backend.models.race import Race
from backend.data_access.repositories.pokemon_repository import PokemonRepository
from backend.data_access.repositories.metadata_repository import MetadataRepository
from backend.data_access.repositories.player_repository import PlayerRepository
from backend.utils.exceptions import PokemonNotFoundException, RaceNotFoundException, ItemNotFoundException, InsufficientItemException, PlayerNotFoundException, InvalidPartyOrderException, PartyFullException, PokemonNotInCollectionException
from backend.utils.logger import get_logger
from backend.core.pet import pet_catch
from backend.core import pokemon_factory
from backend.core.battle import encounter_logic, formulas
from backend.core.services.item_service import ItemService
from backend.core.services.player_service import PlayerService
from backend.core.battle.encounter_logic import encounter_logic as encounter_logic_instance
from backend.core.battle.catch_logic import catch_logic

logger = get_logger(__name__)

class PokemonService:
    """Service for Pokemon related business logic."""

    def __init__(self):
        self.pokemon_repo = PokemonRepository()
        self.metadata_repo = MetadataRepository()
        self.player_repo = PlayerRepository()
        self.pokemon_factory = pokemon_factory.PokemonFactory()
        self.item_service = ItemService()
        self.player_service = PlayerService()

    async def get_pokemon_instance(self, pokemon_id: int) -> Pokemon:
        """
        Retrieves a specific pokemon instance. Raises PokemonNotFoundException if not found.
        """
        pokemon = await self.pokemon_repo.get_pokemon_instance_by_id(pokemon_id)
        if pokemon is None:
            raise PokemonNotFoundException(f"Pokemon instance with ID {pokemon_id} not found.")
        return pokemon

    async def get_player_pokemons(self, player_id: str) -> List[Pokemon]:
        """
        Retrieves all pokemon instances owned by a player.
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        all_pokemon_ids = player.party_pokemon_ids + player.box_pokemon_ids
        pokemons = []
        for pokemon_id in all_pokemon_ids:
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_id)
            if pokemon:
                pokemons.append(pokemon)
            else:
                logger.warning(f"Pokemon instance {pokemon_id} not found for player {player_id}.")
        return pokemons

    async def get_player_party_pokemon(self, player_id: str) -> List[Pokemon]:
        """
        Retrieves the pokemon instances in the player's party.
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        party_pokemons = []
        for pokemon_id in player.party_pokemon_ids:
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_id)
            if pokemon:
                party_pokemons.append(pokemon)
            else:
                logger.warning(f"Pokemon instance {pokemon_id} in party not found for player {player_id}.")
                # TODO: Handle orphaned pokemon instance IDs in player party/box (S1: Data integrity check)
        return party_pokemons

    async def get_player_box_pokemon(self, player_id: str) -> List[Pokemon]:
        """
        Retrieves the pokemon instances in the player's box.
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        box_pokemons = []
        for pokemon_id in player.box_pokemon_ids:
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_id)
            if pokemon:
                box_pokemons.append(pokemon)
            else:
                logger.warning(f"Pokemon instance {pokemon_id} in box not found for player {player_id}.")
                # TODO: Handle orphaned pokemon instance IDs in player party/box (S1: Data integrity check)
        return box_pokemons

    async def save_pokemon(self, pokemon: Pokemon):
        """Saves a pokemon instance to the repository."""
        await self.pokemon_repo.save_pokemon_instance(pokemon)

    async def create_pokemon_instance(self, race_id: int, level: int) -> Pokemon:
        """
        Creates a new pokemon instance with generated stats, moves, etc.
        """
        # TODO: Implement detailed pokemon instance creation logic (S2 refinement)
        # This should involve fetching race data, calculating stats based on level,
        # generating IVs/EVs, selecting moves, etc.
        logger.info(f"Creating new pokemon instance for race {race_id} at level {level}")
        # Placeholder implementation:
        new_pokemon = Pokemon(
            instance_id=None, # Repository will assign ID
            race_id=race_id,
            level=level,
            current_hp=100, # Placeholder
            max_hp=100, # Placeholder
            attack=50, # Placeholder
            defense=50, # Placeholder
            special_attack=50, # Placeholder
            special_defense=50, # Placeholder
            speed=50, # Placeholder
            moves=[], # Placeholder
            status_effects=[], # Placeholder
            experience=0, # Placeholder
            is_in_party=False # Initially not in party
        )
        # Save the new instance to get its ID
        await self.pokemon_repo.save_pokemon_instance(new_pokemon)
        logger.info(f"Created pokemon instance with ID: {new_pokemon.instance_id}")
        return new_pokemon

    async def check_for_wild_encounter(self, location_id: str) -> bool:
        """
        Checks if a wild pokemon encounter occurs at the given location.
        """
        return await encounter_logic_instance.check_encounter(location_id)

    async def get_wild_encounter_details(self, location_id: str) -> Optional[Tuple[int, int]]:
        """
        Gets the details (race_id, level) of a wild pokemon encounter for a location.
        Should only be called if check_for_wild_encounter returned True.
        """
        return await encounter_logic_instance.get_wild_pokemon_details(location_id)

    async def attempt_catch_pokemon(self, player: Player, pokemon_instance_id: int, pokeball_item_id: int) -> Tuple[bool, str]:
        """
        Attempts to catch a specific wild pokemon instance using a pokeball.
        Returns a tuple: (success: bool, message: str).
        """
        logger.debug(f"Player {player.player_id} attempting to catch pokemon instance {pokemon_instance_id} with pokeball {pokeball_item_id}")

        # 1. Get pokemon instance details
        pokemon_instance = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
        if not pokemon_instance:
            logger.error(f"Attempted to catch non-existent pokemon instance: {pokemon_instance_id}")
            return (False, "尝试捕获的宝可梦不存在。") # Should not happen if flow is correct

        # 2. Consume the pokeball
        try:
            await self.item_service.remove_item_from_player(player.player_id, pokeball_item_id, quantity=1)
            logger.debug(f"Consumed pokeball {pokeball_item_id} from player {player.player_id}.")
        except InsufficientItemException:
            logger.warning(f"Player {player.player_id} attempted to use pokeball {pokeball_item_id} but does not have enough.")
            # Attempt to get item name for better message, but fallback if not found
            try:
                item_data = await self.item_service.get_item_data(pokeball_item_id)
                item_name = item_data.name
            except ItemNotFoundException:
                item_name = f"ID为 {pokeball_item_id} 的道具"
            return (False, f"你没有足够的 {item_name}。")
        except ItemNotFoundException:
             logger.error(f"Attempted to use non-existent pokeball {pokeball_item_id} by player {player.player_id}.")
             return (False, f"ID为 {pokeball_item_id} 的道具不存在。")
        except Exception as e:
            logger.error(f"Error consuming item {pokeball_item_id} for player {player.player_id}: {e}", exc_info=True)
            return (False, "消耗道具时发生错误。")

        # 3. Perform catch calculation
        # TODO: Implement detailed catch calculation logic (S2 refinement)
        # This should involve pokemon's HP, status effects, pokeball type, etc.
        # For now, a simple random chance based on level.
        catch_success_rate = catch_logic.calculate_catch_rate(pokemon_instance.level, pokeball_item_id) # Assuming catch_logic handles this
        logger.debug(f"Calculated catch success rate: {catch_success_rate}")

        if random.random() < catch_success_rate:
            # Catch successful
            logger.info(f"Player {player.player_id} successfully caught pokemon instance {pokemon_instance_id}.")

            # 4. Add pokemon to player's collection (box)
            player.box_pokemon_ids.append(pokemon_instance_id)
            pokemon_instance.is_in_party = False # Ensure it's marked as not in party
            await self.player_repo.save_player(player)
            await self.pokemon_repo.save_pokemon_instance(pokemon_instance)

            # Get pokemon race name for the success message
            try:
                race_data = await self.metadata_repo.get_race_by_id(pokemon_instance.race_id)
                pokemon_name = race_data.name if race_data else f"未知宝可梦 (ID: {pokemon_instance.race_id})"
            except RaceNotFoundException:
                 pokemon_name = f"未知宝可梦 (ID: {pokemon_instance.race_id})"

            return (True, f"恭喜！你成功捕获了野生的 {pokemon_name} (等级 {pokemon_instance.level})！它已被送往你的宝可梦盒子。")
        else:
            # Catch failed
            logger.info(f"Player {player.player_id}'s attempt to catch pokemon instance {pokemon_instance_id} failed.")
            # TODO: Wild pokemon might flee after failed attempt (S2 refinement)
            return (False, "可惜！宝可梦挣脱了，逃走了。") # Or "宝可梦挣脱了！" if it doesn't flee

    async def move_pokemon_to_box(self, player_id: str, pokemon_instance_id: int) -> Player:
        """
        Moves a pokemon from the player's party to the box.
        Raises PokemonNotInCollectionException if the pokemon is not in the party.
        Returns the updated Player object.
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        if pokemon_instance_id not in player.party_pokemon_ids:
            raise PokemonNotInCollectionException(f"Pokemon instance {pokemon_instance_id} not found in player {player_id}'s party.")

        player.party_pokemon_ids.remove(pokemon_instance_id)
        player.box_pokemon_ids.append(pokemon_instance_id)

        # Update the pokemon instance's is_in_party status
        pokemon_instance = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
        if pokemon_instance:
            pokemon_instance.is_in_party = False
            await self.pokemon_repo.save_pokemon_instance(pokemon_instance)
        else:
             logger.warning(f"Pokemon instance {pokemon_instance_id} not found when moving to box.")
             # TODO: Handle orphaned pokemon instance IDs (S1: Data integrity check)

        await self.player_repo.save_player(player)
        logger.info(f"Moved pokemon instance {pokemon_instance_id} from player {player_id}'s party to box.")
        return player

    async def move_pokemon_to_party(self, player_id: str, pokemon_instance_id: int) -> Player:
        """
        Moves a pokemon from the player's box to the party.
        Raises PokemonNotInCollectionException if the pokemon is not in the box.
        Raises PartyFullException if the player's party is full.
        Returns the updated Player object.
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        if pokemon_instance_id not in player.box_pokemon_ids:
            raise PokemonNotInCollectionException(f"Pokemon instance {pokemon_instance_id} not found in player {player_id}'s box.")

        party_limit = 6 # Define party limit (can be moved to config)
        if len(player.party_pokemon_ids) >= party_limit:
            raise PartyFullException(f"Player {player_id}'s party is full.")

        player.box_pokemon_ids.remove(pokemon_instance_id)
        player.party_pokemon_ids.append(pokemon_instance_id)

        # Update the pokemon instance's is_in_party status
        pokemon_instance = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
        if pokemon_instance:
            pokemon_instance.is_in_party = True
            await self.pokemon_repo.save_pokemon_instance(pokemon_instance)
        else:
             logger.warning(f"Pokemon instance {pokemon_instance_id} not found when moving to party.")
             # TODO: Handle orphaned pokemon instance IDs (S1: Data integrity check)

        await self.player_repo.save_player(player)
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
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        # Validate that the provided list contains the same Pokemon instances as the current party
        current_party_ids_set = set(player.party_pokemon_ids)
        ordered_ids_set = set(ordered_pokemon_ids)

        if current_party_ids_set != ordered_ids_set or len(current_party_ids_set) != len(ordered_pokemon_ids):
            raise InvalidPartyOrderException("Provided list of Pokemon IDs does not match the current party.")

        # Update the player's party with the new order
        player.party_pokemon_ids = ordered_pokemon_ids
        await self.player_repo.save_player(player)

        logger.info(f"Player {player_id}'s party sorted to order: {ordered_pokemon_ids}")
        return "队伍排序成功！"

    async def heal_pokemon(self, pokemon_instance_id: int, amount: int) -> Pokemon:
        """
        Heals a specific pokemon instance by a given amount.
        Raises PokemonNotFoundException if the pokemon instance is not found.
        Returns the updated Pokemon object.
        """
        pokemon = await self.get_pokemon_instance(pokemon_instance_id)

        # Ensure HP does not exceed max HP
        pokemon.current_hp = min(pokemon.current_hp + amount, pokemon.max_hp)

        await self.pokemon_repo.update_pokemon_instance(pokemon) # Assuming update_pokemon_instance exists in PokemonRepository
        logger.info(f"Healed pokemon instance {pokemon_instance_id} by {amount}. Current HP: {pokemon.current_hp}")
        return pokemon

    # TODO: Implement other pokemon modification methods (e.g., change status, gain experience, learn move)
