from typing import Dict, Any, List, Tuple, Optional
import random
from backend.models.pokemon import Pokemon
from backend.models.race import Race # Need Race data for base stats
# from backend.core.battle import formulas # Example dependency - formulas should be in core.battle
from backend.core.battle.formulas import calculate_stats # Assuming this function exists
from backend.models.nature import Nature
from backend.models.ability import Ability
from backend.utils.logger import get_logger

logger = get_logger(__name__)

async def get_pokemon_stats(pokemon: Pokemon, race_data: Race) -> Dict[str, int]:
    """
    计算宝可梦的各项能力值。
    
    Args:
        pokemon: 宝可梦实例
        race_data: 宝可梦种族数据
        
    Returns:
        包含各能力值的字典
    """
    if not pokemon or not race_data:
        logger.error("计算能力值时缺少宝可梦实例或种族数据")
        return {}
    
    # 获取基础值
    base_stats = {
        "hp": race_data.base_hp,
        "attack": race_data.base_attack,
        "defense": race_data.base_defense,
        "special_attack": race_data.base_sp_attack,
        "special_defense": race_data.base_sp_defense,
        "speed": race_data.base_speed
    }
    
    # 计算各项能力值
    stats = {}
    for stat, base in base_stats.items():
        # 获取个体值（0-31）
        iv = pokemon.individual_values.get(stat, 0) if hasattr(pokemon, 'individual_values') else 0
        
        # 获取努力值（0-252，总和不超过510）
        ev = pokemon.effort_values.get(stat, 0) if hasattr(pokemon, 'effort_values') else 0
        
        # 计算能力值
        if stat == "hp":
            # HP计算公式：(2 * 基础值 + 个体值 + 努力值/4) * 等级/100 + 等级 + 10
            value = int((2 * base + iv + ev // 4) * pokemon.level // 100 + pokemon.level + 10)
        else:
            # 其他能力值计算公式：((2 * 基础值 + 个体值 + 努力值/4) * 等级/100 + 5) * 性格修正
            value = int((2 * base + iv + ev // 4) * pokemon.level // 100 + 5)
            
            # 应用性格修正
            if hasattr(pokemon, 'nature') and isinstance(pokemon.nature, Nature):
                if pokemon.nature.increased_stat == stat:
                    value = int(value * 1.1)
                elif pokemon.nature.decreased_stat == stat:
                    value = int(value * 0.9)
        
        stats[stat] = value
    
    # 应用装备的道具效果
    if hasattr(pokemon, 'equipment_stat_modifiers') and pokemon.equipment_stat_modifiers:
        for stat, modifier in pokemon.equipment_stat_modifiers.items():
            if stat in stats:
                stats[stat] = max(1, stats[stat] + modifier)
    
    # 应用特性效果
    if hasattr(pokemon, 'ability') and isinstance(pokemon.ability, Ability):
        if pokemon.ability.effect_type == "stat_modifier":
            try:
                stat = pokemon.ability.effect_value.get("stat")
                multiplier = float(pokemon.ability.effect_value.get("multiplier", 1.0))
                if stat in stats:
                    stats[stat] = max(1, int(stats[stat] * multiplier))
            except (AttributeError, ValueError, TypeError):
                logger.warning(f"无法应用特性 {pokemon.ability.name} 的能力值修正效果")
    
    return stats

async def calculate_happiness(pokemon: Pokemon, action_type: str = None, value: int = None) -> int:
    """
    计算和更新宝可梦的亲密度。
    
    Args:
        pokemon: 宝可梦实例
        action_type: 影响亲密度的行动类型（如"battle", "item", "levelup"等）
        value: 直接设置的亲密度值，如果提供则忽略action_type
        
    Returns:
        更新后的亲密度值
    """
    # 如果没有亲密度属性，初始化为70（默认值）
    if not hasattr(pokemon, 'happiness') or pokemon.happiness is None:
        pokemon.happiness = 70
    
    # 如果直接提供了值，则直接设置
    if value is not None:
        pokemon.happiness = max(0, min(255, value))
        return pokemon.happiness
    
    # 根据行动类型增加亲密度
    if action_type:
        happiness_change = {
            "level_up": 5,
            "battle_win": 3,
            "vitamin": 5,
            "ev_training": 2,
            "walking": 1,
            "healing_item": 2,
            "faint": -1,
            "bitter_item": -10
        }.get(action_type, 0)
        
        # 应用亲密度变化，确保在0-255范围内
        pokemon.happiness = max(0, min(255, pokemon.happiness + happiness_change))
    
    return pokemon.happiness

async def get_evolution_requirements(pokemon: Pokemon, race_data: Race) -> List[Dict[str, Any]]:
    """
    获取宝可梦的进化需求。
    
    Args:
        pokemon: 宝可梦实例
        race_data: 宝可梦种族数据
        
    Returns:
        包含进化需求的字典列表
    """
    if not race_data or not hasattr(race_data, 'evolution_data') or not race_data.evolution_data:
        return []
    
    evolution_requirements = []
    for evolution in race_data.evolution_data:
        requirement = {
            "evolves_to": evolution.get("evolves_to"),
            "method": evolution.get("method"),
            "met": False
        }
        
        # 检查是否满足进化条件
        if evolution.get("method") == "level":
            requirement["level"] = evolution.get("level", 100)
            requirement["met"] = pokemon.level >= requirement["level"]
        
        elif evolution.get("method") == "item":
            requirement["item_id"] = evolution.get("item_id")
            # 无法在core层检查物品是否拥有，只返回需求
        
        elif evolution.get("method") == "trade":
            requirement["trade"] = True
            # 可能需要额外条件，如持有特定道具
            if "held_item_id" in evolution:
                requirement["held_item_id"] = evolution.get("held_item_id")
        
        elif evolution.get("method") == "happiness":
            requirement["min_happiness"] = evolution.get("min_happiness", 220)
            requirement["met"] = pokemon.happiness >= requirement["min_happiness"] if hasattr(pokemon, 'happiness') else False
        
        # 添加时间条件
        if "time_of_day" in evolution:
            requirement["time_of_day"] = evolution.get("time_of_day")
        
        evolution_requirements.append(requirement)
    
    return evolution_requirements

async def generate_wild_pokemon(race_data: Race, level: int, area_data: Dict = None) -> Pokemon:
    """
    生成野生宝可梦。
    
    Args:
        race_data: 宝可梦种族数据
        level: 野生宝可梦等级
        area_data: 区域数据，影响宝可梦的生成（可选）
        
    Returns:
        生成的野生宝可梦实例
    """
    from backend.core.pet.pet_grow import generate_ivs
    
    # 创建基础宝可梦对象
    pokemon = Pokemon(
        instance_id=0,  # 临时ID，实际应该由数据层分配
        species_id=race_data.species_id,
        race_id=race_data.race_id,
        name=race_data.name,
        nickname=race_data.name,  # 野生宝可梦默认使用种族名作为昵称
        level=level,
        exp=0,
        gender=_generate_random_gender(race_data.gender_ratio if hasattr(race_data, 'gender_ratio') else 0.5)
    )
    
    # 生成随机个体值
    pokemon.individual_values = await generate_ivs(pokemon)
    
    # 初始化努力值
    pokemon.effort_values = {
        "hp": 0, "attack": 0, "defense": 0,
        "special_attack": 0, "special_defense": 0, "speed": 0
    }
    
    # 设置捕获率
    pokemon.catch_rate = race_data.catch_rate if hasattr(race_data, 'catch_rate') else 45
    
    # 设置类型
    pokemon.types = race_data.types.copy() if hasattr(race_data, 'types') else ["normal"]
    
    # 随机选择特性
    if hasattr(race_data, 'abilities') and race_data.abilities:
        # 有10%概率获得隐藏特性（如果有）
        if len(race_data.abilities) > 2 and random.random() < 0.1:
            pokemon.ability = race_data.abilities[2]
        else:
            # 随机选择普通特性
            ability_index = random.randint(0, min(1, len(race_data.abilities) - 1))
            pokemon.ability = race_data.abilities[ability_index]
    
    # 计算能力值
    pokemon.stats = await get_pokemon_stats(pokemon, race_data)
    
    # 设置当前HP为最大HP
    pokemon.current_hp = pokemon.stats["hp"]
    
    # 随机选择技能（根据等级可学会的技能）
    pokemon.skills = []
    if hasattr(race_data, 'learnable_skills'):
        available_skills = [skill for skill in race_data.learnable_skills if skill.get("learn_level", 100) <= level]
        # 随机选择最多4个技能
        if available_skills:
            selected_skills = random.sample(available_skills, min(4, len(available_skills)))
            pokemon.skills = selected_skills
    
    # 初始化其他状态
    pokemon.status_effects = []
    pokemon.stat_stages = {}
    pokemon.happiness = 70
    
    # 如果提供了区域数据，可以进行额外的定制
    if area_data:
        # 例如，某些区域可能会增加特定类型宝可梦的等级或特殊技能概率
        if "level_boost" in area_data and area_data["level_boost"].get("type") in pokemon.types:
            level_boost = area_data["level_boost"].get("value", 0)
            pokemon.level = min(100, pokemon.level + level_boost)
            # 重新计算能力值
            pokemon.stats = await get_pokemon_stats(pokemon, race_data)
            pokemon.current_hp = pokemon.stats["hp"]
    
    return pokemon

def _generate_random_gender(gender_ratio: float) -> str:
    """
    基于性别比例生成随机性别。
    
    Args:
        gender_ratio: 雄性宝可梦的比例（0-1），0表示全部雌性，1表示全部雄性
        
    Returns:
        性别字符串："male"或"female"
    """
    # 某些宝可梦没有性别
    if gender_ratio < 0:
        return "unknown"
    
    return "male" if random.random() < gender_ratio else "female"

# Add other general pet system functions (e.g., calculate_happiness, manage_abilities)
