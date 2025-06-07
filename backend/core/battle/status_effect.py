# backend/core/battle/status_effect.py

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import random

from backend.models.pokemon import Pokemon
from backend.models.status_effect import StatusEffect
from backend.core.battle.events import BattleEvent, DamageEvent, StatusEffectEvent, BattleMessageEvent
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class MajorStatusType(Enum):
    """主要状态异常类型"""
    BURN = "burn"           # 灼伤
    FREEZE = "freeze"       # 冰冻
    PARALYSIS = "paralysis" # 麻痹
    POISON = "poison"       # 中毒
    TOXIC = "toxic"         # 剧毒
    SLEEP = "sleep"         # 睡眠
    NONE = "none"           # 无状态

class VolatileStatusType(Enum):
    """易变状态类型"""
    CONFUSED = "confused"     # 混乱
    FLINCH = "flinch"         # 畏缩
    LEECH_SEED = "leech_seed" # 寄生种子
    BOUND = "bound"           # 束缚
    TAUNT = "taunt"           # 挑衅
    INFATUATION = "infatuation" # 着迷
    IDENTIFIED = "identified" # 识破

async def apply_major_status(pokemon: Pokemon, status_type: MajorStatusType, turns: int = -1) -> Tuple[bool, str]:
    """
    应用主要状态效果到宝可梦。
    
    Args:
        pokemon: 目标宝可梦
        status_type: 状态类型
        turns: 持续回合数，-1 表示持续到战斗结束或被治愈
        
    Returns:
        成功应用状态效果的布尔值和描述消息
    """
    # 如果已经有主要状态效果，则不能再应用新的
    if pokemon.major_status_effect and pokemon.major_status_effect.effect_logic_key != "none":
        return False, f"{pokemon.nickname}已经处于{pokemon.major_status_effect.name}状态，无法再被施加新状态！"
    
    # 检查属性免疫（例如，电系免疫麻痹，火系免疫灼伤等）
    if is_immune_to_status(pokemon, status_type):
        return False, f"{pokemon.nickname}的属性使其免疫{status_type.value}状态！"
    
    # 应用状态效果
    status_data = {
        "name": status_type.value.capitalize(),
        "description": get_status_description(status_type),
        "effect_logic_key": status_type.value,
        "remaining_turns": turns,
        "custom_data": {}
    }
    
    if status_type == MajorStatusType.TOXIC:
        status_data["custom_data"]["toxic_counter"] = 1
    
    new_status = StatusEffect(
        status_effect_id=get_status_effect_id(status_type),  # 这里应该从元数据获取
        name=status_data["name"],
        description=status_data["description"],
        effect_logic_key=status_data["effect_logic_key"],
        remaining_turns=status_data["remaining_turns"],
        custom_data=status_data["custom_data"]
    )
    
    pokemon.major_status_effect = new_status
    
    message = get_status_application_message(status_type, pokemon.nickname)
    return True, message

async def remove_major_status(pokemon: Pokemon) -> Tuple[bool, str]:
    """
    移除宝可梦的主要状态效果。
    
    Args:
        pokemon: 目标宝可梦
        
    Returns:
        成功移除状态效果的布尔值和描述消息
    """
    if not pokemon.major_status_effect or pokemon.major_status_effect.effect_logic_key == "none":
        return False, f"{pokemon.nickname}没有状态异常需要移除。"
    
    status_type = MajorStatusType(pokemon.major_status_effect.effect_logic_key)
    old_status = pokemon.major_status_effect
    pokemon.major_status_effect = None
    
    message = get_status_removal_message(status_type, pokemon.nickname)
    return True, message

async def apply_volatile_status(pokemon: Pokemon, status_type: VolatileStatusType, turns: int = -1, custom_data: Dict[str, Any] = None) -> Tuple[bool, str]:
    """
    应用易变状态效果到宝可梦。
    
    Args:
        pokemon: 目标宝可梦
        status_type: 状态类型
        turns: 持续回合数，-1 表示持续到战斗结束或被移除
        custom_data: 自定义数据，用于保存状态效果的特定信息
        
    Returns:
        成功应用状态效果的布尔值和描述消息
    """
    if not pokemon.volatile_status:
        pokemon.volatile_status = {}
    
    # 检查是否已有相同易变状态
    if status_type.value in pokemon.volatile_status:
        return False, f"{pokemon.nickname}已经处于{status_type.value}状态！"
    
    # 应用易变状态
    pokemon.volatile_status[status_type.value] = {
        "remaining_turns": turns,
        "custom_data": custom_data or {}
    }
    
    message = get_volatile_status_application_message(status_type, pokemon.nickname)
    return True, message

async def remove_volatile_status(pokemon: Pokemon, status_type: VolatileStatusType) -> Tuple[bool, str]:
    """
    移除宝可梦的易变状态效果。
    
    Args:
        pokemon: 目标宝可梦
        status_type: 要移除的状态类型
        
    Returns:
        成功移除状态效果的布尔值和描述消息
    """
    if not pokemon.volatile_status or status_type.value not in pokemon.volatile_status:
        return False, f"{pokemon.nickname}没有{status_type.value}状态需要移除。"
    
    del pokemon.volatile_status[status_type.value]
    
    message = get_volatile_status_removal_message(status_type, pokemon.nickname)
    return True, message

async def process_status_effects_at_turn_end(pokemon: Pokemon) -> List[BattleEvent]:
    """
    处理回合结束时的状态效果。
    
    Args:
        pokemon: 目标宝可梦
        
    Returns:
        一个包含状态效果处理所产生事件的列表
    """
    events: List[BattleEvent] = []
    
    # 处理主要状态效果
    if pokemon.major_status_effect:
        status_key = pokemon.major_status_effect.effect_logic_key
        status_type = MajorStatusType(status_key)
        
        # 减少持续回合数（如果有设定）
        if pokemon.major_status_effect.remaining_turns > 0:
            pokemon.major_status_effect.remaining_turns -= 1
            if pokemon.major_status_effect.remaining_turns <= 0:
                success, message = await remove_major_status(pokemon)
                if success:
                    events.append(BattleMessageEvent(message=message))
                    events.append(StatusEffectEvent(
                        pokemon_instance_id=pokemon.instance_id,
                        pokemon_name=pokemon.nickname,
                        status_effect_id=pokemon.major_status_effect.status_effect_id if pokemon.major_status_effect else None,
                        status_name="none",
                        is_applied=False,
                        message=message
                    ))
        
        # 根据状态类型处理效果
        if status_type == MajorStatusType.BURN:
            # 灼伤：每回合损失最大HP的1/16
            damage = max(1, pokemon.max_hp // 16)
            await _apply_status_damage(pokemon, damage, "灼伤", events)
            
        elif status_type == MajorStatusType.POISON:
            # 中毒：每回合损失最大HP的1/8
            damage = max(1, pokemon.max_hp // 8)
            await _apply_status_damage(pokemon, damage, "中毒", events)
            
        elif status_type == MajorStatusType.TOXIC:
            # 剧毒：每回合损失的HP越来越多
            toxic_counter = pokemon.major_status_effect.custom_data.get("toxic_counter", 1)
            damage = max(1, (pokemon.max_hp * toxic_counter) // 16)
            await _apply_status_damage(pokemon, damage, "剧毒", events)
            # 增加中毒计数器
            pokemon.major_status_effect.custom_data["toxic_counter"] = min(toxic_counter + 1, 15)
            
        elif status_type == MajorStatusType.SLEEP:
            # 睡眠：回合结束时有概率醒来
            if random.random() < 0.3:  # 30%概率醒来
                success, message = await remove_major_status(pokemon)
                if success:
                    events.append(BattleMessageEvent(message=message))
                    events.append(StatusEffectEvent(
                        pokemon_instance_id=pokemon.instance_id,
                        pokemon_name=pokemon.nickname,
                        status_effect_id=None,
                        status_name="none",
                        is_applied=False,
                        message=message
                    ))
            else:
                events.append(BattleMessageEvent(message=f"{pokemon.nickname}还在睡觉。"))
                
        elif status_type == MajorStatusType.FREEZE:
            # 冰冻：回合结束时有概率解冻
            if random.random() < 0.2:  # 20%概率解冻
                success, message = await remove_major_status(pokemon)
                if success:
                    events.append(BattleMessageEvent(message=message))
                    events.append(StatusEffectEvent(
                        pokemon_instance_id=pokemon.instance_id,
                        pokemon_name=pokemon.nickname,
                        status_effect_id=None,
                        status_name="none",
                        is_applied=False,
                        message=message
                    ))
            else:
                events.append(BattleMessageEvent(message=f"{pokemon.nickname}还处于冰冻状态。"))
    
    # 处理易变状态效果
    if pokemon.volatile_status:
        status_keys = list(pokemon.volatile_status.keys())
        for status_key in status_keys:
            try:
                status_type = VolatileStatusType(status_key)
                status_data = pokemon.volatile_status[status_key]
                
                # 减少持续回合数（如果有设定）
                if status_data["remaining_turns"] > 0:
                    status_data["remaining_turns"] -= 1
                    if status_data["remaining_turns"] <= 0:
                        success, message = await remove_volatile_status(pokemon, status_type)
                        if success:
                            events.append(BattleMessageEvent(message=message))
                        continue
                
                # 根据状态类型处理效果
                if status_type == VolatileStatusType.CONFUSED:
                    # 混乱：回合结束时有概率解除
                    if random.random() < 0.25:  # 25%概率解除混乱
                        success, message = await remove_volatile_status(pokemon, status_type)
                        if success:
                            events.append(BattleMessageEvent(message=message))
                
                elif status_type == VolatileStatusType.LEECH_SEED:
                    # 寄生种子：损失HP，但需要敌方宝可梦存在才能恢复
                    damage = max(1, pokemon.max_hp // 8)
                    message = f"{pokemon.nickname}受到了寄生种子的伤害！"
                    events.append(BattleMessageEvent(message=message))
                    
                    # 实际HP减少逻辑
                    pokemon.current_hp = max(0, pokemon.current_hp - damage)
                    events.append(DamageEvent(
                        target_instance_id=pokemon.instance_id,
                        target_name=pokemon.nickname,
                        damage=damage,
                        current_hp=pokemon.current_hp,
                        max_hp=pokemon.max_hp,
                        message=message
                    ))
                    
                    # 注意：恢复敌方宝可梦HP的逻辑应该在战斗逻辑中实现，这里只处理伤害部分
            
            except ValueError:
                logger.warning(f"未知的易变状态类型: {status_key}")
                continue
    
    return events

async def _apply_status_damage(pokemon: Pokemon, damage: int, status_name: str, events: List[BattleEvent]) -> None:
    """
    应用状态效果造成的伤害
    
    Args:
        pokemon: 目标宝可梦
        damage: 伤害值
        status_name: 状态名称
        events: 事件列表，用于添加新事件
    """
    message = f"{pokemon.nickname}受到了{status_name}伤害！"
    events.append(BattleMessageEvent(message=message))
    
    # 实际HP减少逻辑
    pokemon.current_hp = max(0, pokemon.current_hp - damage)
    events.append(DamageEvent(
        target_instance_id=pokemon.instance_id,
        target_name=pokemon.nickname,
        damage=damage,
        current_hp=pokemon.current_hp,
        max_hp=pokemon.max_hp,
        message=message
    ))

def is_immune_to_status(pokemon: Pokemon, status_type: MajorStatusType) -> bool:
    """
    检查宝可梦是否对特定状态效果免疫
    
    Args:
        pokemon: 目标宝可梦
        status_type: 状态类型
        
    Returns:
        是否免疫
    """
    # 简化版本，实际应该根据宝可梦的属性、特性等判断
    if not pokemon.types:
        return False
    
    # 基于属性的免疫
    primary_type = pokemon.types[0].lower() if pokemon.types else None
    
    if status_type == MajorStatusType.BURN and primary_type == "fire":
        return True
    elif status_type == MajorStatusType.FREEZE and primary_type == "ice":
        return True
    elif status_type == MajorStatusType.PARALYSIS and primary_type == "electric":
        return True
    elif (status_type == MajorStatusType.POISON or status_type == MajorStatusType.TOXIC) and (primary_type == "poison" or primary_type == "steel"):
        return True
    
    # 特性免疫（简化版）
    if pokemon.ability:
        ability_name = pokemon.ability.name.lower()
        
        if status_type == MajorStatusType.BURN and ability_name == "water veil":
            return True
        elif status_type == MajorStatusType.FREEZE and ability_name == "magma armor":
            return True
        elif status_type == MajorStatusType.PARALYSIS and ability_name == "limber":
            return True
        elif (status_type == MajorStatusType.POISON or status_type == MajorStatusType.TOXIC) and ability_name == "immunity":
            return True
        elif status_type == MajorStatusType.SLEEP and ability_name == "insomnia":
            return True
    
    return False

def get_status_description(status_type: MajorStatusType) -> str:
    """获取状态效果的描述"""
    descriptions = {
        MajorStatusType.BURN: "灼伤状态会每回合减少宝可梦1/16最大HP，并降低物理攻击力。",
        MajorStatusType.FREEZE: "冰冻状态使宝可梦无法行动，每回合有20%概率解除。",
        MajorStatusType.PARALYSIS: "麻痹状态有25%概率使宝可梦无法行动，并降低速度。",
        MajorStatusType.POISON: "中毒状态会每回合减少宝可梦1/8最大HP。",
        MajorStatusType.TOXIC: "剧毒状态会每回合减少宝可梦越来越多的HP。",
        MajorStatusType.SLEEP: "睡眠状态使宝可梦无法行动，持续1-3回合。",
        MajorStatusType.NONE: "无状态效果。"
    }
    return descriptions.get(status_type, "未知状态效果。")

def get_status_application_message(status_type: MajorStatusType, pokemon_name: str) -> str:
    """获取状态效果应用时的消息"""
    messages = {
        MajorStatusType.BURN: f"{pokemon_name}被灼伤了！",
        MajorStatusType.FREEZE: f"{pokemon_name}被冰冻了！",
        MajorStatusType.PARALYSIS: f"{pokemon_name}麻痹了！可能无法行动！",
        MajorStatusType.POISON: f"{pokemon_name}中毒了！",
        MajorStatusType.TOXIC: f"{pokemon_name}中了剧毒！",
        MajorStatusType.SLEEP: f"{pokemon_name}睡着了！",
        MajorStatusType.NONE: f"{pokemon_name}恢复了正常状态。"
    }
    return messages.get(status_type, f"{pokemon_name}受到了未知状态效果！")

def get_status_removal_message(status_type: MajorStatusType, pokemon_name: str) -> str:
    """获取状态效果移除时的消息"""
    messages = {
        MajorStatusType.BURN: f"{pokemon_name}的灼伤痊愈了！",
        MajorStatusType.FREEZE: f"{pokemon_name}解冻了！",
        MajorStatusType.PARALYSIS: f"{pokemon_name}不再麻痹了！",
        MajorStatusType.POISON: f"{pokemon_name}的中毒痊愈了！",
        MajorStatusType.TOXIC: f"{pokemon_name}的剧毒痊愈了！",
        MajorStatusType.SLEEP: f"{pokemon_name}醒来了！",
        MajorStatusType.NONE: f"{pokemon_name}没有状态需要移除。"
    }
    return messages.get(status_type, f"{pokemon_name}的未知状态效果被移除了！")

def get_volatile_status_application_message(status_type: VolatileStatusType, pokemon_name: str) -> str:
    """获取易变状态效果应用时的消息"""
    messages = {
        VolatileStatusType.CONFUSED: f"{pokemon_name}混乱了！",
        VolatileStatusType.FLINCH: f"{pokemon_name}畏缩了！",
        VolatileStatusType.LEECH_SEED: f"{pokemon_name}被种子寄生了！",
        VolatileStatusType.BOUND: f"{pokemon_name}被束缚住了！",
        VolatileStatusType.TAUNT: f"{pokemon_name}被挑衅了！",
        VolatileStatusType.INFATUATION: f"{pokemon_name}着迷了！",
        VolatileStatusType.IDENTIFIED: f"{pokemon_name}被识破了！"
    }
    return messages.get(status_type, f"{pokemon_name}受到了未知易变状态效果！")

def get_volatile_status_removal_message(status_type: VolatileStatusType, pokemon_name: str) -> str:
    """获取易变状态效果移除时的消息"""
    messages = {
        VolatileStatusType.CONFUSED: f"{pokemon_name}不再混乱了！",
        VolatileStatusType.FLINCH: f"{pokemon_name}不再畏缩了！",
        VolatileStatusType.LEECH_SEED: f"{pokemon_name}摆脱了种子寄生！",
        VolatileStatusType.BOUND: f"{pokemon_name}挣脱了束缚！",
        VolatileStatusType.TAUNT: f"{pokemon_name}不再受到挑衅了！",
        VolatileStatusType.INFATUATION: f"{pokemon_name}不再着迷了！",
        VolatileStatusType.IDENTIFIED: f"{pokemon_name}不再被识破了！"
    }
    return messages.get(status_type, f"{pokemon_name}的未知易变状态效果被移除了！")

def get_status_effect_id(status_type: MajorStatusType) -> int:
    """获取状态效果ID（应该从元数据获取，这里只是示例）"""
    status_ids = {
        MajorStatusType.BURN: 1,
        MajorStatusType.FREEZE: 2,
        MajorStatusType.PARALYSIS: 3,
        MajorStatusType.POISON: 4,
        MajorStatusType.TOXIC: 5,
        MajorStatusType.SLEEP: 6,
        MajorStatusType.NONE: 0
    }
    return status_ids.get(status_type, 0)
