# Import key core components
# from .game_logic import process_game_turn # Example
# from .pokemon_factory import PokemonFactory # Example

# Import functions/classes from pet and battle submodules
from .pet import (
    learn_skill, forget_skill, use_skill,
    gain_experience, level_up, calculate_exp_needed as pet_calculate_exp_needed, # Alias if needed to avoid name clash
    calculate_catch_success,
    check_evolution, evolve_pokemon,
    use_item_on_pokemon,
    get_pokemon_stats
)

from .battle import (
    calculate_stats, calculate_damage, calculate_catch_rate, calculate_exp_needed as battle_calculate_exp_needed, # Alias
    process_battle_turn,
    try_encounter, determine_wild_pokemon_level
)

# Optionally define __all__ for explicit exports
__all__ = [
    "PokemonFactory",

    # From pet
    "learn_skill", "forget_skill", "use_skill",
    "gain_experience", "level_up", "pet_calculate_exp_needed",
    "calculate_catch_success",
    "check_evolution", "evolve_pokemon",
    "use_item_on_pokemon",
    "get_pokemon_stats",

    # From battle
    "calculate_stats", "calculate_damage", "calculate_catch_rate", "battle_calculate_exp_needed",
    "process_battle_turn",
    "try_encounter", "determine_wild_pokemon_level",
]

# Re-export logger from utils for convenience within core modules
from backend.utils.logger import get_logger
logger = get_logger(__name__)
