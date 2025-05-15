# backend/core/battle/formulas.py

import math
import random # Need random for the final shake check
from typing import Dict, Optional, List, Any, Tuple
from backend.models.pokemon import Pokemon
from backend.models.race import Race
from backend.models.item import Item # For Pokeball modifier
from backend.models.skill import Skill # For Skill power/type
from backend.models.status_effect import StatusEffect # For status effect modifier
from backend.models.battle import Battle # Import Battle model to access terrain/weather
from backend.utils.logger import get_logger
from backend.utils.exceptions import (
    InvalidBattleActionException, BattleFinishedException,
    PokemonFaintedException, NoActivePokemonException, SkillNotFoundException,
    ItemNotFoundException, InvalidTargetException, NotEnoughPokemonException,
    InvalidPokemonStateError
)
from backend.data_access.metadata_loader import MetadataRepository # Import MetadataRepository
from backend.models.attribute import Attribute # Import Attribute model

logger = get_logger(__name__)

# This module contains pure functions for calculations.
# It should not modify any objects or interact with external systems.

def calculate_stats(pokemon: Pokemon, race_data: Race) -> Dict[str, int]:
    """
    Calculates a pokemon's current stats based on its level, IVs, EVs, Nature, and Race base stats.
    Returns a dictionary of calculated stats.
    """
    # This is a simplified placeholder. Actual Pokemon stat calculation is complex.
    # Formula depends on HP vs other stats.
    # HP: (((Base_HP * 2 + IV_HP + EV_HP/4) * Level) / 100) + Level + 10
    # Other Stats: ((((Base_Stat * 2 + IV_Stat + EV_Stat/4) * Level) / 100) + 5) * Nature_Modifier

    base_stats = race_data.base_stats # Assuming base_stats is a dict on Race model
    level = pokemon.level
    ivs = pokemon.ivs
    evs = pokemon.evs
    nature = pokemon.nature # Assuming nature is a string or object

    # Need Nature modifiers data - this could be a constant lookup or passed in.
    # For simplicity, let's assume a neutral nature modifier of 1.0 for all stats for MVP.
    # A real implementation needs a lookup for nature effects.
    nature_modifiers = {
        "attack": 1.0, "defense": 1.0, "special_attack": 1.0, "special_defense": 1.0, "speed": 1.0
    }
    # Example: If nature is "adamant", nature_modifiers["attack"] = 1.1, nature_modifiers["special_attack"] = 0.9

    calculated_stats = {}

    # Calculate HP
    base_hp = base_stats.get("hp", 1)
    iv_hp = ivs.get("hp", 0)
    ev_hp = evs.get(hp, 0)
    calculated_stats["hp"] = math.floor(((base_hp * 2 + iv_hp + math.floor(ev_hp/4)) * level) / 100) + level + 10

    # Calculate other stats
    for stat in ["attack", "defense", "special_attack", "special_defense", "speed"]:
        base_stat = base_stats.get(stat, 1)
        iv_stat = ivs.get(stat, 0)
        ev_stat = evs.get(stat, 0)
        nature_mod = nature_modifiers.get(stat, 1.0)
        calculated_stats[stat] = math.floor((math.floor(((base_stat * 2 + iv_stat + math.floor(ev_stat/4)) * level) / 100) + 5) * nature_mod)

    return calculated_stats

# Mapping from attribute CSV column names to multipliers
EFFECTIVENESS_MULTIPLIERS = {
    "attacking_id": 2.0,
    "defending_id": 0.5,
    "super_effective_id": 3.0,
    "none_effective_id": 0.0,
}

def calculate_damage(
    attacker: Pokemon,
    defender: Pokemon,
    skill: Skill,
    effectiveness: float,
    is_critical: bool,
    field_state: Dict[str, Any] # Placeholder for field effects
) -> int:
    """
    Calculates the damage dealt by a skill.

    Args:
        attacker: The attacking Pokemon.
        defender: The defending Pokemon.
        skill: The skill being used.
        effectiveness: The type effectiveness multiplier.
        is_critical: Whether the hit is critical.
        field_state: The current state of the battle field (weather, terrain, etc.).

    Returns:
        The calculated damage amount.
    """
    # Simplified damage calculation for now
    # TODO: Implement full damage formula including stats, level, STAB, items, abilities, field effects (S108 refinement)
    base_power = skill.power if skill.power is not None else 0
    # Assuming a basic formula: Damage = (Base Power * Att / Def * Modifier) * Effectiveness * Critical
    # This is a placeholder and needs to be replaced with a proper formula.
    # For now, just apply effectiveness and critical hit.
    damage = base_power * effectiveness
    if is_critical:
        damage *= 1.5 # Standard critical hit multiplier

    # Ensure damage is an integer and non-negative
    return max(0, int(damage))

def calculate_type_effectiveness(
    attacking_type_id: int,
    defending_type_ids: List[int],
    metadata_repo: MetadataRepository # Pass MetadataRepository instance
) -> float:
    """
    Calculates the type effectiveness multiplier based on the attacking skill's type
    and the defending Pokemon's type(s), using the rules from attributes.csv.

    Args:
        attacking_type_id: The ID of the attacking skill's type.
        defending_type_ids: A list of the defending Pokemon's type IDs.
        metadata_repo: The MetadataRepository instance to get attribute data.

    Returns:
        The total type effectiveness multiplier.
    """
    total_effectiveness = 0.0

    if not defending_type_ids:
        # Should not happen for valid Pokemon, but handle defensively
        return 1.0

    for def_type_id in defending_type_ids:
        def_attribute = metadata_repo.get_attribute(def_type_id)
        if not def_attribute:
            # Should not happen if data is consistent, but log a warning
            print(f"Warning: Could not find attribute data for ID: {def_type_id}") # Use logger later
            total_effectiveness += 1.0 # Assume normal effectiveness if data missing
            continue

        # Check against attacking_id, defending_id, super_effective_id, none_effective_id
        effectiveness_for_this_type = 1.0 # Default to normal effectiveness

        if def_attribute.attacking_id == attacking_type_id:
            effectiveness_for_this_type = EFFECTIVENESS_MULTIPLIERS["attacking_id"]
        elif def_attribute.defending_id == attacking_type_id:
            effectiveness_for_this_type = EFFECTIVENESS_MULTIPLIERS["defending_id"]
        elif def_attribute.super_effective_id == attacking_type_id:
            effectiveness_for_this_type = EFFECTIVENESS_MULTIPLIERS["super_effective_id"]
        elif def_attribute.none_effective_id == attacking_type_id:
            effectiveness_for_this_type = EFFECTIVENESS_MULTIPLIERS["none_effective_id"]
        # If none of the above match, effectiveness_for_this_type remains 1.0

        total_effectiveness += effectiveness_for_this_type

    # According to the user's rule, multipliers are added for dual types.
    # If a Pokemon has only one type, the loop runs once and total_effectiveness is the multiplier.
    # If a Pokemon has two types, the loop runs twice and total_effectiveness is the sum of multipliers.
    # This matches the user's description.

    return total_effectiveness

def check_accuracy(skill_accuracy: Optional[int], attacker_accuracy_stage: int, defender_evasion_stage: int, field_state: Dict[str, Any]) -> bool:
    """
    Checks if a skill hits based on accuracy, evasion, and field effects.

    Args:
        skill_accuracy: The skill's base accuracy (None for moves that never miss).
        attacker_accuracy_stage: The attacker's accuracy stage.
        defender_evasion_stage: The defender's evasion stage.
        field_state: The current state of the battle field (weather, terrain, etc.).

    Returns:
        True if the skill hits, False otherwise.
    """
    # TODO: Implement accuracy calculation including stat stages, abilities, items, field effects (S112 refinement)
    if skill_accuracy is None:
        return True # Moves with None accuracy never miss

    # Simplified check for now, ignoring stat stages and field effects
    hit_chance = skill_accuracy / 100.0
    return random.random() < hit_chance

def check_critical_hit(attacker: Pokemon, skill_critical_rate: int) -> bool:
    """
    Checks if a skill is a critical hit.

    Args:
        attacker: The attacking Pokemon.
        skill_critical_rate: The skill's critical hit ratio (e.g., 1, 2, 3).

    Returns:
        True if it's a critical hit, False otherwise.
    """
    # TODO: Implement critical hit calculation including critical hit ratio, abilities, items (S109 refinement)
    # Simplified check based on skill critical rate
    # Assuming critical_rate 1 = 6.25%, 2 = 12.5%, 3 = 50% (standard Pokemon rates)
    # This needs to be confirmed or adjusted based on game design.
    critical_chance = 0.0
    if skill_critical_rate == 1:
        critical_chance = 1/16 # 6.25%
    elif skill_critical_rate == 2:
        critical_chance = 1/8 # 12.5%
    elif skill_critical_rate == 3:
        critical_chance = 1/2 # 50%
    # Add more rates if needed

    return random.random() < critical_chance

def calculate_stat_stage_modifier(stage: int) -> float:
    """
    Calculates the stat modifier based on the stat stage.

    Args:
        stage: The stat stage (-6 to +6).

    Returns:
        The stat modifier (e.g., 1.5 for +2 Attack).
    """
    # TODO: Implement stat stage modifiers for different stats (accuracy/evasion are different) (S119 refinement)
    # Standard stat stage modifiers (Attack, Defense, Sp. Atk, Sp. Def, Speed)
    if stage > 0:
        return (2 + stage) / 2.0
    elif stage < 0:
        return 2.0 / (2 - stage)
    else:
        return 1.0

def get_effective_stat(pokemon: Pokemon, stat_type: str) -> int:
    """
    Calculates the effective stat value considering base stats, IVs, EVs, nature, and stat stages.

    Args:
        pokemon: The Pokemon instance.
        stat_type: The type of stat (e.g., "attack", "defense").

    Returns:
        The effective stat value.
    """
    # TODO: Implement full effective stat calculation (S111 refinement)
    # This requires accessing base stats from Race, IVs, EVs, Nature modifier, and stat stages.
    # For now, return a placeholder or base stat + stage modifier effect on base stat
    base_stat = getattr(pokemon, stat_type, 0) # Get base stat from Pokemon instance (which should include IVs/EVs/Nature eventually)
    stage = pokemon.stat_stages.get(stat_type, 0)
    modifier = calculate_stat_stage_modifier(stage)

    # This is a very simplified approach. A proper implementation needs base stats from Race, IVs, EVs, Nature.
    # For now, let's just apply the stage modifier to the current stat value (which is a placeholder).
    # A better placeholder might be to use base stats from the race.
    # Let's assume pokemon.base_stats is available (needs to be loaded into Pokemon instance)
    # effective_stat = int(pokemon.base_stats.get(stat_type, 0) * modifier) # This is still not quite right without IVs/EVs/Nature

    # Let's use the current stat value as a base for now, acknowledging this is a placeholder.
    effective_stat = int(base_stat * modifier)

    return max(1, effective_stat) # Stat should be at least 1

def check_run_success(player_speed: int, wild_speed: int, run_attempts: int) -> bool:
    """
    Checks if running from a wild battle is successful.

    Args:
        player_speed: The player's active Pokemon's speed stat.
        wild_speed: The wild Pokemon's speed stat.
        run_attempts: The number of previous run attempts in this battle.

    Returns:
        True if running is successful, False otherwise.
    """
    # TODO: Implement run success formula (S116 refinement)
    # Standard formula: Chance = ( (PlayerSpeed * 128 / WildSpeed) + 30 * RunAttempts ) % 256
    # If Chance > random_byte (0-255), success. If WildSpeed > PlayerSpeed and Chance < 256, always success.
    # This is a simplified placeholder.
    if player_speed > wild_speed:
        return True
    elif wild_speed > 0:
        # Simplified chance calculation
        chance = (player_speed * 128 // wild_speed) + 30 * run_attempts
        return chance > random.randint(0, 255)
    else:
        return True # Cannot fail to run from a Pokemon with 0 speed

def calculate_catch_rate_value_A(
    wild_pokemon: Pokemon,
    pokeball_catch_rate: int,
    status_effect: Optional[StatusEffect] # Status effect multiplier
) -> int:
    """
    Calculates the value 'A' used in the catch rate formula.

    Args:
        wild_pokemon: The wild Pokemon instance.
        pokeball_catch_rate: The catch rate modifier of the used Pokeball.
        status_effect: The major status effect of the wild Pokemon (if any).

    Returns:
        The calculated value 'A'.
    """
    # TODO: Implement full catch rate value A calculation including HP, status, pokeball (S117 refinement)
    # Standard formula: A = ( (WildPokemonMaxHP * 3 - WildPokemonCurrentHP * 2) * WildPokemonCatchRate * PokeballCatchRate ) / (WildPokemonMaxHP * 3)
    # If status effect (sleep or freeze), A *= 2. If status effect (paralysis, poison, burn), A *= 1.5.
    # This is a simplified placeholder.
    if wild_pokemon.max_hp == 0: # Avoid division by zero
        return 0

    hp_factor = (wild_pokemon.max_hp * 3 - wild_pokemon.current_hp * 2) / (wild_pokemon.max_hp * 3)
    # Assuming wild_pokemon.race.catch_rate is available
    # catch_rate_value = int(hp_factor * wild_pokemon.race.catch_rate * pokeball_catch_rate) # Needs race data

    # Placeholder using a fixed base catch rate
    base_catch_rate = 100 # Example base catch rate
    catch_rate_value = int(hp_factor * base_catch_rate * pokeball_catch_rate)

    # Apply status effect multiplier
    if status_effect:
        if status_effect.logic_key in ['sleep', 'freeze']: # Assuming logic keys for sleep/freeze
            catch_rate_value = int(catch_rate_value * 2.0)
        elif status_effect.logic_key in ['paralysis', 'poison', 'burn']: # Assuming logic keys
            catch_rate_value = int(catch_rate_value * 1.5)

    return max(1, catch_rate_value) # Value A should be at least 1

def perform_catch_shakes(value_A: int) -> int:
    """
    Simulates the shakes of a Pokeball and determines the number of shakes.

    Args:
        value_A: The calculated value 'A' from the catch rate formula.

    Returns:
        The number of shakes (0 to 4). 4 indicates a successful catch.
    """
    # TODO: Implement catch shake logic (S117 refinement)
    # Standard logic: Calculate value B = 65536 * (Value A / 255)^0.1875
    # Generate 4 random numbers between 0 and 65535. If all 4 are less than B, catch succeeds (4 shakes).
    # Otherwise, the number of shakes is the count of random numbers less than B.
    # This is a simplified placeholder.
    if value_A >= 255:
        return 4 # Always catch if A is 255 or more

    # Simplified shake simulation
    shakes = 0
    # A very basic chance based on A
    catch_chance_per_shake = value_A / 255.0 # Simplified
    for _ in range(4):
        if random.random() < catch_chance_per_shake:
            shakes += 1
        else:
            break # Stop shaking if one fails

    return shakes

def calculate_exp_needed(level: int, growth_rate: str) -> int:
    """
    Calculates the total experience needed to reach a given level
    based on the pokemon's growth rate.
    This is a placeholder; actual formulas vary by growth rate type.
    """
    # Implement actual Pokemon growth rate formulas here based on the growth_rate string.
    # Growth rates: Fast, Medium Fast, Medium Slow, Slow, Erratic, Fluctuating
    # Formulas are well-documented online.

    # Example for Medium Fast (n^3):
    if growth_rate == "medium_fast":
        return level ** 3
    # Example for Slow (5*n^4 / 4):
    elif growth_rate == "slow":
        return math.floor(5 * (level ** 4) / 4)
    # Add other growth rates...
    else:
        # Default to Medium Fast or raise an error
        return level ** 3 # Defaulting for MVP

def calculate_exp_gain(defeated_pokemon: Pokemon, player_pokemon_level: int, is_trainer_battle: bool = False) -> int:
    """
    Calculates the base experience points gained from defeating a pokemon.
    Formula: (BaseExpYield * Level / 7) * (1 if trainer battle else 1.5)
    Simplified formula, actual formula is more complex and includes factors like:
    - Traded Pokemon bonus (1.5x or 1.7x)
    - Lucky Egg (1.5x)
    - Friendship (Gen 8+)
    - Evolution
    - Number of participants
    """
    race_data = defeated_pokemon.race # Assuming defeated_pokemon has race data
    if not race_data or race_data.base_exp_yield is None:
        logger.warning(f"Defeated pokemon instance {defeated_pokemon.instance_id} ({defeated_pokemon.nickname}) missing race data or base_exp_yield. Returning 0 EXP.")
        return 0

    # Ensure defeated pokemon has a level
    defeated_level = defeated_pokemon.level if defeated_pokemon.level is not None else 1

    # Base EXP calculation
    # Formula: (BaseExpYield * Level / 7)
    base_exp = math.floor((race_data.base_exp_yield * defeated_level) / 7)

    # Trainer battle modifier (wild pokemon give 1x, trainer pokemon give 1.5x in some gens)
    # Let's use 1x for wild and 1.5x for trainer for now.
    trainer_modifier = 1.5 if is_trainer_battle else 1.0
    exp_gain = math.floor(base_exp * trainer_modifier)

    # TODO: Add other EXP modifiers (Lucky Egg, Trade bonus, etc.) (S3 refinement)

    # Ensure minimum EXP gain is 1
    exp_gain = max(1, exp_gain)

    logger.debug(f"Calculated EXP gain for defeating {defeated_pokemon.nickname} (Level {defeated_level}, Base EXP {race_data.base_exp_yield}): {exp_gain}")

    return exp_gain

def check_item_drop(defeated_pokemon: Pokemon) -> Optional[int]:
    """
    Checks if a defeated pokemon drops an item and returns the item ID if it does.
    Based on the pokemon's race data which includes item_drop_chance and item_drop_id.
    """
    race_data = defeated_pokemon.race # Assuming defeated_pokemon has race data
    if not race_data or race_data.item_drop_chance is None or race_data.item_drop_id is None:
        logger.debug(f"Defeated pokemon instance {defeated_pokemon.instance_id} ({defeated_pokemon.nickname}) has no item drop configured.")
        return None

    drop_chance = race_data.item_drop_chance
    item_id = race_data.item_drop_id

    # Ensure drop chance is between 0 and 1
    drop_chance = max(0.0, min(1.0, drop_chance))

    # Roll the dice
    if random.random() < drop_chance:
        logger.debug(f"Defeated pokemon {defeated_pokemon.nickname} dropped item ID {item_id} (Chance: {drop_chance:.2f})")
        return item_id
    else:
        logger.debug(f"Defeated pokemon {defeated_pokemon.nickname} did not drop an item (Chance: {drop_chance:.2f})")
        return None

# Constants for stat stage modifiers
STAT_STAGE_MODIFIERS = {
    # Attack, Defense, Special Attack, Special Defense, Speed
    -6: 2/8,
    -5: 2/7,
    -4: 2/6,
    -3: 2/5,
    -2: 2/4,
    -1: 2/3,
    0: 1,
    1: 3/2,
    2: 4/2,
    3: 5/2,
    4: 6/2,
    5: 7/2,
    6: 8/2,
}

ACCURACY_EVASION_STAGE_MODIFIERS = {
    # Accuracy, Evasion
    -6: 3/9,
    -5: 3/8,
    -4: 3/7,
    -3: 3/6,
    -2: 3/5,
    -1: 3/4,
    0: 1,
    1: 4/3,
    2: 5/3,
    3: 6/3,
    4: 7/3,
    5: 8/3,
    6: 9/3,
}

def calculate_accuracy(attacker: Pokemon, defender: Pokemon, skill: Skill) -> float:
    """
    Calculates the effective accuracy of a skill, considering attacker's accuracy stage
    and defender's evasion stage.
    Formula: SkillAccuracy * (AttackerAccuracyModifier / DefenderEvasionModifier)
    Accuracy and Evasion stages range from -6 to +6.
    """
    if skill.accuracy is None:
        logger.debug(f"Skill {skill.name} has no accuracy (status move or always hits). Returning 100%.")
        return 1.0 # Moves with None accuracy always hit (e.g., status moves)

    # Get accuracy and evasion stage modifiers
    # Assuming Pokemon model has accuracy_stage and evasion_stage attributes
    attacker_acc_modifier = ACCURACY_EVASION_STAGE_MODIFIERS.get(attacker.accuracy_stage, 1.0)
    defender_eva_modifier = ACCURACY_EVASION_STAGE_MODIFIERS.get(defender.evasion_stage, 1.0)

    # Avoid division by zero if evasion modifier is somehow zero (shouldn't happen with defined stages)
    if defender_eva_modifier <= 0:
        logger.warning(f"Defender {defender.nickname} has invalid evasion modifier ({defender_eva_modifier}). Using 1.0.")
        defender_eva_modifier = 1.0

    # Calculate effective accuracy
    effective_accuracy = skill.accuracy * (attacker_acc_modifier / defender_eva_modifier)

    # Accuracy cannot be less than 0 or greater than 100 (or some game-specific cap)
    # Let's cap between 0 and 100 for simplicity (represented as 0.0 to 1.0)
    effective_accuracy = max(0.0, min(1.0, effective_accuracy))

    logger.debug(f"Calculated effective accuracy for {skill.name} ({attacker.nickname} vs {defender.nickname}): {effective_accuracy:.2f}")

    return effective_accuracy

def check_accuracy(attacker: Pokemon, defender: Pokemon, skill: Skill) -> bool:
    """
    Checks if a skill hits based on its effective accuracy.
    Returns True if hit, False otherwise.
    """
    if skill.accuracy is None:
        return True # Moves with None accuracy always hit

    effective_accuracy = calculate_accuracy(attacker, defender, skill)

    # Generate a random number between 0 and 1
    random_roll = random.random()

    # Hit if random roll is less than effective accuracy
    if random_roll < effective_accuracy:
        logger.debug(f"Skill {skill.name} hit ({random_roll:.2f} < {effective_accuracy:.2f}).")
        return True
    else:
        logger.debug(f"Skill {skill.name} missed ({random_roll:.2f} >= {effective_accuracy:.2f}).")
        return False

def calculate_critical_hit_chance(attacker: Pokemon, skill: Skill) -> float:
    """
    Calculates the chance of a critical hit.
    Simplified formula: Base chance (e.g., 1/16 or 6.25%) + modifiers from skill/ability/item.
    For MVP, let's use a base chance and potentially a skill modifier.
    """
    # Base critical hit chance (e.g., 1/16 = 0.0625)
    base_chance = 0.0625

    # Skill-specific critical hit ratio (e.g., some skills have higher crit chance)
    # Assuming Skill model has a critical_hit_ratio attribute (e.g., 1 for normal, 2 for high crit)
    skill_crit_modifier = skill.critical_hit_ratio if hasattr(skill, 'critical_hit_ratio') and skill.critical_hit_ratio is not None else 1

    # Apply skill modifier (simplified: ratio * base chance)
    # Actual formula is more complex, often affecting the 'stage' of crit chance.
    # For MVP, let's just multiply for simplicity.
    critical_hit_chance = base_chance * skill_crit_modifier

    # Cap the chance (e.g., max 50% or 100% depending on generation/modifiers)
    # Let's cap at 1.0 (100%) for simplicity.
    critical_hit_chance = min(1.0, critical_hit_chance)

    logger.debug(f"Calculated critical hit chance for {skill.name} ({attacker.nickname}): {critical_hit_chance:.2f}")

    return critical_hit_chance

def check_critical_hit(attacker: Pokemon, skill: Skill) -> bool:
    """
    Checks if an attack is a critical hit.
    Returns True if critical hit, False otherwise.
    """
    critical_hit_chance = calculate_critical_hit_chance(attacker, skill)

    # Generate a random number between 0 and 1
    random_roll = random.random()

    # Critical hit if random roll is less than critical hit chance
    if random_roll < critical_hit_chance:
        logger.debug(f"Skill {skill.name} is a critical hit ({random_roll:.2f} < {critical_hit_chance:.2f}).")
        return True
    else:
        logger.debug(f"Skill {skill.name} is not a critical hit ({random_roll:.2f} >= {critical_hit_chance:.2f}).")
        return False

def calculate_stat_stage_modifier(stage: int, is_accuracy_evasion: bool = False) -> float:
    """
    Calculates the modifier for a stat based on its stage.
    Stages range from -6 to +6.
    Accuracy and Evasion use a different set of modifiers.
    """
    if is_accuracy_evasion:
        return ACCURACY_EVASION_STAGE_MODIFIERS.get(stage, 1.0)
    else:
        return STAT_STAGE_MODIFIERS.get(stage, 1.0)

# Terrain damage modifiers (example, based on field_effects.csv)
# Structure: {terrain_logic_key: {skill_type_id: multiplier}}
TERRAIN_DAMAGE_MODIFIERS: Dict[str, Dict[int, float]] = {
    "electric_terrain_effect": {13: 1.5}, # Electric Terrain boosts Electric (type 13) moves by 1.5x
    "grassy_terrain_effect": {11: 1.5}, # Grassy Terrain boosts Grass (type 11) moves by 1.5x
    "psychic_terrain_effect": {14: 1.5}, # Psychic Terrain boosts Psychic (type 14) moves by 1.5x
    "misty_terrain_effect": {16: 0.5}, # Misty Terrain weakens Dragon (type 16) moves by 0.5x
    # Add other terrain effects as needed
}

# Need a way to get type ID from type name or load a full type chart
# For now, using placeholder type IDs based on common practice (e.g., 13 for Electric)
# TODO: Load actual type IDs and effectiveness from metadata (S31 refinement)

async def calculate_damage(attacker: Pokemon, defender: Pokemon, skill: Skill, battle: Battle, metadata_repo: MetadataRepository) -> int:
    """
    Calculates the damage a skill deals to a target.

    Formula based on Generation V onwards:
    Damage = (((((2 * Level / 5) + 2) * AttackStat * SkillPower / DefenseStat) / 50) + 2) * Modifier

    Modifier includes:
    - STAB (Same Type Attack Bonus): 1.5x if skill type matches attacker's type
    - Type Effectiveness: 0x, 0.25x, 0.5x, 1x, 2x, 4x based on skill type and defender's type(s)
    - Critical Hit: 1.5x (Gen 6+)
    - Random Factor: 0.85 to 1.0
    - Weather: 1.5x or 0.5x for certain types/moves
    - Terrain: 1.5x or 0.5x for certain types/moves
    - Burn: 0.5x physical damage if attacker is burned
    - Other modifiers (Items, Abilities, etc.) - TODO

    Args:
        attacker: The attacking Pokemon.
        defender: The defending Pokemon.
        skill: The skill being used.
        battle: The current battle object (for weather/terrain).
        metadata_repo: The MetadataRepository to access game data.

    Returns:
        The calculated damage amount.
    """
    if skill.power is None:
        # Non-damaging moves have 0 damage in this context
        return 0

    level = attacker.level
    skill_power = skill.power

    # Determine Attack and Defense stats based on skill category
    if skill.category == 'physical':
        attack_stat = attacker.attack
        defense_stat = defender.defense
    elif skill.category == 'special':
        attack_stat = attacker.special_attack
        defense_stat = defender.special_defense
    else:
        # Status moves or other categories don't deal direct damage
        return 0

    # Apply stat stage modifiers
    # TODO: Need to track stat stages in Pokemon model (S32 refinement)
    # attack_stat *= calculate_stat_stage_modifier(attacker.attack_stage)
    # defense_stat *= calculate_stat_stage_modifier(defender.defense_stage)

    # Basic Damage Calculation
    # Ensure no division by zero if defense_stat is 0 (shouldn't happen with base stats > 0, but good practice)
    if defense_stat <= 0:
        defense_stat = 1

    damage = ((((2 * level / 5) + 2) * attack_stat * skill_power / defense_stat) / 50) + 2

    # --- Modifiers ---
    modifier = 1.0

    # 1. STAB (Same Type Attack Bonus)
    # Check if skill type matches any of the attacker's types
    # TODO: Need attacker's types as Attribute objects or IDs (S33 refinement)
    # Assuming attacker.types is a list of type IDs for now
    attacker_type_ids = [t.attribute_id for t in attacker.types] # Assuming attacker.types are Attribute objects
    if skill.skill_type in attacker_type_ids:
        modifier *= 1.5
        logger.debug(f"STAB applied ({modifier}x)")

    # 2. Type Effectiveness
    # Calculate effectiveness against all defender's types
    # TODO: Need defender's types as Attribute objects or IDs (S34 refinement)
    # Assuming defender.types is a list of type IDs for now
    defender_type_ids = [t.attribute_id for t in defender.types] # Assuming defender.types are Attribute objects
    type_effectiveness_multiplier = calculate_type_effectiveness(skill.skill_type, defender_type_ids, metadata_repo) # Pass metadata_repo
    modifier *= type_effectiveness_multiplier
    logger.debug(f"Type Effectiveness applied ({type_effectiveness_multiplier}x)")

    # 3. Critical Hit
    if check_critical_hit(attacker, skill):
        modifier *= 1.5 # Critical hit multiplier (Gen 6+)
        logger.debug(f"Critical hit modifier applied (1.5x)")

    # 4. Random Factor (0.85 to 1.0)
    random_factor = random.randint(85, 100) / 100.0
    modifier *= random_factor
    logger.debug(f"Random Factor applied ({random_factor}x)")

    # 5. Weather (TODO: Implement weather effects) (S36 refinement)
    # if battle.weather:
    #     weather_modifier = 1.0
    #     # Example: Sunny weather boosts Fire moves (type 10), weakens Water moves (type 11)
    #     if battle.weather == 'sunny_effect':
    #         if skill.skill_type == 10: weather_modifier = 1.5
    #         elif skill.skill_type == 11: weather_modifier = 0.5
    #     # Example: Rainy weather boosts Water moves (type 11), weakens Fire moves (type 10)
    #     elif battle.weather == 'rainy_effect':
    #         if skill.skill_type == 11: weather_modifier = 1.5
    #         elif skill.skill_type == 10: weather_modifier = 0.5
    #     # Add other weather effects...
    #     modifier *= weather_modifier
    #     logger.debug(f"Weather ({battle.weather}) modifier applied ({weather_modifier}x)")

    # 6. Terrain (Implement terrain effects based on loaded data)
    if battle.terrain:
        terrain_modifier = 1.0
        # Get terrain data using the logic key
        terrain_data = metadata_repo.get_field_effect(battle.terrain)
        if terrain_data:
            # Check if the current terrain has a damage modifier for the skill's type
            # Use the TERRAIN_DAMAGE_MODIFIERS dictionary
            if battle.terrain in TERRAIN_DAMAGE_MODIFIERS:
                if skill.skill_type in TERRAIN_DAMAGE_MODIFIERS[battle.terrain]:
                    terrain_modifier = TERRAIN_DAMAGE_MODIFIERS[battle.terrain][skill.skill_type]
                    modifier *= terrain_modifier
                    logger.debug(f"Terrain ({battle.terrain}) modifier applied ({terrain_modifier}x) for skill type {skill.skill_type}")
            # TODO: Add logic for terrain effects that are not simple damage multipliers (e.g., Grassy Terrain healing) (S37 refinement)
            # These effects might be handled elsewhere in battle_logic.py

    # 7. Burn (TODO: Implement burn effect) (S38 refinement)
    # if attacker.has_status('burn') and skill.category == 'physical':
    #     modifier *= 0.5
    #     logger.debug("Burn modifier applied (0.5x)")

    # 8. Other modifiers (Items, Abilities, etc.) (TODO: Implement) (S39 refinement)

    # Final Damage Calculation
    final_damage = math.floor(damage * modifier)

    # Ensure minimum damage is 1 if the attack is supposed to deal damage, unless effectiveness is 0
    if final_damage <= 0 and skill.power > 0 and type_effectiveness_multiplier > 0:
        final_damage = 1

    logger.debug(f"Calculated final damage: {final_damage}")

    return final_damage

def calculate_exp_needed(level: int, growth_rate: str) -> int:
    """
    Calculates the total experience needed to reach the given level for a specific growth rate.
    This is a placeholder and needs to be implemented based on actual growth rate formulas.
    """
    # Placeholder implementation - needs actual formulas for different growth rates
    # Example: Medium Fast growth rate (simplification)
    if growth_rate == "medium_fast":
        return level ** 3
    # Add other growth rates...
    logger.warning(f"Experience needed calculation for growth rate '{growth_rate}' is a placeholder.")
    return level * 100 # Default placeholder
