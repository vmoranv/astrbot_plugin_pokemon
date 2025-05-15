# backend/core/pet/pet_skill.py

from typing import List, Optional
from backend.models.pokemon import Pokemon
from backend.models.skill import Skill
# from backend.services.metadata_service import MetadataService # Example dependency - Core should not depend on Services

# Core logic functions should receive necessary data as arguments, not fetch it themselves.

async def learn_skill(pokemon: Pokemon, skill: Skill) -> bool:
    """
    Teaches a skill to a pokemon.
    Checks if the pokemon can learn the skill and if there is space.
    Returns True if learned, False otherwise.
    """
    # This is pure logic based on the Pokemon and Skill objects.
    # Actual checks (e.g., if pokemon's race can learn this skill) should be done in the Service layer
    # before calling this core function, potentially using MetadataService.

    # Example logic (simplified):
    if len(pokemon.skills) >= 4: # Assuming a max of 4 skills
        # Cannot learn more skills
        return False

    if skill.skill_id in [s.skill_id for s in pokemon.skills]:
        # Already knows this skill
        return False

    # Add the skill to the pokemon's skills list
    pokemon.skills.append(skill)
    # Note: Saving the updated pokemon object is the responsibility of the Service layer.
    return True

async def forget_skill(pokemon: Pokemon, skill_id: int) -> bool:
    """
    Makes a pokemon forget a skill by its ID.
    Returns True if forgotten, False if skill not found.
    """
    # Example logic (simplified):
    initial_skill_count = len(pokemon.skills)
    pokemon.skills = [s for s in pokemon.skills if s.skill_id != skill_id]

    # Return True if the skill count decreased, meaning a skill was removed
    return len(pokemon.skills) < initial_skill_count

async def use_skill(attacker: Pokemon, target: Pokemon, skill: Skill) -> str:
    """
    Executes a skill in battle.
    Applies skill effects (damage, status, stat changes, etc.).
    Returns a description of the skill usage result.
    This is a simplified placeholder; actual battle logic is complex.
    """
    # This function would interact with battle formulas and potentially status/field effects logic
    # within the core layer. It should not interact with external services or data access.

    # Example placeholder logic:
    result_message = f"{attacker.nickname}使用了{skill.name}！"

    # In a real implementation, this would involve:
    # 1. Calculating damage using formulas based on attacker/target stats, skill power, type effectiveness, etc.
    # 2. Applying status effects (poison, paralysis, etc.) with a certain probability.
    # 3. Applying stat changes (attack up, defense down, etc.).
    # 4. Handling other skill effects (healing, entry hazards, etc.).
    # 5. Updating attacker and target Pokemon objects (e.g., reducing HP, adding status effects).

    # Example: Apply damage (simplified)
    # damage = calculate_damage(attacker, target, skill) # Assuming a formula function exists
    # target.current_hp -= damage
    # result_message += f" 造成了 {damage} 点伤害。"

    # Example: Apply status effect (simplified)
    # if skill.status_effect and random.random() < skill.status_chance: # Assuming status_effect and status_chance on Skill model
    #     target.add_status_effect(skill.status_effect) # Assuming method on Pokemon model
    #     result_message += f" {target.nickname} 中毒了！" # Example message

    return result_message

# Add other skill related functions as needed (e.g., get_available_skills_at_level)
