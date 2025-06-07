# Import pet related core logic functions and classes
from .pet_skill import learn_skill, forget_skill, use_skill, replace_skill
from .pet_grow import gain_experience, level_up, calculate_exp_needed, gain_evs, generate_ivs
from .pet_catch import calculate_catch_success
from .pet_evolution import check_evolution, evolve_pokemon, check_mega_evolution, perform_mega_evolution
from .pet_item import use_item_on_pokemon
from .pet_system import get_pokemon_stats, calculate_happiness, get_evolution_requirements, generate_wild_pokemon
from .pet_equipment import equip_item, unequip_item, get_equipment_effects, check_battle_item_trigger
from .evolution_handler import EvolutionHandler

# Optionally define __all__ for explicit exports
__all__ = [
    # 技能相关
    "learn_skill",
    "forget_skill", 
    "use_skill",
    "replace_skill",
    
    # 成长相关
    "gain_experience",
    "level_up",
    "calculate_exp_needed",
    "gain_evs",
    "generate_ivs",
    
    # 捕获相关
    "calculate_catch_success",
    
    # 进化相关
    "check_evolution",
    "evolve_pokemon",
    "check_mega_evolution",
    "perform_mega_evolution",
    "EvolutionHandler",
    
    # 道具相关
    "use_item_on_pokemon",
    
    # 装备相关
    "equip_item",
    "unequip_item",
    "get_equipment_effects",
    "check_battle_item_trigger",
    
    # 系统相关
    "get_pokemon_stats",
    "calculate_happiness",
    "get_evolution_requirements",
    "generate_wild_pokemon",
]
