from typing import Dict, List, Optional, Tuple
from backend.models.pokemon import Pokemon
from backend.models.item import Item
from backend.utils.logger import get_logger

logger = get_logger(__name__)

async def equip_item(pokemon: Pokemon, item: Item) -> Tuple[bool, str]:
    """
    为宝可梦装备道具。
    
    Args:
        pokemon: 要装备道具的宝可梦
        item: 要装备的道具
        
    Returns:
        成功与否的布尔值和结果消息的元组
    """
    # 检查道具是否可装备
    if not item.is_equippable:
        return False, f"{item.name}不是可装备的道具。"
    
    # 检查宝可梦是否已经装备了道具
    if pokemon.held_item:
        return False, f"{pokemon.nickname}已经持有了{pokemon.held_item.name}，请先卸下当前道具。"
    
    # 检查道具是否适合该宝可梦（例如某些道具只有特定种族或类型可以使用）
    if not _check_item_compatibility(pokemon, item):
        return False, f"{pokemon.nickname}无法使用{item.name}。"
    
    # 装备道具
    pokemon.held_item = item
    
    # 应用道具效果
    _apply_held_item_effects(pokemon, item)
    
    return True, f"{pokemon.nickname}成功装备了{item.name}。"

async def unequip_item(pokemon: Pokemon) -> Tuple[bool, str, Optional[Item]]:
    """
    从宝可梦身上卸下道具。
    
    Args:
        pokemon: 要卸下道具的宝可梦
        
    Returns:
        成功与否的布尔值、结果消息和卸下的道具（如果有）的元组
    """
    # 检查宝可梦是否装备了道具
    if not pokemon.held_item:
        return False, f"{pokemon.nickname}没有装备任何道具。", None
    
    # 获取当前装备的道具
    item = pokemon.held_item
    
    # 移除道具效果
    _remove_held_item_effects(pokemon, item)
    
    # 卸下道具
    removed_item = pokemon.held_item
    pokemon.held_item = None
    
    return True, f"从{pokemon.nickname}身上卸下了{removed_item.name}。", removed_item

async def get_equipment_effects(pokemon: Pokemon) -> Dict[str, int]:
    """
    获取宝可梦当前装备道具提供的效果。
    
    Args:
        pokemon: 要查询的宝可梦
        
    Returns:
        道具提供的效果字典，键为效果类型，值为效果数值
    """
    effects = {}
    
    if not pokemon.held_item:
        return effects
    
    item = pokemon.held_item
    
    # 解析道具效果
    if hasattr(item, 'equipment_effects') and item.equipment_effects:
        effects = item.equipment_effects.copy()
    
    return effects

async def check_battle_item_trigger(pokemon: Pokemon, trigger_type: str, battle_context: Dict) -> Tuple[bool, str, Dict]:
    """
    检查战斗中道具触发效果。
    
    Args:
        pokemon: 持有道具的宝可梦
        trigger_type: 触发类型（如"on_hit", "on_low_hp", "on_status"等）
        battle_context: 战斗上下文信息
        
    Returns:
        是否触发的布尔值、效果描述和更新后的战斗上下文的元组
    """
    if not pokemon.held_item:
        return False, "", battle_context
    
    item = pokemon.held_item
    
    # 检查道具是否有对应的触发效果
    if not hasattr(item, 'battle_triggers') or trigger_type not in item.battle_triggers:
        return False, "", battle_context
    
    # 获取触发效果
    trigger_effect = item.battle_triggers[trigger_type]
    
    # 判断是否满足触发条件
    if trigger_type == "on_low_hp":
        hp_threshold = trigger_effect.get("threshold", 0.25)
        if pokemon.current_hp / pokemon.stats["hp"] > hp_threshold:
            return False, "", battle_context
    
    # 应用触发效果
    effect_message = f"{pokemon.nickname}的{item.name}发动了效果！"
    
    # 根据效果类型更新战斗上下文
    if "heal_percent" in trigger_effect:
        heal_percent = trigger_effect["heal_percent"]
        heal_amount = int(pokemon.stats["hp"] * heal_percent)
        pokemon.current_hp = min(pokemon.stats["hp"], pokemon.current_hp + heal_amount)
        effect_message += f" 恢复了{heal_amount}点HP！"
    
    if "stat_boost" in trigger_effect:
        stat = trigger_effect["stat_boost"]["stat"]
        stages = trigger_effect["stat_boost"]["stages"]
        if stat in pokemon.stat_stages:
            pokemon.stat_stages[stat] = min(6, pokemon.stat_stages[stat] + stages)
            effect_message += f" {pokemon.nickname}的{stat}提升了！"
    
    # 检查是否为一次性道具
    if item.is_consumed_on_use:
        pokemon.held_item = None
        effect_message += f" {item.name}已消耗。"
    
    return True, effect_message, battle_context

def _check_item_compatibility(pokemon: Pokemon, item: Item) -> bool:
    """
    检查道具是否与宝可梦兼容。
    
    Args:
        pokemon: 要检查的宝可梦
        item: 要检查的道具
        
    Returns:
        是否兼容的布尔值
    """
    # 检查种族限制
    if hasattr(item, 'race_restriction') and item.race_restriction:
        if pokemon.race.race_id not in item.race_restriction:
            return False
    
    # 检查类型限制
    if hasattr(item, 'type_restriction') and item.type_restriction:
        pokemon_types = {pokemon.race.type1, pokemon.race.type2} if pokemon.race.type2 else {pokemon.race.type1}
        if not any(t in item.type_restriction for t in pokemon_types):
            return False
    
    # 检查能力限制
    if hasattr(item, 'ability_restriction') and item.ability_restriction:
        if not pokemon.ability or pokemon.ability.ability_id not in item.ability_restriction:
            return False
    
    return True

def _apply_held_item_effects(pokemon: Pokemon, item: Item) -> None:
    """
    应用持有道具的效果到宝可梦。
    
    Args:
        pokemon: 要应用效果的宝可梦
        item: 提供效果的道具
    """
    if not hasattr(item, 'equipment_effects') or not item.equipment_effects:
        return
    
    # 应用持有道具的效果（例如属性修正）
    # 注意：这些是持久效果，会在卸下道具时移除
    if "stat_modifier" in item.equipment_effects:
        stat_mods = item.equipment_effects["stat_modifier"]
        if not hasattr(pokemon, 'equipment_stat_modifiers'):
            pokemon.equipment_stat_modifiers = {}
        
        for stat, value in stat_mods.items():
            if stat in pokemon.stats:
                if stat not in pokemon.equipment_stat_modifiers:
                    pokemon.equipment_stat_modifiers[stat] = 0
                pokemon.equipment_stat_modifiers[stat] += value
                # 更新实际属性值
                pokemon.stats[stat] = max(1, pokemon.stats[stat] + value)

def _remove_held_item_effects(pokemon: Pokemon, item: Item) -> None:
    """
    移除持有道具的效果。
    
    Args:
        pokemon: 要移除效果的宝可梦
        item: 要移除效果的道具
    """
    if not hasattr(item, 'equipment_effects') or not item.equipment_effects:
        return
    
    # 移除持有道具的效果
    if "stat_modifier" in item.equipment_effects and hasattr(pokemon, 'equipment_stat_modifiers'):
        stat_mods = item.equipment_effects["stat_modifier"]
        
        for stat, value in stat_mods.items():
            if stat in pokemon.equipment_stat_modifiers:
                pokemon.equipment_stat_modifiers[stat] -= value
                # 更新实际属性值
                pokemon.stats[stat] = max(1, pokemon.stats[stat] - value)
                
                # 如果修正值为0，移除该键
                if pokemon.equipment_stat_modifiers[stat] == 0:
                    del pokemon.equipment_stat_modifiers[stat]
