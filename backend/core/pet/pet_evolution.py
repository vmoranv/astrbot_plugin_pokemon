from typing import Optional, Dict, List, Tuple
from backend.models.pokemon import Pokemon
from backend.models.race import Race
from backend.models.skill import Skill
from backend.core.battle.formulas import calculate_stats
from backend.utils.logger import get_logger

logger = get_logger(__name__)

async def check_evolution(pokemon: Pokemon, race_data: Race) -> Optional[int]:
    """
    检查宝可梦是否满足进化条件。
    
    Args:
        pokemon: 要检查的宝可梦
        race_data: 宝可梦当前种族数据
        
    Returns:
        如果可以进化，返回进化后的种族ID；否则返回None
    """
    # 如果没有进化信息，则无法进化
    if not hasattr(race_data, 'evolution_data') or not race_data.evolution_data:
        return None
    
    for evolution in race_data.evolution_data:
        # 基于不同的进化条件检查
        if evolution.get('method') == 'level':
            # 等级进化
            required_level = evolution.get('level', 100)
            if pokemon.level >= required_level:
                return evolution.get('evolves_to')
                
        elif evolution.get('method') == 'item':
            # 道具进化（需要在服务层处理，这里只检查条件）
            # 返回可以使用哪个道具进化的信息
            return evolution.get('evolves_to')
            
        elif evolution.get('method') == 'trade':
            # 交换进化（同样需要在服务层处理）
            # 可能有额外条件，如持有特定道具
            if not evolution.get('held_item') or (hasattr(pokemon, 'held_item') and 
                                                 pokemon.held_item and 
                                                 pokemon.held_item.item_id == evolution.get('held_item')):
                return evolution.get('evolves_to')
                
        elif evolution.get('method') == 'friendship':
            # 友好度进化
            required_friendship = evolution.get('min_friendship', 220)
            if hasattr(pokemon, 'friendship') and pokemon.friendship >= required_friendship:
                # 可能有时间条件（白天/夜晚）
                time_condition = evolution.get('time_condition')
                if not time_condition:  # 无时间条件
                    return evolution.get('evolves_to')
                # 时间条件在服务层处理
    
    # 没有满足的进化条件
    return None

async def evolve_pokemon(pokemon: Pokemon, current_race: Race, next_race: Race, available_skills: List[Skill]) -> Tuple[Pokemon, List[str]]:
    """
    将宝可梦进化到新种族。
    
    Args:
        pokemon: 要进化的宝可梦
        current_race: 当前种族数据
        next_race: 进化后的种族数据
        available_skills: 进化后可学习的技能列表
        
    Returns:
        进化后的宝可梦对象和描述进化过程的消息列表
    """
    messages = []
    
    # 记录原始数据
    old_name = current_race.name
    old_stats = pokemon.stats.copy() if pokemon.stats else {}
    
    # 更新种族ID和类型
    pokemon.species_id = next_race.species_id
    messages.append(f"恭喜！{pokemon.nickname} 从 {old_name} 进化成了 {next_race.name}！")
    
    # 更新类型
    if hasattr(next_race, 'types'):
        pokemon.types = next_race.types.copy()
        type_names = [t.capitalize() for t in pokemon.types]
        messages.append(f"{pokemon.nickname} 现在是 {' 和 '.join(type_names)} 属性！")
    
    # 更新基础数据（可能需要更新其他属性，如体重、身高等）
    if hasattr(next_race, 'base_stats'):
        # 重新计算统计数据
        pokemon.stats = calculate_stats(pokemon, next_race)
        
        # 生成统计数据变化消息
        if old_stats:
            stat_changes = []
            for stat, new_value in pokemon.stats.items():
                if stat in old_stats:
                    change = new_value - old_stats[stat]
                    if change != 0:
                        stat_changes.append(f"{stat.capitalize()}: {'+' if change > 0 else ''}{change}")
            
            if stat_changes:
                messages.append(f"能力值变化：{', '.join(stat_changes)}")
    
    # 更新当前HP（可选，根据游戏规则决定是否恢复）
    old_hp_percent = pokemon.current_hp / old_stats.get("hp", 100) if old_stats.get("hp", 0) > 0 else 1.0
    pokemon.current_hp = int(pokemon.stats["hp"] * old_hp_percent)
    
    # 检查进化后可学习的新技能
    evolution_skills = _get_evolution_skills(next_race.species_id, available_skills)
    
    for skill in evolution_skills:
        # 检查技能槽是否已满
        if len(pokemon.skills) >= 4:
            messages.append(f"{pokemon.nickname} 想学习 {skill.name}，但已经知道了4个技能！")
        else:
            # 添加新技能
            pokemon.skills.append(skill)
            messages.append(f"{pokemon.nickname} 学会了 {skill.name}！")
    
    # 清除进化标志
    pokemon.can_evolve_to = None
    
    return pokemon, messages

def _get_evolution_skills(species_id: int, available_skills: List[Skill]) -> List[Skill]:
    """
    获取宝可梦进化时可以学习的特殊技能。
    
    Args:
        species_id: 进化后的种族ID
        available_skills: 所有可用技能列表
        
    Returns:
        进化时可学习的技能列表
    """
    evolution_skills = []
    
    for skill in available_skills:
        # 检查技能是否为进化时学习的技能
        if hasattr(skill, 'learn_method') and skill.learn_method == 'evolution' and \
           hasattr(skill, 'learnable_by') and species_id in skill.learnable_by:
            evolution_skills.append(skill)
    
    return evolution_skills

async def check_mega_evolution(pokemon: Pokemon, held_item: Optional[Dict] = None) -> Optional[int]:
    """
    检查宝可梦是否可以进行超级进化。
    
    Args:
        pokemon: 要检查的宝可梦
        held_item: 宝可梦持有的道具信息
        
    Returns:
        如果可以超级进化，返回超级进化形态的ID；否则返回None
    """
    # 超级进化需要特定的超级石
    if not held_item or not hasattr(held_item, 'effect_type') or held_item.effect_type != 'mega_stone':
        return None
    
    # 检查该超级石是否对应该宝可梦
    if hasattr(held_item, 'specific_pokemon') and held_item.specific_pokemon != pokemon.species_id:
        return None
    
    # 返回超级进化形态ID
    return held_item.get('mega_evolution_id')

async def perform_mega_evolution(pokemon: Pokemon, mega_race: Race) -> Tuple[Pokemon, List[str]]:
    """
    执行宝可梦的超级进化。
    
    Args:
        pokemon: 要超级进化的宝可梦
        mega_race: 超级进化形态的种族数据
        
    Returns:
        超级进化后的宝可梦对象和描述超级进化过程的消息列表
    """
    messages = []
    
    # 记录原始数据
    old_stats = pokemon.stats.copy() if pokemon.stats else {}
    
    # 标记为超级进化状态
    pokemon.is_mega_evolved = True
    pokemon.original_species_id = pokemon.species_id
    pokemon.species_id = mega_race.species_id
    
    messages.append(f"{pokemon.nickname} 超级进化成了 {mega_race.name}！")
    
    # 更新类型
    if hasattr(mega_race, 'types'):
        pokemon.types = mega_race.types.copy()
        type_names = [t.capitalize() for t in pokemon.types]
        messages.append(f"{pokemon.nickname} 现在是 {' 和 '.join(type_names)} 属性！")
    
    # 更新特性
    if hasattr(mega_race, 'abilities') and mega_race.abilities:
        pokemon.ability = mega_race.abilities[0]  # 通常超级进化只有一个特定特性
        messages.append(f"{pokemon.nickname} 的特性变成了 {pokemon.ability.name}！")
    
    # 更新统计数据
    pokemon.stats = calculate_stats(pokemon, mega_race)
    
    # 生成统计数据变化消息
    if old_stats:
        stat_changes = []
        for stat, new_value in pokemon.stats.items():
            if stat in old_stats:
                change = new_value - old_stats[stat]
                if change != 0:
                    stat_changes.append(f"{stat.capitalize()}: {'+' if change > 0 else ''}{change}")
        
        if stat_changes:
            messages.append(f"能力值变化：{', '.join(stat_changes)}")
    
    return pokemon, messages
