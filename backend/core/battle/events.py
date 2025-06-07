from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from backend.models.pokemon import Pokemon # Import Pokemon model
from backend.models.skill import Skill # Import Skill model
from backend.models.status_effect import StatusEffect # Import StatusEffect model
from backend.models.ability import Ability # Import Ability model
from backend.models.item import Item # Import Item model for item trigger event

@dataclass
class BattleEvent:
    """Base class for all battle events."""
    event_type: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "details": self.details,
        }

@dataclass
class StatStageChangeEvent(BattleEvent):
    """Event triggered when a Pokemon's stat stage changes."""
    pokemon: Pokemon
    stat_type: str
    stages_changed: int
    new_stage: int
    message: str
    event_type: str = "stat_stage_change" # Define event_type

    def __post_init__(self):
        # Store relevant details in the base class details dict as well
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "stat_type": self.stat_type,
            "stages_changed": self.stages_changed,
            "new_stage": self.new_stage,
            "message": self.message,
        }

@dataclass
class DamageDealtEvent(BattleEvent):
    """Event triggered when a Pokemon deals damage to another."""
    attacker: Pokemon
    defender: Pokemon
    skill: Skill
    damage: int
    is_critical: bool
    is_effective: bool
    is_not_effective: bool
    is_immune: bool
    message: str
    event_type: str = "damage_dealt" # Define event_type

    def __post_init__(self):
        self.details = {
            "attacker_instance_id": self.attacker.instance_id,
            "defender_instance_id": self.defender.instance_id,
            "skill_id": self.skill.skill_id,
            "damage": self.damage,
            "is_critical": self.is_critical,
            "is_effective": self.is_effective,
            "is_not_effective": self.is_not_effective,
            "is_immune": self.is_immune,
            "message": self.message,
        }

@dataclass
class FaintEvent(BattleEvent):
    """Event triggered when a Pokemon faints."""
    fainted_pokemon: Pokemon
    message: str
    event_type: str = "faint" # Define event_type

    def __post_init__(self):
        self.details = {
            "fainted_pokemon_instance_id": self.fainted_pokemon.instance_id,
            "message": self.message,
        }

@dataclass
class StatusEffectAppliedEvent(BattleEvent):
    """Event triggered when a status effect is applied to a Pokemon."""
    pokemon: Pokemon
    status_effect: StatusEffect
    message: str
    event_type: str = "status_effect_applied" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "status_effect_id": self.status_effect.status_id,
            "message": self.message,
        }

@dataclass
class StatusEffectRemovedEvent(BattleEvent):
    """Event triggered when a status effect is removed from a Pokemon."""
    pokemon: Pokemon
    status_effect: StatusEffect
    message: str
    event_type: str = "status_effect_removed" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "status_effect_id": self.status_effect.status_id,
            "message": self.message,
        }

@dataclass
class HealEvent(BattleEvent):
    """Event triggered when a Pokemon is healed."""
    pokemon: Pokemon
    amount: int
    message: str
    event_type: str = "heal" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "amount": self.amount,
            "message": self.message,
        }

@dataclass
class AbilityTriggerEvent(BattleEvent):
    """Event triggered when an ability activates."""
    pokemon: Pokemon
    ability: Ability
    message: str
    event_type: str = "ability_trigger" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "ability_id": self.ability.ability_id if self.ability else None, # Assuming Ability has ability_id
            "message": self.message,
        }

@dataclass
class FieldEffectEvent(BattleEvent):
    """Event triggered by changes or effects related to the battle field (weather, terrain)."""
    effect_type: str # e.g., "weather", "terrain"
    effect_name: str
    state: str # e.g., "start", "active", "end"
    message: str
    event_type: str = "field_effect" # Define event_type

    def __post_init__(self):
        self.details = {
            "effect_type": self.effect_type,
            "effect_name": self.effect_name,
            "state": self.state,
            "message": self.message,
        }

@dataclass
class VolatileStatusChangeEvent(BattleEvent):
    """
    表示宝可梦的易变状态变化的事件。
    """
    pokemon: Pokemon
    status_logic_key: str
    is_applied: bool
    message: str = ""
    event_type: str = "volatile_status_change" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "status_logic_key": self.status_logic_key,
            "is_applied": self.is_applied,
            "message": self.message
        }

@dataclass
class ForcedSwitchEvent(BattleEvent):
    """Event triggered when a Pokemon is forced to switch out."""
    pokemon_switched_out: Pokemon
    reason: str # e.g., "skill", "item", "ability"
    reason_details: Optional[Dict[str, Any]] = None # Details about the reason (e.g., skill_id)
    message: str # Message indicating the forced switch
    event_type: str = "forced_switch" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon_switched_out_instance_id": self.pokemon_switched_out.instance_id,
            "reason": self.reason,
            "reason_details": self.reason_details,
            "message": self.message,
        }

@dataclass
class ItemTriggerEvent(BattleEvent):
    """Event triggered when an item activates or is consumed."""
    pokemon: Pokemon
    item: Item
    message: str
    event_type: str = "item_trigger" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "item_id": self.item.item_id if self.item else None, # Assuming Item has item_id
            "message": self.message,
        }

@dataclass
class AbilityChangeEvent(BattleEvent):
    """Event triggered when a Pokemon's ability changes."""
    pokemon: Pokemon
    old_ability: Optional[Ability]
    new_ability: Optional[Ability]
    reason: str # e.g., "Gastro Acid", "Simple Beam"
    message: str
    event_type: str = "ability_change" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "old_ability_id": self.old_ability.ability_id if self.old_ability else None,
            "new_ability_id": self.new_ability.ability_id if self.new_ability else None,
            "reason": self.reason,
            "message": self.message,
        }

@dataclass
class MoveMissedEvent(BattleEvent):
    """Event triggered when a skill misses."""
    attacker: Pokemon
    target: Pokemon
    skill: Skill
    message: str
    event_type: str = "move_missed" # Define event_type

    def __post_init__(self):
        self.details = {
            "attacker_instance_id": self.attacker.instance_id,
            "target_instance_id": self.target.instance_id,
            "skill_id": self.skill.skill_id,
            "message": self.message,
        }

@dataclass
class SwitchOutEvent(BattleEvent):
    """Event triggered when a Pokemon is switched out."""
    pokemon: Pokemon
    message: str
    event_type: str = "switch_out" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "message": self.message,
        }

@dataclass
class SwitchInEvent(BattleEvent):
    """Event triggered when a Pokemon is switched in."""
    pokemon: Pokemon
    message: str
    event_type: str = "switch_in" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "message": self.message,
        }

@dataclass
class BattleMessageEvent(BattleEvent):
    """A generic event for displaying a simple battle message."""
    message: str
    event_type: str = "battle_message" # Define event_type

    def __post_init__(self):
        self.details = {
            "message": self.message,
        }

@dataclass
class ConfusionDamageEvent(BattleEvent):
    """
    表示宝可梦因混乱而自伤的事件。
    """
    pokemon: Pokemon
    damage: int
    old_hp: int
    new_hp: int
    event_type: str = "confusion_damage" # Define event_type

    def __post_init__(self):
        self.details = {
            "pokemon": self.pokemon.to_dict() if self.pokemon else None,
            "damage": self.damage,
            "old_hp": self.old_hp,
            "new_hp": self.new_hp
        }

@dataclass
class FlinchEvent(BattleEvent):
    """
    表示宝可梦畏缩的事件。
    """
    def __init__(self, pokemon: Pokemon):
        super().__init__(event_type="flinch")
        self.pokemon = pokemon
        
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "pokemon": self.pokemon.to_dict() if self.pokemon else None
        })
        return base_dict

@dataclass
class VolatileStatusAppliedEvent(BattleEvent):
    """表示宝可梦获得临时战斗状态的事件。"""
    pokemon: Pokemon
    status_type: str
    turns: Optional[int]
    message: str
    event_type: str = "volatile_status_applied"

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "status_type": self.status_type,
            "turns": self.turns,
            "message": self.message,
        }

@dataclass
class VolatileStatusRemovedEvent(BattleEvent):
    """表示宝可梦临时战斗状态被移除的事件。"""
    pokemon: Pokemon
    status_type: str
    message: str
    event_type: str = "volatile_status_removed"

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "status_type": self.status_type,
            "message": self.message,
        }

@dataclass
class VolatileStatusTriggeredEvent(BattleEvent):
    """表示宝可梦临时战斗状态触发效果的事件。"""
    pokemon: Pokemon
    status_type: str
    effect_description: str
    message: str
    event_type: str = "volatile_status_triggered"

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "status_type": self.status_type,
            "effect_description": self.effect_description,
            "message": self.message,
        }

@dataclass
class FieldEffectAppliedEvent(BattleEvent):
    """表示场地效果被应用的事件。"""
    effect_id: int
    effect_name: str
    effect_type: str  # "weather" 或 "terrain"
    duration: int
    message: str
    event_type: str = "field_effect_applied"

    def __post_init__(self):
        self.details = {
            "effect_id": self.effect_id,
            "effect_name": self.effect_name,
            "effect_type": self.effect_type,
            "duration": self.duration,
            "message": self.message,
        }

@dataclass
class FieldEffectRemovedEvent(BattleEvent):
    """表示场地效果结束的事件。"""
    effect_id: int
    effect_name: str
    effect_type: str  # "weather" 或 "terrain"
    message: str
    event_type: str = "field_effect_removed"

    def __post_init__(self):
        self.details = {
            "effect_id": self.effect_id,
            "effect_name": self.effect_name,
            "effect_type": self.effect_type,
            "message": self.message,
        }

@dataclass
class FieldEffectDamageEvent(BattleEvent):
    """表示场地效果造成伤害的事件。"""
    effect_id: int
    effect_name: str
    pokemon_instance_id: int
    pokemon_name: str
    damage: int
    message: str
    event_type: str = "field_effect_damage"

    def __post_init__(self):
        self.details = {
            "effect_id": self.effect_id,
            "effect_name": self.effect_name,
            "pokemon_instance_id": self.pokemon_instance_id,
            "pokemon_name": self.pokemon_name,
            "damage": self.damage,
            "message": self.message,
        }

@dataclass
class ItemEffectTriggeredEvent(BattleEvent):
    """表示道具效果被触发的事件。"""
    item_id: int
    item_name: str
    holder_instance_id: int
    holder_name: str
    effect_description: str
    message: str
    event_type: str = "item_effect_triggered"

    def __post_init__(self):
        self.details = {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "holder_instance_id": self.holder_instance_id,
            "holder_name": self.holder_name,
            "effect_description": self.effect_description,
            "message": self.message,
        }

@dataclass
class ItemConsumedEvent(BattleEvent):
    """表示道具被消耗的事件。"""
    item_id: int
    item_name: str
    user_id: str  # 玩家ID或宝可梦ID
    user_name: str
    message: str
    event_type: str = "item_consumed"

    def __post_init__(self):
        self.details = {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "message": self.message,
        }

@dataclass
class CriticalHitEvent(BattleEvent):
    """表示暴击的事件。"""
    attacker_instance_id: int
    attacker_name: str
    defender_instance_id: int
    defender_name: str
    skill_id: int
    skill_name: str
    message: str
    event_type: str = "critical_hit"

    def __post_init__(self):
        self.details = {
            "attacker_instance_id": self.attacker_instance_id,
            "attacker_name": self.attacker_name,
            "defender_instance_id": self.defender_instance_id,
            "defender_name": self.defender_name,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "message": self.message,
        }

@dataclass
class TypeEffectivenessEvent(BattleEvent):
    """表示属性相克效果的事件。"""
    attacker_instance_id: int
    attacker_name: str
    defender_instance_id: int
    defender_name: str
    skill_id: int
    skill_name: str
    effectiveness: float  # 0.5, 1.0, 2.0 等
    message: str
    event_type: str = "type_effectiveness"

    def __post_init__(self):
        self.details = {
            "attacker_instance_id": self.attacker_instance_id,
            "attacker_name": self.attacker_name,
            "defender_instance_id": self.defender_instance_id,
            "defender_name": self.defender_name,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "effectiveness": self.effectiveness,
            "message": self.message,
        }

@dataclass
class SkillHitEvent(BattleEvent):
    """表示技能命中的事件。"""
    attacker_instance_id: int
    attacker_name: str
    defender_instance_id: int
    defender_name: str
    skill_id: int
    skill_name: str
    message: str
    event_type: str = "skill_hit"

    def __post_init__(self):
        self.details = {
            "attacker_instance_id": self.attacker_instance_id,
            "attacker_name": self.attacker_name,
            "defender_instance_id": self.defender_instance_id,
            "defender_name": self.defender_name,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "message": self.message,
        }

@dataclass
class StatusConditionMessageEvent(BattleEvent):
    """表示状态条件相关消息的事件。"""
    pokemon_instance_id: int
    pokemon_name: str
    status_id: int
    status_name: str
    effect_description: str
    message: str
    event_type: str = "status_condition_message"

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon_instance_id,
            "pokemon_name": self.pokemon_name,
            "status_id": self.status_id,
            "status_name": self.status_name,
            "effect_description": self.effect_description,
            "message": self.message,
        }

@dataclass
class BattleStartEvent(BattleEvent):
    """表示战斗开始的事件。"""
    player_id: str
    opponent_type: str  # "wild", "trainer", "gym_leader" 等
    opponent_id: Optional[str] = None  # 如果是训练师战斗
    message: str
    event_type: str = "battle_start"

    def __post_init__(self):
        self.details = {
            "player_id": self.player_id,
            "opponent_type": self.opponent_type,
            "opponent_id": self.opponent_id,
            "message": self.message,
        }

@dataclass
class BattleEndEvent(BattleEvent):
    """表示战斗结束的事件。"""
    player_id: str
    result: str  # "win", "loss", "draw", "escape" 等
    reward_exp: int = 0
    reward_money: int = 0
    message: str
    event_type: str = "battle_end"

    def __post_init__(self):
        self.details = {
            "player_id": self.player_id,
            "result": self.result,
            "reward_exp": self.reward_exp,
            "reward_money": self.reward_money,
            "message": self.message,
        }

@dataclass
class TurnStartEvent(BattleEvent):
    """表示回合开始的事件。"""
    turn_number: int
    message: str
    event_type: str = "turn_start"

    def __post_init__(self):
        self.details = {
            "turn_number": self.turn_number,
            "message": self.message,
        }

@dataclass
class TurnEndEvent(BattleEvent):
    """表示回合结束的事件。"""
    turn_number: int
    message: str
    event_type: str = "turn_end"

    def __post_init__(self):
        self.details = {
            "turn_number": self.turn_number,
            "message": self.message,
        }

@dataclass
class SkillLearnedEvent(BattleEvent):
    """表示宝可梦学习新技能的事件。"""
    pokemon_instance_id: int
    pokemon_name: str
    skill_id: int
    skill_name: str
    message: str
    event_type: str = "skill_learned"

    def __post_init__(self):
        self.details = {
            "pokemon_instance_id": self.pokemon_instance_id,
            "pokemon_name": self.pokemon_name,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "message": self.message,
        }
