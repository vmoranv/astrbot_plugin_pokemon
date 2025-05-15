# backend/core/pet/pet_grow.py

from backend.models.pokemon import Pokemon
from backend.models.race import Race # Need Race data for base stats and growth rate
# from backend.core.battle import formulas # Example dependency - formulas should be in core.battle
from backend.core.battle.formulas import calculate_stats # Assuming this function exists
from backend.core.pet.pet_evolution import check_evolution # Assuming this function exists
from backend.models.skill import Skill # Need Skill data for learning new skills

async def gain_experience(pokemon: Pokemon, exp_amount: int, race_data: Race, skills_data: List[Skill]) -> List[str]:
    """
    Adds experience to a pokemon and checks for level up.
    Returns a list of messages about level ups and new skills learned.
    Requires Race data for growth rate and Skills data for level-up moves.
    """
    messages = []
    pokemon.experience += exp_amount
    logger.debug(f"Pokemon {pokemon.nickname} gained {exp_amount} EXP. Total EXP: {pokemon.experience}")

    # Check for level up
    # Need a way to get EXP needed for the next level based on growth rate (from Race data)
    # Assuming a function calculate_exp_needed(level, growth_rate) exists in formulas or here
    while pokemon.level < 100: # Assuming max level is 100
        exp_needed_for_next_level = calculate_exp_needed(pokemon.level + 1, race_data.growth_rate) # Assuming growth_rate is on Race model
        if pokemon.experience >= exp_needed_for_next_level:
            await level_up(pokemon, race_data, skills_data)
            messages.append(f"{pokemon.nickname} 升到了 {pokemon.level} 级！")
            # After leveling up, check if enough EXP for the *next* level
        else:
            break # Not enough EXP for the next level

    # Note: Saving the updated pokemon object is the responsibility of the Service layer.
    return messages

async def level_up(pokemon: Pokemon, race_data: Race, skills_data: List[Skill]) -> None:
    """
    Levels up a pokemon and updates its stats.
    Checks for new skills learned and potential evolution.
    Requires Race data for base stats/growth and Skills data for level-up moves.
    """
    pokemon.level += 1
    logger.info(f"Leveling up {pokemon.nickname} to level {pokemon.level}")

    # Recalculate stats based on new level, base stats, IVs, EVs, Nature (using formulas)
    # Assuming calculate_stats function exists in core.battle.formulas
    pokemon.stats = calculate_stats(pokemon, race_data) # Update the stats attribute

    # Check for new skills learned at this level (from Race data via MetadataService - passed in)
    # Assuming Race data includes a list of skills learned at each level
    new_skills_learned = [
        skill for skill in skills_data
        if skill.learn_level == pokemon.level and skill.skill_id not in [s.skill_id for s in pokemon.skills]
    ]
    for new_skill in new_skills_learned:
        # Attempt to learn the skill. pet_skill.learn_skill handles the logic of adding it.
        # If the pokemon already knows 4 moves, learn_skill will return False.
        # In a real game, the player might be prompted to forget a move.
        # For simplicity here, we'll just try to learn it.
        learned = await learn_skill(pokemon, new_skill) # Call core.pet.pet_skill function
        if learned:
            logger.info(f"{pokemon.nickname} 学会了 {new_skill.name}！")
            # A message about learning the skill should be added in the calling Service layer
            # after checking the return value of this function.

    # Check for evolution (using pet_evolution)
    # check_evolution should return the ID of the next race if evolution is possible
    next_race_id = await check_evolution(pokemon, race_data) # Call core.pet.pet_evolution function
    if next_race_id is not None:
        logger.info(f"{pokemon.nickname} is ready to evolve!")
        # The actual evolution process (changing race_id, recalculating stats, etc.)
        # should likely happen in the Service layer after confirming the evolution.
        # This core function just indicates that evolution is possible.
        pokemon.can_evolve_to = next_race_id # Add a flag or attribute to the Pokemon model

    # Note: Saving the updated pokemon object is the responsibility of the Service layer.

# Add other growth related functions (EV/IV management)

# Helper function (could be in formulas.py)
def calculate_exp_needed(level: int, growth_rate: str) -> int:
    """
    Calculates the total experience needed to reach a given level
    based on the pokemon's growth rate.
    This is a placeholder; actual formulas vary by growth rate type.
    """
    # Example simplified formula (e.g., Medium Fast)
    # EXP = level^3
    # This needs to be replaced with actual Pokemon growth rate formulas (Fast, Medium Fast, Medium Slow, Slow, Erratic, Fluctuating)
    # The growth_rate string from Race data would determine which formula to use.
    # For MVP, a simple formula or lookup table can be used.
    # Let's use a very simple placeholder:
    return level * level * 100 # Very simplified placeholder
