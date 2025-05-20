from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

# Forward declaration for type hinting if Pokemon, Skill, StatusEffect, Item are in this file or imported later
# For now, assuming they will be imported.
# If they are in different files, proper imports are needed:
from backend.models.pokemon import Pokemon # 假设 Pokemon 模型定义在 backend.models.pokemon
from backend.models.skill import Skill # 假设 Skill 模型定义在 backend.models.skill
from backend.models.status_effect import StatusEffect # 假设 StatusEffect 模型定义在 backend.models.status_effect
from backend.models.item import Item # 假设 Item 模型定义在 backend.models.item

@dataclass
class Event:
    """
    事件数据模型。
    对应数据库中的 events 表。
    """
    event_id: int
    name: str
    description: Optional[str] = None
    reward_item_id: Optional[int] = None # 奖励道具ID
    dialog_id: Optional[int] = None # 关联的对话ID
    pet_id: Optional[int] = None # 关联的宝可梦ID

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Event object to a dictionary."""
        return {
            "event_id": self.event_id,
            "name": self.name,
            "description": self.description,
            "reward_item_id": self.reward_item_id,
            "dialog_id": self.dialog_id,
            "pet_id": self.pet_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Event":
        """Creates an Event object from a dictionary."""
        return Event(
            event_id=data["event_id"],
            name=data["name"],
            description=data.get("description"),
            reward_item_id=data.get("reward_item_id"),
            dialog_id=data.get("dialog_id"),
            pet_id=data.get("pet_id"),
        )

# 如果 Event 需要 to_dict 或 from_dict 方法，也请添加类型提示
# def to_dict(self) -> Dict[str, Any]:
#     pass
# @staticmethod
# def from_dict(data: Dict[str, Any]) -> "Event":
#     pass 

# --- Game World Events ---
# 这些事件通常代表游戏中发生的、可能持久化或触发后续逻辑的重要节点。

@dataclass
class PokemonCapturedEvent(Event):
    """宝可梦被成功捕获的事件。继承自通用 Event 以便记录。"""
    # event_id, name, description 等字段由 Event 基类提供
    # 我们需要通过 super() 或在创建实例时正确设置它们
    pokemon_species_id: int
    captured_pokemon_instance_id: int # 被捕获的宝可梦实例ID
    pokemon_name: str # 被捕获的宝可梦的名字或种类名
    trainer_id: int # 执行捕获的训练家ID
    message: str # 事件的描述信息

    # 如果需要自定义 to_dict/from_dict，可以覆盖或扩展
    # 默认情况下，dataclass 的字段会被包含


@dataclass
class PokemonEvolvedEvent(Event):
    """宝可梦进化的事件。"""
    pokemon_instance_id: int
    original_species_id: int
    evolved_species_id: int
    original_name: str
    evolved_name: str
    message: str


@dataclass
class PokemonLeveledUpEvent: # 可以不继承 Event，如果只是一个通知
    """宝可梦升级的事件 (瞬时通知)。"""
    pokemon_instance_id: int
    pokemon_name: str
    new_level: int
    message: str


@dataclass
class PokemonLearnedSkillEvent: # 可以不继承 Event
    """宝可梦学会新技能的事件 (瞬时通知)。"""
    pokemon_instance_id: int
    pokemon_name: str
    skill_id: int
    skill_name: str
    message: str


@dataclass
class PokemonUsedItemEvent: # 可以不继承 Event
    """宝可梦使用道具的事件 (瞬时通知)。"""
    pokemon_instance_id: int
    pokemon_name: str
    item_id: int
    item_name: str
    message: str
    # 可以添加效果描述等


# --- Battle Events ---
# 这些事件用于描述战斗中发生的具体情况，通常用于战斗日志或驱动战斗动画/UI。
# 它们通常是瞬时的，不直接持久化到 Event 表。

@dataclass
class BattleEvent:
    """战斗事件的基类。"""
    event_type: str
    # 'details' 字段可以用来存放特定事件的额外信息，但更推荐使用具体的字段
    # details: Dict[str, Any] = field(default_factory=dict)
    message: str = "" # 通用消息字段


@dataclass
class DamageDealtEvent(BattleEvent):
    """造成伤害的事件。"""
    attacker_instance_id: int
    attacker_name: str
    defender_instance_id: int
    defender_name: str
    skill_id: Optional[int] = None
    skill_name: Optional[str] = None
    damage: int
    is_critical: bool = False
    effectiveness: Optional[str] = None # e.g., "super_effective", "not_very_effective", "immune"
    current_hp_defender: int
    max_hp_defender: int
    event_type: str = "damage_dealt"


@dataclass
class BattleStatusEffectAppliedEvent(BattleEvent):
    """战斗中状态效果被施加的事件。"""
    target_instance_id: int
    target_name: str
    status_effect_name: str # 例如 "poison", "sleep"
    source_skill_id: Optional[int] = None
    event_type: str = "battle_status_effect_applied"


@dataclass
class BattleStatusEffectRemovedEvent(BattleEvent):
    """战斗中状态效果被移除的事件。"""
    target_instance_id: int
    target_name: str
    status_effect_name: str
    event_type: str = "battle_status_effect_removed"


@dataclass
class FaintEvent(BattleEvent):
    """宝可梦陷入濒死状态的事件。"""
    pokemon_instance_id: int
    pokemon_name: str
    event_type: str = "faint"


@dataclass
class StatStageChangeEvent(BattleEvent):
    """能力等级变化的事件。"""
    target_instance_id: int
    target_name: str
    stat_name: str # e.g., "attack", "defense"
    change_amount: int # e.g., +1, -2
    current_stage: int
    event_type: str = "stat_stage_change"


@dataclass
class VolatileStatusAppliedEvent(BattleEvent):
    """宝可梦获得临时战斗状态的事件。"""
    target_instance_id: int
    target_name: str
    status_type: str # e.g., "flinch", "confusion"
    turns: Optional[int] = None
    event_type: str = "volatile_status_applied"


@dataclass
class VolatileStatusRemovedEvent(BattleEvent):
    """宝可梦临时战斗状态被移除的事件。"""
    target_instance_id: int
    target_name: str
    status_type: str
    event_type: str = "volatile_status_removed"


@dataclass
class VolatileStatusTriggeredEvent(BattleEvent):
    """宝可梦临时战斗状态触发效果的事件。"""
    target_instance_id: int
    target_name: str
    status_type: str
    effect_description: str # 描述触发的具体效果
    event_type: str = "volatile_status_triggered"


@dataclass
class ConfusionDamageEvent(BattleEvent):
    """混乱状态导致自我攻击的事件。"""
    pokemon_instance_id: int
    pokemon_name: str
    damage: int
    current_hp: int
    max_hp: int
    event_type: str = "confusion_damage"


@dataclass
class FlinchEvent(BattleEvent):
    """宝可梦因畏缩而无法行动的事件。"""
    pokemon_instance_id: int
    pokemon_name: str
    event_type: str = "flinch"


@dataclass
class BattleMessageEvent(BattleEvent):
    """通用的战斗消息事件。"""
    # message 字段已在 BattleEvent 基类中
    event_type: str = "battle_message"


@dataclass
class MissEvent(BattleEvent):
    """攻击未命中的事件。"""
    attacker_instance_id: int
    attacker_name: str
    defender_instance_id: int
    defender_name: str
    skill_name: Optional[str] = None
    event_type: str = "miss"

@dataclass
class HealEvent(BattleEvent):
    """治疗事件（HP恢复）。"""
    target_instance_id: int
    target_name: str
    amount_healed: int
    current_hp: int
    max_hp: int
    source: Optional[str] = None # e.g., "item", "skill"
    event_type: str = "heal"

@dataclass
class ExpGainEvent(BattleEvent): # 或者可以是 Game World Event
    """获得经验值的事件。"""
    pokemon_instance_id: int
    pokemon_name: str
    exp_gained: int
    message: str # 覆盖基类 message，或让基类 message 为空
    event_type: str = "exp_gain"

# ... 可以根据需要添加更多特定事件 ... 