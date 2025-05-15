from dataclasses import dataclass, field
from typing import Any, Dict, Optional
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

@dataclass
class StatStageChangeEvent(BattleEvent):
    """Event triggered when a Pokemon's stat stage changes."""
    pokemon: Pokemon
    stat_type: str
    stages_changed: int
    new_stage: int
    message: str

    def __post_init__(self):
        # Set event_type automatically
        self.event_type = "stat_stage_change"
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

    def __post_init__(self):
        self.event_type = "damage_dealt"
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

    def __post_init__(self):
        self.event_type = "faint"
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

    def __post_init__(self):
        self.event_type = "status_effect_applied"
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

    def __post_init__(self):
        self.event_type = "status_effect_removed"
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

    def __post_init__(self):
        self.event_type = "heal"
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

    def __post_init__(self):
        self.event_type = "ability_trigger"
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

    def __post_init__(self):
        self.event_type = "field_effect"
        self.details = {
            "effect_type": self.effect_type,
            "effect_name": self.effect_name,
            "state": self.state,
            "message": self.message,
        }

@dataclass
class VolatileStatusChangeEvent(BattleEvent):
    """Event triggered when a Pokemon's volatile status changes (applied, active, removed)."""
    pokemon: Pokemon
    volatile_status_type: str # e.g., "confusion", "flinch", "bound"
    state: str # e.g., "applied", "active", "removed"
    message: str # Message related to the volatile status change

    def __post_init__(self):
        self.event_type = "volatile_status_change"
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "volatile_status_type": self.volatile_status_type,
            "state": self.state,
            "message": self.message,
        }

@dataclass
class ForcedSwitchEvent(BattleEvent):
    """Event triggered when a Pokemon is forced to switch out."""
    pokemon_switched_out: Pokemon
    reason: str # e.g., "skill", "item", "ability"
    reason_details: Optional[Dict[str, Any]] = None # Details about the reason (e.g., skill_id)
    message: str # Message indicating the forced switch

    def __post_init__(self):
        self.event_type = "forced_switch"
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

    def __post_init__(self):
        self.event_type = "item_trigger"
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

    def __post_init__(self):
        self.event_type = "ability_change"
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

    def __post_init__(self):
        self.event_type = "move_missed"
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

    def __post_init__(self):
        self.event_type = "switch_out"
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "message": self.message,
        }

@dataclass
class SwitchInEvent(BattleEvent):
    """Event triggered when a Pokemon is switched in."""
    pokemon: Pokemon
    message: str

    def __post_init__(self):
        self.event_type = "switch_in"
        self.details = {
            "pokemon_instance_id": self.pokemon.instance_id,
            "message": self.message,
        }

@dataclass
class BattleMessageEvent(BattleEvent):
    """A generic event for displaying a simple battle message."""
    message: str

    def __post_init__(self):
        self.event_type = "battle_message"
        self.details = {
            "message": self.message,
        }

@dataclass
class ConfusionDamageEvent(BattleEvent):
    """Event indicating a confused Pokemon hit itself."""
    pokemon: Pokemon
    base_power: int # Base power for confusion self-damage

    def __post_init__(self):
        self.event_type = "confusion_damage"
        self.details['pokemon'] = self.pokemon.nickname
        self.details['base_power'] = self.base_power

# TODO: Add other battle event types here (S1 refinement)
# TODO: Add events for healing, status effect application/removal, volatile status changes, etc. (S1 refinement)
# TODO: Add events for volatile status changes (e.g., confusion, flinch) (S1 refinement)
# TODO: Add events for field effects (weather, terrain) (S1 refinement)
# TODO: Add events for forced switches (e.g., from moves like Roar) (S1 refinement)
# TODO: Add events for item trigger effects (S1 refinement)
# TODO: Add events for ability changes (e.g., Gastro Acid, Simple Beam) (S1 refinement)
# TODO: Add events for critical hits, type effectiveness messages (S1 refinement)
# TODO: Add events for move miss/hit (S1 refinement)
# TODO: Add events for stat stage change messages (S1 refinement)
# TODO: Add events for status condition messages (S1 refinement)
# TODO: Add events for battle start/end messages (S1 refinement)
# TODO: Add events for turn start/end messages (S1 refinement)
# TODO: Add events for switch in/out messages (S1 refinement)
# TODO: Add events for item consumption (S1 refinement)
# TODO: Add events for gaining experience (S1 refinement)
# TODO: Add events for learning skills (S1 refinement)
# TODO: Add events for evolution (S1 refinement)
# TODO: Add events for catch attempts and success/failure (S1 refinement)
# TODO: Add events for run attempts and success/failure (S1 refinement) 