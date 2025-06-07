# Import battle related core logic functions and classes
from .formulas import (
    calculate_stats, 
    calculate_damage, 
    calculate_catch_rate, 
    calculate_exp_needed,
    calculate_type_effectiveness,
    check_accuracy,
    check_critical_hit,
    calculate_stat_stage_modifier,
    get_effective_stat
)
from .battle_logic import BattleLogic
from .encounter_logic import EncounterLogic, encounter_logic
from .status_effect_handler import StatusEffectHandler
from .events import (
    BattleEvent,
    StatStageChangeEvent,
    DamageDealtEvent,
    FaintEvent,
    StatusEffectAppliedEvent,
    StatusEffectRemovedEvent,
    HealEvent,
    BattleMessageEvent,
    MissEvent
)

# Optionally define __all__ for explicit exports
__all__ = [
    # Formula functions
    "calculate_stats",
    "calculate_damage",
    "calculate_catch_rate",
    "calculate_exp_needed",
    "calculate_type_effectiveness",
    "check_accuracy",
    "check_critical_hit",
    "calculate_stat_stage_modifier",
    "get_effective_stat",
    
    # Core classes
    "BattleLogic",
    "EncounterLogic", 
    "encounter_logic",
    "StatusEffectHandler",
    
    # Event classes
    "BattleEvent",
    "StatStageChangeEvent", 
    "DamageDealtEvent",
    "FaintEvent",
    "StatusEffectAppliedEvent",
    "StatusEffectRemovedEvent",
    "HealEvent",
    "BattleMessageEvent",
    "MissEvent",
]
