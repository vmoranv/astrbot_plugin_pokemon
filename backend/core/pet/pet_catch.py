import random
from backend.models.pokemon import Pokemon
from backend.models.item import Item # Need Item data for Pokeball
# from backend.core.battle import formulas # Example dependency - formulas should be in core.battle
from backend.core.battle.formulas import calculate_catch_rate # Assuming this function exists
from typing import Dict, Optional, Tuple
import math
from backend.utils.logger import get_logger

logger = get_logger(__name__)

async def calculate_catch_success(wild_pokemon: Pokemon, ball_item: Item, battle_context: Dict = None) -> Tuple[bool, float, str]:
    """
    计算捕获宝可梦的成功率并决定是否捕获成功。
    
    Args:
        wild_pokemon: 要捕获的野生宝可梦
        ball_item: 使用的精灵球道具
        battle_context: 战斗上下文，包含影响捕获率的因素（如状态异常、剩余HP比例等）
        
    Returns:
        捕获是否成功的布尔值、捕获率的浮点数(0-1)和描述消息的元组
    """
    if not battle_context:
        battle_context = {}
    
    # 获取基础捕获率（通常来自宝可梦种族数据）
    base_catch_rate = wild_pokemon.catch_rate if hasattr(wild_pokemon, 'catch_rate') else 45  # 默认值
    
    # 获取球的捕获倍率
    ball_multiplier = _get_ball_multiplier(ball_item, wild_pokemon, battle_context)
    
    # 获取HP修正（HP越低，越容易捕获）
    hp_factor = _calculate_hp_bonus(wild_pokemon)
    
    # 获取状态异常修正
    status_multiplier = _get_status_multiplier(wild_pokemon)
    
    # 计算捕获率
    catch_rate = (((3 * wild_pokemon.stats.get("hp", 100) - 2 * wild_pokemon.current_hp) * base_catch_rate * ball_multiplier) / (3 * wild_pokemon.stats.get("hp", 100))) * status_multiplier
    
    # 确保捕获率在合理范围内
    catch_rate = min(255, max(1, catch_rate))
    
    # 标准化为0-1范围
    normalized_catch_rate = catch_rate / 255.0
    
    # 决定是否捕获成功（模拟摇动并最终捕获）
    shake_count, success = _simulate_catch_attempt(catch_rate)
    
    # 生成描述消息
    message = _generate_catch_message(wild_pokemon.nickname, ball_item.name, shake_count, success)
    
    return success, normalized_catch_rate, message

def _get_ball_multiplier(ball_item: Item, pokemon: Pokemon, battle_context: Dict) -> float:
    """获取精灵球的捕获倍率"""
    # 不同球有不同的倍率和特殊条件
    ball_type = ball_item.name.lower() if hasattr(ball_item, 'name') else "pokeball"
    
    # 默认精灵球倍率
    multipliers = {
        "pokeball": 1.0,
        "greatball": 1.5,
        "ultraball": 2.0,
        "masterball": 255.0,  # 必定成功
        "netball": 1.0,  # 对水和虫系宝可梦有3.5倍效果
        "nestball": 1.0,  # 等级越低效果越好
        "diveball": 1.0,  # 在水中有3.5倍效果
        "duskball": 1.0,  # 夜晚有3.5倍效果
        "timerball": 1.0,  # 回合数越多效果越好
    }
    
    multiplier = multipliers.get(ball_type, 1.0)
    
    # 特殊球的额外逻辑
    if ball_type == "netball" and ("water" in pokemon.types or "bug" in pokemon.types):
        multiplier = 3.5
    
    elif ball_type == "nestball":
        level = pokemon.level
        if level <= 30:
            # 等级越低，倍率越高，最高4倍
            multiplier = ((41 - level) / 10)
    
    elif ball_type == "diveball" and battle_context.get("environment") == "water":
        multiplier = 3.5
    
    elif ball_type == "duskball" and battle_context.get("time_of_day") == "night":
        multiplier = 3.5
    
    elif ball_type == "timerball":
        turn_count = battle_context.get("turn_count", 0)
        # 最高4倍，回合数越多倍率越高
        multiplier = min(4.0, 1.0 + turn_count * 0.3)
    
    return multiplier

def _calculate_hp_bonus(pokemon: Pokemon) -> float:
    """计算基于HP的捕获修正"""
    max_hp = pokemon.stats.get("hp", 100)
    current_hp = pokemon.current_hp
    hp_ratio = current_hp / max_hp
    
    # HP越低，修正越高
    if hp_ratio < 0.1:
        return 2.5
    elif hp_ratio < 0.3:
        return 2.0
    elif hp_ratio < 0.5:
        return 1.5
    else:
        return 1.0

def _get_status_multiplier(pokemon: Pokemon) -> float:
    """获取状态异常的捕获修正倍率"""
    if not hasattr(pokemon, "status_condition") or not pokemon.status_condition:
        return 1.0
    
    status = pokemon.status_condition
    
    # 不同状态异常的修正倍率
    status_multipliers = {
        "sleep": 2.5,
        "freeze": 2.5,
        "paralysis": 1.5,
        "poison": 1.5,
        "burn": 1.5,
        "toxic": 1.5,
    }
    
    # 如果是对象，尝试获取名称属性
    if hasattr(status, "name"):
        status_name = status.name.lower()
    else:
        status_name = str(status).lower()
    
    return status_multipliers.get(status_name, 1.0)

def _simulate_catch_attempt(catch_rate: float) -> Tuple[int, bool]:
    """模拟精灵球的摇动和捕获尝试"""
    # 计算每次摇动的成功概率
    shake_probability = min(255, catch_rate) / 255.0
    
    # 模拟最多4次摇动
    shake_count = 0
    for _ in range(4):
        if random.random() <= shake_probability:
            shake_count += 1
        else:
            break
    
    # 4次摇动都成功则捕获成功
    success = (shake_count == 4)
    
    return shake_count, success

def _generate_catch_message(pokemon_name: str, ball_name: str, shake_count: int, success: bool) -> str:
    """生成捕获过程的描述消息"""
    if success:
        return f"恭喜！使用{ball_name}成功捕获了{pokemon_name}！"
    
    if shake_count == 0:
        return f"{pokemon_name}立刻从{ball_name}中挣脱出来了！"
    elif shake_count == 1:
        return f"{ball_name}摇晃了一下，但{pokemon_name}挣脱出来了！"
    elif shake_count == 2:
        return f"{ball_name}摇晃了两下，但{pokemon_name}挣脱出来了！"
    elif shake_count == 3:
        return f"{ball_name}摇晃了三下，但差一点就成功了！{pokemon_name}挣脱出来了！"
    
    return f"使用{ball_name}尝试捕获{pokemon_name}失败了。"

# Add other catch related functions if needed (e.g., apply_status_effect_for_catch)
