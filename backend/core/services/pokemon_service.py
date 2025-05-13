from typing import Optional, List
from backend.models.pokemon import Pokemon
from backend.models.player import Player
from backend.data_access.repositories.pokemon_repository import PokemonRepository
from backend.data_access.repositories.metadata_repository import MetadataRepository
from backend.utils.exceptions import PokemonNotFoundException, RaceNotFoundException
from backend.utils.logger import get_logger
# from backend.core.pet import pet_catch # Example core dependency
# from backend.core import pokemon_factory # Example core dependency

logger = get_logger(__name__)

class PokemonService:
    """Service for Pokemon related business logic."""

    def __init__(self):
        self.pokemon_repo = PokemonRepository()
        self.metadata_repo = MetadataRepository()
        # self.pokemon_factory = pokemon_factory.PokemonFactory() # Example

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
        return await self.pokemon_repo.get_player_pokemons(player_id)

    async def catch_wild_pokemon(self, player: Player, location_id: str) -> Optional[Pokemon]:
        """
        Attempts to encounter and catch a wild pokemon.
        """
        # Example workflow:
        # 1. Use core.battle.encounter_logic.try_encounter(location_id) to see if a pokemon is encountered.
        #    wild_race = await encounter_logic.try_encounter(location_id)
        # 2. If encountered, get race data from metadata_repo.
        #    if wild_race:
        #        race_data = await self.metadata_repo.get_race_by_id(wild_race.race_id)
        #        if not race_data:
        #            raise RaceNotFoundException(f"Race data not found for ID {wild_race.race_id}")
        # 3. Create a wild pokemon instance (using core.pokemon_factory).
        #    wild_pokemon_instance = await self.pokemon_factory.create_pokemon_instance(race_data, level=5, owner_id=None) # Wild pokemon has no owner initially
        # 4. Simulate catch attempt (using core.pet.pet_catch.calculate_catch_success).
        #    is_caught = await pet_catch.calculate_catch_success(wild_pokemon_instance, player_pokeball_item) # Need to determine which pokeball is used
        # 5. If caught, update the pokemon instance owner and save it. Add to player's box/party.
        #    if is_caught:
        #        wild_pokemon_instance.owner_id = player.player_id
        #        pokemon_id = await self.pokemon_repo.save_pokemon_instance(wild_pokemon_instance)
        #        # Add pokemon_id to player's party or box (update player model and save player)
        #        # player.add_pokemon_to_box(pokemon_id) # Assuming method in Player model
        #        # await self.player_repo.save_player(player)
        #        logger.info(f"Player {player.player_id} caught a {race_data.name}!")
        #        return wild_pokemon_instance
        #    else:
        #        logger.info(f"Player {player.player_id} failed to catch the {race_data.name}.")
        #        return None # Catch failed
        # else:
        #    logger.info(f"No pokemon encountered in {location_id}.")
        #    return None # No encounter

        logger.warning("catch_wild_pokemon not fully implemented in MVP.")
        return None # Placeholder

    # Add other pokemon related business logic methods (e.g., add_pokemon_to_player, remove_pokemon_from_player, transfer_pokemon, battle_pokemon)
