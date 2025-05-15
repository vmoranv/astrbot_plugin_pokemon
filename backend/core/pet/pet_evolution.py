# backend/core/pet/pet_evolution.py

from typing import Optional
from backend.models.pokemon import Pokemon
from backend.models.race import Race # Need Race data for evolution chain
# from backend.services.metadata_service import MetadataService # Core should not depend on Services

# Core logic functions should receive necessary data as arguments.

async def check_evolution(pokemon: Pokemon, race_data: Race) -> Optional[int]:
    """
    Checks if a pokemon meets the conditions to evolve.
    Requires the Pokemon instance and its Race data (which includes evolution info).
    Returns the ID of the next Race if evolution is possible, None otherwise.
    """
    # This is pure logic based on the Pokemon's current state (level, happiness, held item, etc.)
    # and the evolution requirements defined in its Race data.

    # Assume Race data includes a list of possible evolutions, each with conditions.
    # Example structure for evolution data in Race model:
    # race_data.evolutions = [
    #     {"to_race_id": 2, "condition_type": "level", "condition_value": 12},
    #     {"to_race_id": 3, "condition_type": "item", "condition_value": 101}, # Item ID for evolution stone
    #     # Add other conditions like happiness, trade, location, etc.
    # ]

    # Example logic (simplified):
    if not race_data.evolutions:
        # This race does not evolve
        return None

    for evolution in race_data.evolutions:
        condition_type = evolution.get("condition_type")
        condition_value = evolution.get("condition_value")
        next_race_id = evolution.get("to_race_id")

        if condition_type == "level":
            if pokemon.level >= condition_value:
                logger.debug(f"{pokemon.nickname} meets level condition for evolution to {next_race_id}")
                return next_race_id
        elif condition_type == "item":
            # Check if the pokemon is holding the required item
            # This requires the Pokemon model to have a 'held_item_id' attribute
            if hasattr(pokemon, 'held_item_id') and pokemon.held_item_id == condition_value:
                 logger.debug(f"{pokemon.nickname} meets item condition for evolution to {next_race_id}")
                 return next_race_id
        # Add checks for other evolution conditions (happiness, trade, etc.)
        # elif condition_type == "happiness":
        #     if hasattr(pokemon, 'happiness') and pokemon.happiness >= condition_value:
        #         return next_race_id
        # elif condition_type == "trade":
        #     # This condition is met by the trade process itself, not checked here
        #     pass # Or maybe check a flag set during trade?

    # No evolution conditions met
    return None

async def evolve_pokemon(pokemon: Pokemon, next_race: Race) -> None:
    """
    Evolves a pokemon to the next stage.
    Requires the Pokemon instance and the Race data for the next stage.
    This function updates the Pokemon object's race and recalculates stats.
    """
    # This is pure logic that modifies the Pokemon object based on the new Race data.
    # Saving the updated pokemon is the responsibility of the Service layer.

    logger.info(f"Evolving {pokemon.nickname} to {next_race.name}")

    # Update the pokemon's race ID and name
    pokemon.race_id = next_race.race_id
    pokemon.name = next_race.name # Update name to new species name

    # Recalculate stats based on the new race's base stats, current level, IVs, EVs, Nature
    # Assuming calculate_stats function exists in core.battle.formulas
    from backend.core.battle.formulas import calculate_stats # Import here to avoid circular dependency if formulas also imports pet_grow/evolution
    pokemon.stats = calculate_stats(pokemon, next_race) # Recalculate stats with the new race data

    # Evolution might also involve:
    # - Learning new moves (check next_race's level-up moves at current level)
    # - Changing ability
    # - Resetting happiness (sometimes happens)
    # - Clearing the can_evolve_to flag

    pokemon.can_evolve_to = None # Clear the evolution flag

    # Note: Saving the updated pokemon object is the responsibility of the Service layer.

# Add other evolution related functions if needed
