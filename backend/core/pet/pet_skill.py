from typing import List, Optional, Dict, Tuple, Any
import random
from backend.models.pokemon import Pokemon
from backend.models.skill import Skill
from backend.models.battle import Battle
from backend.core.battle.status_effect import MajorStatusType, VolatileStatusType, apply_major_status, apply_volatile_status
from backend.core.battle.formulas import calculate_damage, get_type_effectiveness
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Core logic functions should receive necessary data as arguments, not fetch it themselves.

async def learn_skill(pokemon: Pokemon, skill: Skill) -> Tuple[bool, str]:
    """
    教导宝可梦学习技能。
    检查宝可梦是否可以学习该技能以及是否有空间。
    
    Args:
        pokemon: 要学习技能的宝可梦
        skill: 要学习的技能
        
    Returns:
        布尔值表示是否成功学习和结果消息的元组
    """
    # 检查技能是否已学会
    if any(s.skill_id == skill.skill_id for s in pokemon.skills):
        return False, f"{pokemon.nickname} 已经学会了 {skill.name}。"
    
    # 检查技能槽是否已满
    if len(pokemon.skills) >= 4:
        return False, f"{pokemon.nickname} 已经知道了4个技能，无法学习更多技能。"
    
    # 学习技能
    pokemon.skills.append(skill)
    return True, f"{pokemon.nickname} 学会了 {skill.name}！"

async def forget_skill(pokemon: Pokemon, skill_id: int) -> Tuple[bool, str]:
    """
    让宝可梦忘记某个技能。
    
    Args:
        pokemon: 要忘记技能的宝可梦
        skill_id: 要忘记的技能ID
        
    Returns:
        布尔值表示是否成功忘记和结果消息的元组
    """
    # 检查宝可梦是否有该技能
    skill_to_forget = None
    for skill in pokemon.skills:
        if skill.skill_id == skill_id:
            skill_to_forget = skill
            break
    
    if not skill_to_forget:
        return False, f"{pokemon.nickname} 没有学会ID为 {skill_id} 的技能。"
    
    # 移除技能
    pokemon.skills = [s for s in pokemon.skills if s.skill_id != skill_id]
    return True, f"{pokemon.nickname} 忘记了 {skill_to_forget.name}。"

async def replace_skill(pokemon: Pokemon, new_skill: Skill, old_skill_id: int) -> Tuple[bool, str]:
    """
    替换宝可梦的某个技能。
    
    Args:
        pokemon: 要替换技能的宝可梦
        new_skill: 新技能
        old_skill_id: 要替换的旧技能ID
        
    Returns:
        布尔值表示是否成功替换和结果消息的元组
    """
    # 检查是否已学会新技能
    if any(s.skill_id == new_skill.skill_id for s in pokemon.skills):
        return False, f"{pokemon.nickname} 已经学会了 {new_skill.name}。"
    
    # 找到要替换的技能
    skill_index = None
    old_skill_name = None
    for i, skill in enumerate(pokemon.skills):
        if skill.skill_id == old_skill_id:
            skill_index = i
            old_skill_name = skill.name
            break
    
    if skill_index is None:
        return False, f"{pokemon.nickname} 没有学会ID为 {old_skill_id} 的技能。"
    
    # 替换技能
    pokemon.skills[skill_index] = new_skill
    return True, f"{pokemon.nickname} 忘记了 {old_skill_name}，学会了 {new_skill.name}！"

async def use_skill(attacker: Pokemon, target: Pokemon, skill: Skill, battle_context: Dict = None) -> Dict[str, Any]:
    """
    在战斗中使用技能。
    
    Args:
        attacker: 使用技能的宝可梦
        target: 技能目标宝可梦
        skill: 使用的技能
        battle_context: 战斗上下文信息
        
    Returns:
        包含技能使用结果的字典，包括伤害、效果、消息等
    """
    if not battle_context:
        battle_context = {}
    
    result = {
        "success": True,
        "damage": 0,
        "critical": False,
        "effectiveness": 1.0,
        "status_effects": [],
        "stat_changes": [],
        "messages": [f"{attacker.nickname} 使用了 {skill.name}！"],
        "effects": []
    }
    
    # 检查PP是否足够
    if skill.current_pp <= 0:
        result["success"] = False
        result["messages"] = [f"{attacker.nickname} 想使用 {skill.name}，但PP不足！"]
        return result
    
    # 扣除PP
    skill.current_pp -= 1
    
    # 检查技能命中
    if not _check_skill_hit(attacker, target, skill, battle_context):
        result["success"] = False
        result["messages"].append(f"{skill.name} 没有命中 {target.nickname}！")
        return result
    
    # 根据技能类型处理效果
    skill_category = skill.category if hasattr(skill, 'category') else "physical"
    
    # 处理伤害技能
    if skill_category in ["physical", "special"]:
        damage_result = await _calculate_skill_damage(attacker, target, skill, battle_context)
        result.update(damage_result)
        
        if damage_result["damage"] > 0:
            # 应用伤害到目标
            target.current_hp = max(0, target.current_hp - damage_result["damage"])
            
            effectiveness_text = ""
            if damage_result["effectiveness"] > 1.5:
                effectiveness_text = "效果拔群！"
            elif damage_result["effectiveness"] > 1.0:
                effectiveness_text = "效果不错。"
            elif damage_result["effectiveness"] < 0.5:
                effectiveness_text = "效果微弱..."
            elif damage_result["effectiveness"] == 0:
                effectiveness_text = f"对 {target.nickname} 没有效果..."
            
            crit_text = "会心一击！" if damage_result["critical"] else ""
            
            damage_message = f"造成了 {damage_result['damage']} 点伤害！"
            if effectiveness_text or crit_text:
                damage_message += f" {effectiveness_text} {crit_text}"
                
            result["messages"].append(damage_message)
    
    # 处理状态技能
    elif skill_category == "status":
        status_result = await _apply_skill_status_effects(attacker, target, skill, battle_context)
        result.update(status_result)
        result["messages"].extend(status_result["messages"])
    
    # 处理技能可能的附加效果
    if hasattr(skill, 'effect_chance') and skill.effect_chance > 0:
        if random.random() * 100 <= skill.effect_chance:
            effect_result = await _apply_skill_additional_effects(attacker, target, skill, battle_context)
            if effect_result["applied"]:
                result["effects"].extend(effect_result["effects"])
                result["messages"].extend(effect_result["messages"])
    
    return result

async def _check_skill_hit(attacker: Pokemon, target: Pokemon, skill: Skill, battle_context: Dict) -> bool:
    """检查技能是否命中"""
    # 获取技能基础命中率
    base_accuracy = skill.accuracy if hasattr(skill, 'accuracy') else 100
    
    # 如果命中率为0或None，则总是命中（如必杀技等）
    if not base_accuracy:
        return True
    
    # 计算实际命中率，考虑命中率和回避率
    attacker_accuracy_stage = attacker.stat_stages.get("accuracy", 0) if hasattr(attacker, 'stat_stages') else 0
    target_evasion_stage = target.stat_stages.get("evasion", 0) if hasattr(target, 'stat_stages') else 0
    
    # 计算命中率修正
    accuracy_multiplier = _calculate_stat_stage_multiplier(attacker_accuracy_stage)
    evasion_multiplier = _calculate_stat_stage_multiplier(target_evasion_stage)
    
    # 计算最终命中率
    final_accuracy = base_accuracy * accuracy_multiplier / evasion_multiplier
    
    # 考虑天气、场地等因素的影响
    if battle_context.get("weather") == "fog":
        final_accuracy *= 0.8  # 雾天命中率降低
    
    # 检查命中
    return random.random() * 100 <= final_accuracy

def _calculate_stat_stage_multiplier(stage: int) -> float:
    """计算能力等级修正倍率"""
    if stage >= 0:
        return (stage + 3) / 3
    else:
        return 3 / (abs(stage) + 3)

async def _calculate_skill_damage(attacker: Pokemon, target: Pokemon, skill: Skill, battle_context: Dict) -> Dict[str, Any]:
    """计算技能造成的伤害"""
    result = {
        "damage": 0,
        "critical": False,
        "effectiveness": 1.0
    }
    
    # 获取技能基础威力
    base_power = skill.power if hasattr(skill, 'power') else 0
    
    # 如果威力为0，则为非伤害技能
    if base_power <= 0:
        return result
    
    # 确定攻击和防御的属性
    if skill.category == "physical":
        attack_stat = attacker.stats.get("attack", 0)
        defense_stat = target.stats.get("defense", 0)
    else:  # special
        attack_stat = attacker.stats.get("special_attack", 0)
        defense_stat = target.stats.get("special_defense", 0)
    
    # 计算伤害
    damage_result = calculate_damage(
        attacker=attacker,
        target=target,
        move_power=base_power,
        move_type=skill.type if hasattr(skill, 'type') else "normal",
        attack_stat=attack_stat,
        defense_stat=defense_stat,
        is_physical=(skill.category == "physical"),
        battle_context=battle_context
    )
    
    return damage_result

async def _apply_skill_status_effects(attacker: Pokemon, target: Pokemon, skill: Skill, battle_context: Dict) -> Dict[str, Any]:
    """应用技能的状态效果"""
    result = {
        "status_effects": [],
        "stat_changes": [],
        "messages": []
    }
    
    # 处理主要状态异常
    if hasattr(skill, 'status_effect') and skill.status_effect:
        try:
            status_type = MajorStatusType(skill.status_effect)
            success, message = await apply_major_status(target, status_type, skill.status_duration if hasattr(skill, 'status_duration') else -1)
            if success:
                result["status_effects"].append({"type": status_type.value, "target": "target"})
                result["messages"].append(message)
        except ValueError:
            # 不是主要状态异常，可能是易变状态
            try:
                status_type = VolatileStatusType(skill.status_effect)
                success, message = await apply_volatile_status(target, status_type, skill.status_duration if hasattr(skill, 'status_duration') else 3)
                if success:
                    result["status_effects"].append({"type": status_type.value, "target": "target"})
                    result["messages"].append(message)
            except ValueError:
                logger.warning(f"未知的状态效果类型: {skill.status_effect}")
    
    # 处理能力变化
    if hasattr(skill, 'stat_changes') and skill.stat_changes:
        for stat_change in skill.stat_changes:
            stat = stat_change.get("stat")
            stages = stat_change.get("stages", 0)
            target_type = stat_change.get("target", "target")  # "self" 或 "target"
            
            if not stat or not stages:
                continue
            
            # 确定能力变化的目标
            stat_target = attacker if target_type == "self" else target
            
            # 应用能力变化
            if not hasattr(stat_target, 'stat_stages'):
                stat_target.stat_stages = {}
            
            current_stage = stat_target.stat_stages.get(stat, 0)
            new_stage = max(-6, min(6, current_stage + stages))
            stat_target.stat_stages[stat] = new_stage
            
            # 生成消息
            target_name = attacker.nickname if target_type == "self" else target.nickname
            if new_stage > current_stage:
                result["messages"].append(f"{target_name} 的 {stat} 提高了！")
            elif new_stage < current_stage:
                result["messages"].append(f"{target_name} 的 {stat} 降低了！")
            else:
                result["messages"].append(f"{target_name} 的 {stat} 已经不能再{'提高' if stages > 0 else '降低'}了！")
            
            result["stat_changes"].append({
                "stat": stat,
                "stages": stages,
                "target": target_type
            })
    
    return result

async def _apply_skill_additional_effects(attacker: Pokemon, target: Pokemon, skill: Skill, battle_context: Dict) -> Dict[str, Any]:
    """应用技能的附加效果"""
    result = {
        "applied": False,
        "effects": [],
        "messages": []
    }
    
    # 如果没有附加效果定义，直接返回
    if not hasattr(skill, 'additional_effects') or not skill.additional_effects:
        return result
    
    # 处理各种附加效果
    for effect in skill.additional_effects:
        effect_type = effect.get("type")
        if not effect_type:
            continue
        
        # 处理状态异常附加效果
        if effect_type == "status":
            status_name = effect.get("status")
            if not status_name:
                continue
            
            try:
                status_type = MajorStatusType(status_name)
                success, message = await apply_major_status(target, status_type, effect.get("duration", -1))
                if success:
                    result["applied"] = True
                    result["effects"].append({"type": "status", "status": status_name, "target": "target"})
                    result["messages"].append(message)
            except ValueError:
                try:
                    status_type = VolatileStatusType(status_name)
                    success, message = await apply_volatile_status(target, status_type, effect.get("duration", 3))
                    if success:
                        result["applied"] = True
                        result["effects"].append({"type": "status", "status": status_name, "target": "target"})
                        result["messages"].append(message)
                except ValueError:
                    logger.warning(f"未知的状态效果类型: {status_name}")
        
        # 处理能力变化附加效果
        elif effect_type == "stat_change":
            stat = effect.get("stat")
            stages = effect.get("stages", 0)
            target_type = effect.get("target", "target")  # "self" 或 "target"
            
            if not stat or not stages:
                continue
            
            # 确定能力变化的目标
            stat_target = attacker if target_type == "self" else target
            
            # 应用能力变化
            if not hasattr(stat_target, 'stat_stages'):
                stat_target.stat_stages = {}
            
            current_stage = stat_target.stat_stages.get(stat, 0)
            new_stage = max(-6, min(6, current_stage + stages))
            stat_target.stat_stages[stat] = new_stage
            
            # 生成消息
            target_name = attacker.nickname if target_type == "self" else target.nickname
            if new_stage > current_stage:
                result["messages"].append(f"{target_name} 的 {stat} 提高了！")
            elif new_stage < current_stage:
                result["messages"].append(f"{target_name} 的 {stat} 降低了！")
            else:
                result["messages"].append(f"{target_name} 的 {stat} 已经不能再{'提高' if stages > 0 else '降低'}了！")
            
            result["applied"] = True
            result["effects"].append({
                "type": "stat_change",
                "stat": stat,
                "stages": stages,
                "target": target_type
            })
    
    return result

# Add other skill related functions as needed (e.g., get_available_skills_at_level)
