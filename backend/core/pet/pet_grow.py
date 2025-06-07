from typing import List, Dict, Optional, Tuple
import math
from backend.models.pokemon import Pokemon
from backend.models.race import Race # Need Race data for base stats and growth rate
# from backend.core.battle import formulas # Example dependency - formulas should be in core.battle
from backend.core.battle.formulas import calculate_stats # Assuming this function exists
from backend.core.pet.pet_evolution import check_evolution # Assuming this function exists
from backend.core.pet.pet_skill import learn_skill
from backend.models.skill import Skill # Need Skill data for learning new skills
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# 经验成长速度类型
GROWTH_RATES = {
    "fast": lambda level: 4 * (level ** 3) // 5,
    "medium_fast": lambda level: level ** 3,
    "medium_slow": lambda level: 6 * (level ** 3) // 5 - 15 * (level ** 2) + 100 * level - 140,
    "slow": lambda level: 5 * (level ** 3) // 4,
    "erratic": lambda level: _calculate_erratic_exp(level),
    "fluctuating": lambda level: _calculate_fluctuating_exp(level)
}

def _calculate_erratic_exp(level: int) -> int:
    """计算"不规则"成长速度的经验值需求"""
    if level <= 50:
        return (level ** 3) * (100 - level) // 50
    elif level <= 68:
        return (level ** 3) * (150 - level) // 100
    elif level <= 98:
        return (level ** 3) * ((1911 - 10 * level) // 3) // 500
    else:
        return (level ** 3) * (160 - level) // 100

def _calculate_fluctuating_exp(level: int) -> int:
    """计算"波动"成长速度的经验值需求"""
    if level <= 15:
        return (level ** 3) * ((((level + 1) // 3) + 24) // 50)
    elif level <= 36:
        return (level ** 3) * ((level + 14) // 50)
    else:
        return (level ** 3) * ((level // 2 + 32) // 50)

async def calculate_exp_needed(level: int, growth_rate: str) -> int:
    """
    计算达到指定等级所需的总经验值，基于宝可梦的成长速度。
    
    Args:
        level: 目标等级
        growth_rate: 成长速度类型("fast", "medium_fast", "medium_slow", "slow", "erratic", "fluctuating")
        
    Returns:
        达到该等级所需的总经验值
    """
    if growth_rate not in GROWTH_RATES:
        # 默认使用medium_fast（最常见的成长类型）
        growth_rate = "medium_fast"
        logger.warning(f"未知的成长速度类型: {growth_rate}，使用默认值 medium_fast")
    
    return GROWTH_RATES[growth_rate](level)

async def gain_experience(pokemon: Pokemon, exp_amount: int, race_data: Race, skills_data: List[Skill]) -> List[str]:
    """
    Adds experience to a pokemon and checks for level up.
    Returns a list of messages about level ups and new skills learned.
    Requires Race data for growth rate and Skills data for level-up moves.
    """
    messages = []
    old_level = pokemon.level
    pokemon.experience += exp_amount
    logger.debug(f"Pokemon {pokemon.nickname} gained {exp_amount} EXP. Total EXP: {pokemon.experience}")

    # Check for level up
    # Need a way to get EXP needed for the next level based on growth rate (from Race data)
    # Assuming a function calculate_exp_needed(level, growth_rate) exists in formulas or here
    while pokemon.level < 100: # Assuming max level is 100
        exp_needed = await calculate_exp_needed(pokemon.level + 1, race_data.growth_rate) # Assuming growth_rate is on Race model
        if pokemon.experience >= exp_needed:
            await level_up(pokemon, race_data, skills_data)
            messages.append(f"{pokemon.nickname} 升到了 {pokemon.level} 级！")
            # After leveling up, check if enough EXP for the *next* level
        else:
            break # Not enough EXP for the next level

    # If level up, check for evolution
    if pokemon.level > old_level:
        # Check for evolution (using pet_evolution)
        # check_evolution should return the ID of the next race if evolution is possible
        next_race_id = await check_evolution(pokemon, race_data) # Call core.pet.pet_evolution function
        if next_race_id is not None:
            logger.info(f"{pokemon.nickname} is ready to evolve!")
            # The actual evolution process (changing race_id, recalculating stats, etc.)
            # should likely happen in the Service layer after confirming the evolution.
            # This core function just indicates that evolution is possible.
            pokemon.can_evolve_to = next_race_id # Add a flag or attribute to the Pokemon model
            messages.append(f"{pokemon.nickname} 可以进化了！")

    # Note: Saving the updated pokemon object is the responsibility of the Service layer.
    return messages

async def level_up(pokemon: Pokemon, race_data: Race, skills_data: List[Skill]) -> List[str]:
    """
    Levels up a pokemon and updates its stats.
    Checks for new skills learned and potential evolution.
    Requires Race data for base stats/growth and Skills data for level-up moves.
    """
    messages = []
    old_level = pokemon.level
    pokemon.level += 1
    logger.info(f"Leveling up {pokemon.nickname} to level {pokemon.level}")

    # Recalculate stats based on new level, base stats, IVs, EVs, Nature (using formulas)
    # Assuming calculate_stats function exists in core.battle.formulas
    old_stats = pokemon.stats.copy() if pokemon.stats else {}
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

    # Generate stat increase messages
    if old_stats:
        stat_messages = []
        for stat, new_value in pokemon.stats.items():
            if stat in old_stats:
                increase = new_value - old_stats[stat]
                if increase > 0:
                    stat_messages.append(f"{stat.capitalize()}: +{increase}")
        
        if stat_messages:
            messages.append(f"能力值提升：{', '.join(stat_messages)}")

    # If level up, check for evolution
    if pokemon.level > old_level:
        # Check for evolution (using pet_evolution)
        # check_evolution should return the ID of the next race if evolution is possible
        next_race_id = await check_evolution(pokemon, race_data) # Call core.pet.pet_evolution function
        if next_race_id is not None:
            logger.info(f"{pokemon.nickname} is ready to evolve!")
            # The actual evolution process (changing race_id, recalculating stats, etc.)
            # should likely happen in the Service layer after confirming the evolution.
            # This core function just indicates that evolution is possible.
            pokemon.can_evolve_to = next_race_id # Add a flag or attribute to the Pokemon model
            messages.append(f"{pokemon.nickname} 可以进化了！")

    # Note: Saving the updated pokemon object is the responsibility of the Service layer.
    return messages

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

async def gain_evs(pokemon: Pokemon, ev_yields: Dict[str, int], max_total: int = 510, max_stat: int = 252) -> None:
    """
    增加宝可梦的努力值(EVs)。
    
    Args:
        pokemon: 获得努力值的宝可梦
        ev_yields: 增加的努力值字典，键为属性名，值为增加量
        max_total: 所有努力值的最大总和（通常为510）
        max_stat: 单个属性努力值的最大值（通常为252）
    """
    # 确保pokemon有effort_values属性
    if not hasattr(pokemon, 'effort_values') or not pokemon.effort_values:
        pokemon.effort_values = {
            "hp": 0, "attack": 0, "defense": 0, 
            "special_attack": 0, "special_defense": 0, "speed": 0
        }
    
    # 计算当前总和
    current_total = sum(pokemon.effort_values.values())
    
    # 按属性依次添加努力值，同时检查限制
    for stat, value in ev_yields.items():
        if stat not in pokemon.effort_values:
            continue
            
        # 确保不超过单个属性上限
        available_ev = min(value, max_stat - pokemon.effort_values[stat])
        
        # 确保不超过总上限
        available_ev = min(available_ev, max_total - current_total)
        
        # 添加努力值
        pokemon.effort_values[stat] += available_ev
        current_total += available_ev
        
        # 如果已达总上限，提前结束
        if current_total >= max_total:
            break

async def generate_ivs(pokemon: Pokemon) -> Dict[str, int]:
    """
    为宝可梦生成随机个体值(IVs)。
    
    Args:
        pokemon: 要生成个体值的宝可梦
        
    Returns:
        生成的个体值字典
    """
    import random
    
    # 生成随机个体值，范围通常为0-31
    ivs = {
        "hp": random.randint(0, 31),
        "attack": random.randint(0, 31),
        "defense": random.randint(0, 31),
        "special_attack": random.randint(0, 31),
        "special_defense": random.randint(0, 31),
        "speed": random.randint(0, 31)
    }
    
    # 设置到宝可梦对象
    pokemon.individual_values = ivs
    
    return ivs
