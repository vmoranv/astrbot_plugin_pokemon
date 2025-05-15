# backend/core/pet/pet_item.py

from typing import Optional
from backend.models.pokemon import Pokemon
from backend.models.item import Item # Need Item data
# from backend.core.pet import pet_grow # Example dependency
# from backend.core.battle import status_effect # Example dependency

# Core logic functions should receive necessary data as arguments.

async def use_item_on_pokemon(pokemon: Pokemon, item: Item) -> str:
    """
    Uses a consumable item on a pokemon.
    Applies item effects (healing, status recovery, stat boosts, etc.).
    Returns a message describing the result.
    Requires the Pokemon instance and the Item data.
    """
    # This is pure logic based on the Item's properties and the Pokemon's current state.
    # It should not interact with inventory management (that's Service layer).

    # Assume Item data includes information about its effects.
    # Example structure for item effects in Item model:
    # item.effects = [
    #     {"type": "heal_hp", "value": 50}, # Heals 50 HP
    #     {"type": "heal_status", "value": "poison"}, # Heals poison status
    #     {"type": "boost_stat", "stat": "attack", "value": 1}, # Raises Attack stage by 1
    #     {"type": "add_experience", "value": 100}, # Gives 100 EXP (e.g., Rare Candy)
    # ]

    result_messages = []

    if not item.effects:
        return f"{item.name} 对 {pokemon.nickname} 没有效果。"

    for effect in item.effects:
        effect_type = effect.get("type")
        effect_value = effect.get("value")
        effect_stat = effect.get("stat") # For stat boosts

        if effect_type == "heal_hp":
            # Heal HP, but not above max HP
            heal_amount = effect_value
            healed = min(heal_amount, pokemon.max_hp - pokemon.current_hp)
            if healed > 0:
                pokemon.current_hp += healed
                result_messages.append(f"{pokemon.nickname} 恢复了 {healed} 点 HP。")
            else:
                 result_messages.append(f"{pokemon.nickname} 的 HP 已经满了。")

        elif effect_type == "heal_status":
            # Heal a specific status effect
            status_to_heal = effect_value # e.g., "poison", "paralysis", "burn", "sleep", "freeze"
            # Assuming Pokemon model has a method to remove status effects
            if pokemon.remove_status_effect(status_to_heal):
                 result_messages.append(f"{pokemon.nickname} 的 {status_to_heal} 状态被治愈了。")
            else:
                 result_messages.append(f"{pokemon.nickname} 没有 {status_to_heal} 状态。")

        elif effect_type == "heal_all_status":
             # Heal all major status effects
             healed_any = False
             for status in ["poison", "paralysis", "burn", "sleep", "freeze"]:
                 if pokemon.remove_status_effect(status):
                     healed_any = True
             if healed_any:
                 result_messages.append(f"{pokemon.nickname} 的所有异常状态都被治愈了。")
             else:
                 result_messages.append(f"{pokemon.nickname} 没有异常状态。")


        elif effect_type == "boost_stat":
            # Boost a specific stat stage (e.g., +1 Attack stage)
            stat_to_boost = effect_stat # e.g., "attack", "defense", "speed", etc.
            boost_amount = effect_value # e.g., 1, 2
            # Assuming Pokemon model has a method to adjust stat stages
            if pokemon.adjust_stat_stage(stat_to_boost, boost_amount):
                 result_messages.append(f"{pokemon.nickname} 的 {stat_to_boost} 提高了！") # Simplified message
            else:
                 result_messages.append(f"{pokemon.nickname} 的 {stat_to_boost} 无法再提高了。")

        elif effect_type == "add_experience":
            # Add experience (like Rare Candy)
            exp_amount = effect_value
            # This should call the gain_experience function in pet_grow
            from backend.core.pet.pet_grow import gain_experience # Import here to avoid circular dependency
            # Need Race data and Skills data for gain_experience - these should be passed in from the Service layer
            # For simplicity in this core function, we'll just add EXP directly,
            # but the Service layer should call gain_experience which handles level ups.
            # pokemon.experience += exp_amount
            # result_messages.append(f"{pokemon.nickname} 获得了 {exp_amount} 点经验。")
            # A better approach: The Service layer calls this use_item_on_pokemon,
            # and if the item effect is "add_experience", the Service layer then calls pet_grow.gain_experience.
            # So, this core function might just return a list of effects applied, and the Service layer
            # interprets them and calls other core functions as needed.
            # Let's revise: This function applies effects that modify the Pokemon object directly.
            # EXP gain leading to level up is a process, not a direct object modification here.
            # So, for EXP, this function might just indicate that EXP should be added.
            # Or, for simplicity in MVP, we can let it add EXP and assume the Service layer
            # will then check for level ups after this function returns.
            pokemon.experience += exp_amount
            result_messages.append(f"{pokemon.nickname} 获得了 {exp_amount} 点经验。")


        # Add other effect types (e.g., revive, change form, learn move, change nature, add EVs)

    # Note: Saving the updated pokemon object is the responsibility of the Service layer.
    return " ".join(result_messages) if result_messages else f"{item.name} 对 {pokemon.nickname} 没有明显效果。"

# Add other item related functions that affect pokemon (e.g., give_held_item, take_held_item)
