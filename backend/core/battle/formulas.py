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
    base_stats = race_data.base_stats
    level = pokemon.level
    ivs = pokemon.ivs
    evs = pokemon.evs
    nature = pokemon.nature

    # 实现实际的性格修饰符查找
    nature_modifiers = get_nature_modifiers(nature)
    
    calculated_stats = {}

    # Calculate HP
    base_hp = base_stats.get("hp", 1)
    iv_hp = ivs.get("hp", 0)
    ev_hp = evs.get("hp", 0)
    calculated_stats["hp"] = math.floor(((base_hp * 2 + iv_hp + math.floor(ev_hp/4)) * level) / 100) + level + 10

    # Calculate other stats
    for stat in ["attack", "defense", "special_attack", "special_defense", "speed"]:
        base_stat = base_stats.get(stat, 1)
        iv_stat = ivs.get(stat, 0)
        ev_stat = evs.get(stat, 0)
        nature_mod = nature_modifiers.get(stat, 1.0)
        calculated_stats[stat] = math.floor((math.floor(((base_stat * 2 + iv_stat + math.floor(ev_stat/4)) * level) / 100) + 5) * nature_mod)

    return calculated_stats

def get_nature_modifiers(nature: str) -> Dict[str, float]:
    """
    根据宝可梦的性格返回对应的能力修饰值
    
    性格影响规则：
    - 每种性格会提高一个能力值10%（乘以1.1）
    - 同时降低另一个能力值10%（乘以0.9）
    - 有些性格是中性的，不会改变任何能力值
    
    Args:
        nature: 宝可梦的性格名称
        
    Returns:
        包含各能力值修饰系数的字典
    """
    # 默认所有修饰符为1.0（不变）
    modifiers = {
        "attack": 1.0, 
        "defense": 1.0, 
        "special_attack": 1.0, 
        "special_defense": 1.0, 
        "speed": 1.0
    }
    
    # 性格对应的能力值修饰（提高和降低）
    nature_effects = {
        # 提高攻击
        "勇敢": {"increase": "attack", "decrease": "speed"},
        "固执": {"increase": "attack", "decrease": "special_attack"},
        "顽皮": {"increase": "attack", "decrease": "defense"},
        "淘气": {"increase": "attack", "decrease": "special_defense"},
        
        # 提高防御
        "大胆": {"increase": "defense", "decrease": "attack"},
        "慎重": {"increase": "defense", "decrease": "speed"},
        "害羞": {"increase": "defense", "decrease": "special_attack"},
        "马虎": {"increase": "defense", "decrease": "special_defense"},
        
        # 提高特攻
        "内敛": {"increase": "special_attack", "decrease": "attack"},
        "温和": {"increase": "special_attack", "decrease": "defense"},
        "冷静": {"increase": "special_attack", "decrease": "speed"},
        "温顺": {"increase": "special_attack", "decrease": "special_defense"},
        
        # 提高特防
        "温和": {"increase": "special_defense", "decrease": "attack"},
        "慢吞吞": {"increase": "special_defense", "decrease": "defense"},
        "淘气": {"increase": "special_defense", "decrease": "special_attack"},
        "稳重": {"increase": "special_defense", "decrease": "speed"},
        
        # 提高速度
        "急躁": {"increase": "speed", "decrease": "attack"},
        "爽朗": {"increase": "speed", "decrease": "defense"},
        "开朗": {"increase": "speed", "decrease": "special_attack"},
        "天真": {"increase": "speed", "decrease": "special_defense"},
        
        # 中性性格（不改变任何能力值）
        "调皮": {},
        "认真": {},
        "坦率": {},
        "勤奋": {},
        "实干": {}
    }
    
    # 如果性格在字典中，应用相应的修饰
    if nature in nature_effects:
        effect = nature_effects[nature]
        if "increase" in effect:
            modifiers[effect["increase"]] = 1.1
        if "decrease" in effect:
            modifiers[effect["decrease"]] = 0.9
    
    return modifiers

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
    is_critical: bool,
    effectiveness: float,
    field_state: Dict[str, Any]
) -> int:
    """
    计算技能造成的伤害。
    
    Args:
        attacker: 攻击方宝可梦。
        defender: 防守方宝可梦。
        skill: 使用的技能。
        is_critical: 是否暴击。
        effectiveness: 属性相克效果。
        field_state: 场地状态。
        
    Returns:
        造成的伤害值。
    """
    # 获取技能的基础威力和类型
    base_power = skill.power
    if base_power is None or base_power <= 0:
        return 0  # 非攻击技能不造成伤害
    
    # 获取攻击方和防守方的等级
    attacker_level = attacker.level
    
    # 获取攻击方的攻击力和防守方的防御力
    if skill.damage_type == "physical":
        attack_stat = attacker.attack
        defense_stat = defender.defense
    else:  # special
        attack_stat = attacker.special_attack
        defense_stat = defender.special_defense
    
    # 计算基础伤害
    base_damage = ((2 * attacker_level / 5 + 2) * base_power * attack_stat / defense_stat) / 50 + 2
    
    # 应用随机因子（0.85-1.0）
    random_factor = 0.85 + random.random() * 0.15
    base_damage *= random_factor
    
    # 应用STAB加成（Same Type Attack Bonus）
    if skill.type_id in attacker.type_ids:
        base_damage *= 1.5
    
    # 应用暴击加成
    if is_critical:
        base_damage *= 1.5
    
    # 应用属性相克效果
    base_damage *= effectiveness
    
    # 应用场地效果
    if field_state.get("weather") == "rain" and skill.type_id == 2:  # 假设type_id 2是水系
        base_damage *= 1.5
    elif field_state.get("weather") == "sunny" and skill.type_id == 1:  # 假设type_id 1是火系
        base_damage *= 1.5
    
    # 应用道具效果
    held_item = attacker.held_item
    if held_item and held_item.effect_type == "boost_damage":
        base_damage *= 1.1  # 增加10%伤害
    
    # 确保伤害为整数且非负
    return max(0, int(base_damage))

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
    检查技能是否命中，考虑命中率、精度等级、闪避等级和场地效果。
    
    Args:
        skill_accuracy: 技能的基础命中率（None表示必中）。
        attacker_accuracy_stage: 攻击方的命中等级。
        defender_evasion_stage: 防守方的闪避等级。
        field_state: 战场状态（天气、场地等）。
        
    Returns:
        True表示命中，False表示未命中。
    """
    if skill_accuracy is None:
        return True  # 必中技能

    # 计算命中率和闪避的修正系数
    accuracy_multiplier = calculate_accuracy_evasion_modifier(attacker_accuracy_stage)
    evasion_multiplier = calculate_accuracy_evasion_modifier(defender_evasion_stage)
    
    # 考虑场地效果修正
    field_multiplier = 1.0
    
    # 天气效果
    weather = field_state.get("weather")
    if weather == "heavy_rain" and skill_accuracy < 100:  # 大雨降低非必中技能的命中率
        field_multiplier *= 0.8
    elif weather == "fog" and skill_accuracy < 100:  # 雾天降低非必中技能的命中率
        field_multiplier *= 0.9
        
    # 最终命中率计算
    final_accuracy = (skill_accuracy / 100.0) * accuracy_multiplier / evasion_multiplier * field_multiplier
    
    # 限制最终命中率在合理范围内
    final_accuracy = min(max(final_accuracy, 0.1), 1.0)  # 最低10%命中率，最高100%
    
    return random.random() < final_accuracy

def calculate_accuracy_evasion_modifier(stage: int) -> float:
    """
    计算命中率/闪避率的等级修正系数。
    
    Args:
        stage: 能力等级，范围-6到+6。
        
    Returns:
        修正系数。
    """
    if stage >= 0:
        return (3 + stage) / 3.0
    else:
        return 3.0 / (3 - stage)

def check_critical_hit(attacker: Pokemon, skill_critical_rate: int) -> bool:
    """
    检查技能是否造成暴击。
    
    Args:
        attacker: 攻击方宝可梦。
        skill_critical_rate: 技能的暴击率等级。
        
    Returns:
        True表示暴击，False表示未暴击。
    """
    # 基础暴击率
    critical_chance = 0.0
    
    # 根据技能暴击等级设置基础概率
    if skill_critical_rate == 1:
        critical_chance = 1/16  # 6.25%
    elif skill_critical_rate == 2:
        critical_chance = 1/8   # 12.5%
    elif skill_critical_rate == 3:
        critical_chance = 1/4   # 25%
    elif skill_critical_rate == 4:
        critical_chance = 1/3   # 33.3%
    elif skill_critical_rate >= 5:
        critical_chance = 1/2   # 50%
    
    # 考虑持有道具的效果
    held_item = attacker.held_item
    if held_item:
        if held_item.effect_type == "increase_critical_rate":
            critical_chance *= 1.5  # 增加50%暴击率
    
    # 考虑特性效果
    ability = attacker.ability
    if ability and ability.name == "狙击手":  # Sniper特性
        critical_chance *= 1.5
    
    # 限制最终暴击率
    critical_chance = min(critical_chance, 0.5)  # 最高50%暴击率
    
    return random.random() < critical_chance

def calculate_stat_stage_modifier(stage: int, stat_type: str = "normal") -> float:
    """
    计算能力值等级的修正系数。
    
    Args:
        stage: 能力等级，范围-6到+6。
        stat_type: 能力类型，"normal"表示常规能力，"accuracy_evasion"表示命中/闪避。
        
    Returns:
        修正系数。
    """
    # 命中/闪避使用不同的公式
    if stat_type == "accuracy_evasion":
        return calculate_accuracy_evasion_modifier(stage)
    
    # 常规能力值（攻击、防御、特攻、特防、速度）
    if stage > 0:
        return (2 + stage) / 2.0
    elif stage < 0:
        return 2.0 / (2 - stage)
    else:
        return 1.0

def get_effective_stat(pokemon: Pokemon, stat_type: str, race_data: Dict[str, Any]) -> int:
    """
    计算考虑基础能力值、个体值、努力值、性格和能力等级的有效能力值。
    
    Args:
        pokemon: 宝可梦实例。
        stat_type: 能力类型（"hp"、"attack"、"defense"、"special_attack"、"special_defense"、"speed"）。
        race_data: 宝可梦种族数据，包含基础能力值。
        
    Returns:
        有效能力值。
    """
    # 获取基础能力值
    base_stats = race_data.get("base_stats", {})
    base_stat = base_stats.get(stat_type, 50)  # 默认值50
    
    # 获取个体值和努力值
    iv = pokemon.ivs.get(stat_type, 0)
    ev = pokemon.evs.get(stat_type, 0)
    
    # 获取等级和性格
    level = pokemon.level
    nature = pokemon.nature
    
    # 计算性格修正
    nature_modifier = 1.0
    nature_effects = {
        "勇敢": {"increase": "attack", "decrease": "speed"},
        "固执": {"increase": "attack", "decrease": "special_attack"},
        "调皮": {"increase": "attack", "decrease": "defense"},
        "大胆": {"increase": "attack", "decrease": "special_defense"},
        
        "孤独": {"increase": "defense", "decrease": "speed"},
        "顽皮": {"increase": "defense", "decrease": "attack"},
        "坦率": {"increase": "defense", "decrease": "special_attack"},
        "悠闲": {"increase": "defense", "decrease": "special_defense"},
        
        "勤奋": {"increase": "special_attack", "decrease": "speed"},
        "淘气": {"increase": "special_attack", "decrease": "attack"},
        "爽朗": {"increase": "special_attack", "decrease": "defense"},
        "内敛": {"increase": "special_attack", "decrease": "special_defense"},
        
        "胆小": {"increase": "special_defense", "decrease": "speed"},
        "马虎": {"increase": "special_defense", "decrease": "attack"},
        "冷静": {"increase": "special_defense", "decrease": "defense"},
        "慢吞吞": {"increase": "special_defense", "decrease": "special_attack"},
        
        "天真": {"increase": "speed", "decrease": "attack"},
        "急躁": {"increase": "speed", "decrease": "defense"},
        "开朗": {"increase": "speed", "decrease": "special_attack"},
        "害羞": {"increase": "speed", "decrease": "special_defense"},
        
        # 中性性格
        "认真": {},
        "温和": {},
        "保守": {},
        "沉着": {},
        "稳重": {}
    }
    
    if nature in nature_effects:
        effect = nature_effects[nature]
        if "increase" in effect and effect["increase"] == stat_type:
            nature_modifier = 1.1
        elif "decrease" in effect and effect["decrease"] == stat_type:
            nature_modifier = 0.9
    
    # 计算基础能力值（不考虑能力等级）
    if stat_type == "hp":
        # HP计算公式
        base_value = math.floor(((2 * base_stat + iv + math.floor(ev/4)) * level) / 100) + level + 10
    else:
        # 其他能力值计算公式
        base_value = math.floor((math.floor(((2 * base_stat + iv + math.floor(ev/4)) * level) / 100) + 5) * nature_modifier)
    
    # 如果不是HP，则应用能力等级修正
    if stat_type != "hp":
        stage = pokemon.stat_stages.get(stat_type, 0)
        stage_modifier = calculate_stat_stage_modifier(stage)
        return max(1, int(base_value * stage_modifier))
    
    return max(1, base_value)

def calculate_catch_rate(
    wild_pokemon: Pokemon,
    ball_modifier: float,
    status_modifier: float = 1.0
) -> float:
    """
    计算捕获宝可梦的成功率。
    
    Args:
        wild_pokemon: 野生宝可梦。
        ball_modifier: 精灵球的修正系数。
        status_modifier: 状态异常的修正系数。
        
    Returns:
        捕获成功率（0.0-1.0）。
    """
    # 获取宝可梦的基础捕获率
    base_catch_rate = wild_pokemon.race.catch_rate
    
    # 获取宝可梦的当前HP比例
    hp_ratio = wild_pokemon.current_hp / wild_pokemon.max_hp
    
    # 计算捕获率公式
    a = (3 * wild_pokemon.max_hp - 2 * wild_pokemon.current_hp) * base_catch_rate * ball_modifier * status_modifier / (3 * wild_pokemon.max_hp)
    
    # 限制捕获率
    a = min(max(a, 0), 255)
    
    # 计算捕获概率
    b = 1048560 / math.sqrt(math.sqrt(16711680 / a))
    
    # 抖动检查
    shake_probability = min(b / 65535, 1.0)
    
    # 需要连续4次抖动成功才能捕获
    catch_probability = shake_probability ** 4
    
    return catch_probability

def calculate_exp_gain(
    defeated_pokemon_base_exp: int,
    defeated_pokemon_level: int,
    winner_pokemon_level: int,
    is_wild: bool = True,
    exp_share: bool = False,
    lucky_egg: bool = False,
    num_participants: int = 1
) -> int:
    """
    计算击败宝可梦后获得的经验值。
    
    Args:
        defeated_pokemon_base_exp: 被击败宝可梦的基础经验值。
        defeated_pokemon_level: 被击败宝可梦的等级。
        winner_pokemon_level: 获胜宝可梦的等级。
        is_wild: 是否是野生宝可梦。
        exp_share: 是否有经验分享道具。
        lucky_egg: 是否持有幸运蛋。
        num_participants: 参与战斗的宝可梦数量。
        
    Returns:
        获得的经验值。
    """
    # 基础公式
    exp = (defeated_pokemon_base_exp * defeated_pokemon_level) / 5
    
    # 对战类型修正
    if not is_wild:  # 训练师宝可梦提供1.5倍经验
        exp *= 1.5
    
    # 等级差修正
    level_difference = defeated_pokemon_level - winner_pokemon_level
    if level_difference > 0:
        # 击败高等级宝可梦获得额外经验
        exp *= (1 + 0.05 * level_difference)
    
    # 经验分享修正
    if exp_share:
        # 如果有经验分享，经验不减少
        pass
    else:
        # 多只宝可梦分享经验
        exp /= num_participants
    
    # 幸运蛋修正（1.5倍经验）
    if lucky_egg:
        exp *= 1.5
    
    return max(1, int(exp))

def check_evolution_condition(
    pokemon: Pokemon,
    evolution_trigger: str,
    required_level: Optional[int] = None,
    required_item_id: Optional[int] = None,
    required_friendship: Optional[int] = None,
    required_time: Optional[str] = None,  # "day" 或 "night"
    required_move_id: Optional[int] = None,  # 需要学会特定技能
    required_location_id: Optional[int] = None,  # 特定地点进化
    is_trading: bool = False,
    is_battle: bool = False,
    current_time: Optional[str] = None,  # 当前游戏世界时间
    current_location_id: Optional[int] = None  # 当前位置
) -> bool:
    """
    检查宝可梦是否满足进化条件。
    
    Args:
        pokemon: 宝可梦。
        evolution_trigger: 进化触发条件。
        required_level: 进化所需等级。
        required_item_id: 进化所需道具ID。
        required_friendship: 进化所需友好度。
        required_time: 进化所需时间("day"或"night")。
        required_move_id: 进化所需已学会的技能ID。
        required_location_id: 进化所需地点ID。
        is_trading: 是否正在交换中。
        is_battle: 是否在战斗中。
        current_time: 当前游戏世界时间。
        current_location_id: 当前位置ID。
        
    Returns:
        是否满足进化条件。
    """
    # 基本条件检查
    if evolution_trigger == "level_up":
        if required_level is None:
            return False
        
        # 等级检查
        level_ok = pokemon.level >= required_level
        if not level_ok:
            return False
            
        # 附加条件检查（如果有）
        
        # 时间条件
        if required_time and current_time:
            if required_time != current_time:
                return False
                
        # 技能条件
        if required_move_id:
            move_learned = any(skill.skill_id == required_move_id for skill in pokemon.skills)
            if not move_learned:
                return False
                
        # 地点条件
        if required_location_id and current_location_id:
            if required_location_id != current_location_id:
                return False
                
        # 友好度条件
        if required_friendship:
            if pokemon.happiness < required_friendship:
                return False
                
        # 通过所有检查
        return True
    
    # 道具进化
    elif evolution_trigger == "item":
        return required_item_id is not None
    
    # 交换进化
    elif evolution_trigger == "trade":
        # 有些宝可梦需要在交换时持有特定道具
        if required_item_id:
            return is_trading and pokemon.held_item_id == required_item_id
        return is_trading
    
    # 友好度进化
    elif evolution_trigger == "friendship":
        if required_friendship is None:
            return False
            
        friendship_ok = pokemon.happiness >= required_friendship
        
        # 可能有额外条件，如时间
        if required_time and current_time:
            return friendship_ok and required_time == current_time
            
        return friendship_ok
    
    # 战斗进化
    elif evolution_trigger == "battle":
        if not is_battle:
            return False
            
        # 有些宝可梦需要在战斗中升级到特定等级
        if required_level:
            return pokemon.level >= required_level
            
        return True
        
    # 特殊形式进化，如性别特定进化、特定天气等
    elif evolution_trigger == "special":
        # 这里需要根据具体宝可梦设计更多特殊条件
        # 例如伊布的各种进化形式
        return False
    
    return False

# Terrain damage modifiers (example, based on field_effects.csv)
# Structure: {terrain_logic_key: {skill_type_id: multiplier}}
TERRAIN_DAMAGE_MODIFIERS: Dict[str, Dict[int, float]] = {
    "electric_terrain_effect": {13: 1.5}, # Electric Terrain boosts Electric (type 13) moves by 1.5x
    "grassy_terrain_effect": {11: 1.5}, # Grassy Terrain boosts Grass (type 11) moves by 1.5x
    "psychic_terrain_effect": {14: 1.5}, # Psychic Terrain boosts Psychic (type 14) moves by 1.5x
    "misty_terrain_effect": {16: 0.5}, # Misty Terrain weakens Dragon (type 16) moves by 0.5x
    # Add other terrain effects as needed
}

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
    - Other modifiers (Items, Abilities, etc.)

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
    if check_critical_hit(attacker, skill.critical_hit_ratio):
        modifier *= 1.5 # Critical hit multiplier (Gen 6+)
        logger.debug(f"Critical hit modifier applied (1.5x)")

    # 4. Random Factor (0.85 to 1.0)
    random_factor = random.randint(85, 100) / 100.0
    modifier *= random_factor
    logger.debug(f"Random Factor applied ({random_factor}x)")

    # 5. Weather effects
    if battle.weather:
        weather_modifier = 1.0
        # 天气效果实现
        if battle.weather == 'sunny':
            # 晴天增强火系技能，削弱水系技能
            if skill.skill_type == 10:  # 假设10是火系ID
                weather_modifier = 1.5
                logger.debug(f"Sunny weather boosts Fire-type move (1.5x)")
            elif skill.skill_type == 11:  # 假设11是水系ID
                weather_modifier = 0.5
                logger.debug(f"Sunny weather weakens Water-type move (0.5x)")
        elif battle.weather == 'rainy':
            # 雨天增强水系技能，削弱火系技能
            if skill.skill_type == 11:  # 水系
                weather_modifier = 1.5
                logger.debug(f"Rainy weather boosts Water-type move (1.5x)")
            elif skill.skill_type == 10:  # 火系
                weather_modifier = 0.5
                logger.debug(f"Rainy weather weakens Fire-type move (0.5x)")
        elif battle.weather == 'sandstorm':
            # 沙暴增加岩石系宝可梦的特防
            if 13 in defender_type_ids:  # 假设13是岩石系ID
                if skill.damage_type == "special":
                    defense_stat *= 1.5
                    logger.debug(f"Sandstorm boosts Rock-type Pokémon's Special Defense (1.5x)")
        elif battle.weather == 'hail':
            # 冰雹对非冰系宝可梦造成伤害（在battle_logic中处理）
            pass
            
        modifier *= weather_modifier
        logger.debug(f"Weather ({battle.weather}) modifier applied ({weather_modifier}x)")

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

    # 7. Burn effect
    if any(status.status_type == 'burn' for status in attacker.status_effects) and skill.damage_type == 'physical':
        burn_modifier = 0.5
        modifier *= burn_modifier
        logger.debug(f"Burn modifier applied ({burn_modifier}x)")

    # 8. Other modifiers (Items, Abilities, etc.)
    # 道具效果
    if attacker.held_item:
        item_modifier = 1.0
        
        # 各种属性增强道具
        type_boosting_items = {
            "火焰宝珠": {"type": 10, "boost": 1.2},  # 火系
            "神秘水滴": {"type": 11, "boost": 1.2},  # 水系
            "奇迹种子": {"type": 12, "boost": 1.2},  # 草系
            # 可以添加更多类型增强道具
        }
        
        # 检查是否有属性增强道具
        if attacker.held_item.name in type_boosting_items:
            item_data = type_boosting_items[attacker.held_item.name]
            if skill.skill_type == item_data["type"]:
                item_modifier = item_data["boost"]
                logger.debug(f"Item {attacker.held_item.name} boosts {skill.skill_type}-type moves ({item_modifier}x)")
        
        # 攻击提升道具
        if attacker.held_item.name == "力量护腕" and skill.damage_type == "physical":
            item_modifier = 1.1
            logger.debug(f"Muscle Band boosts physical moves (1.1x)")
        elif attacker.held_item.name == "智力眼镜" and skill.damage_type == "special":
            item_modifier = 1.1
            logger.debug(f"Wise Glasses boosts special moves (1.1x)")
            
        modifier *= item_modifier

    # 检查特殊场地效果（在伤害计算以外的效果）
    if battle.terrain == "grassy_terrain":
        # 每回合结束时回复HP的逻辑将在battle_logic.py中实现
        pass
    elif battle.terrain == "psychic_terrain":
        # 优先级技能失效的逻辑将在battle_logic.py中实现
        pass
    elif battle.terrain == "misty_terrain":
        # 状态异常防护的逻辑将在battle_logic.py中实现
        pass

    # Final Damage Calculation
    final_damage = math.floor(damage * modifier)

    # Ensure minimum damage is 1 if the attack is supposed to deal damage, unless effectiveness is 0
    if final_damage <= 0 and skill.power > 0 and type_effectiveness_multiplier > 0:
        final_damage = 1

    logger.debug(f"Calculated final damage: {final_damage}")

    return final_damage

def calculate_exp_needed(level: int, growth_rate: str) -> int:
    """
    计算达到指定等级所需的总经验值。
    
    Args:
        level: 目标等级。
        growth_rate: 成长速率。
        
    Returns:
        所需的总经验值。
    """
    if level <= 1:
        return 0
        
    # 不同成长速率的经验值计算
    if growth_rate == "fast":
        return int(0.8 * (level ** 3))
    elif growth_rate == "medium_fast":
        return level ** 3
    elif growth_rate == "medium_slow":
        return int(1.2 * (level ** 3) - 15 * (level ** 2) + 100 * level - 140)
    elif growth_rate == "slow":
        return int(1.25 * (level ** 3))
    elif growth_rate == "fluctuating":
        if level <= 15:
            return int((level ** 3) * (((level + 1) / 3) + 24) / 50)
        elif level <= 36:
            return int((level ** 3) * (level + 14) / 50)
        else:
            return int((level ** 3) * ((level / 2) + 32) / 50)
    elif growth_rate == "erratic":
        if level <= 50:
            return int((level ** 3) * (100 - level) / 50)
        elif level <= 68:
            return int((level ** 3) * (150 - level) / 100)
        elif level <= 98:
            return int((level ** 3) * ((1911 - 10 * level) / 3) / 500)
        else:
            return int((level ** 3) * (160 - level) / 100)
    
    # 默认使用medium_fast
    return level ** 3

def calculate_exp_to_next_level(current_exp: int, current_level: int, growth_rate: str) -> int:
    """
    计算升级到下一级所需的经验值。
    
    Args:
        current_exp: 当前经验值。
        current_level: 当前等级。
        growth_rate: 成长速率。
        
    Returns:
        升级所需的经验值。
    """
    next_level = current_level + 1
    exp_needed_for_next = calculate_exp_needed(next_level, growth_rate)
    exp_needed_for_current = calculate_exp_needed(current_level, growth_rate)
    
    # 计算还需要多少经验值
    exp_needed = exp_needed_for_next - current_exp
    
    return max(0, exp_needed)

def calculate_escape_chance(
    player_pokemon_speed: int,
    wild_pokemon_speed: int,
    escape_attempt_count: int = 0
) -> float:
    """
    计算从野生宝可梦战斗中逃跑的成功率。
    
    Args:
        player_pokemon_speed: 玩家宝可梦的速度。
        wild_pokemon_speed: 野生宝可梦的速度。
        escape_attempt_count: 已尝试逃跑的次数。
        
    Returns:
        逃跑成功的概率（0.0-1.0）。
    """
    # 基本公式：逃跑指数 = ((玩家速度 * 128) / 野生速度) + 30 * 逃跑尝试次数
    if wild_pokemon_speed <= 0:
        return 1.0  # 防止除以零，100%成功
        
    escape_index = ((player_pokemon_speed * 128) / wild_pokemon_speed) + 30 * escape_attempt_count
    
    # 限制在合理范围内
    escape_index = min(255, escape_index)
    
    # 转换为概率（0-255范围映射到0.0-1.0）
    escape_probability = escape_index / 255.0
    
    return escape_probability
