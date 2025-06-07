from typing import List, Dict, Any, Optional, Callable, TYPE_CHECKING, Union, Tuple
# Assuming Skill, StatusEffect, Race models will be defined
# from .skill import Skill
# from .status_effect import StatusEffect
# from ..core.battle import formulas # Example dependency for calculations
from dataclasses import dataclass, field
from typing import Optional
import datetime
import uuid # Using uuid for unique instance IDs
import random
import math
import json # Import json for handling JSON strings
import asyncio

# Assuming Race and Skill models are defined
from .race import Race # Import Race model
from .skill import Skill, PokemonSkill # Import Skill model and PokemonSkill
from .status_effect import StatusEffect # Import StatusEffect model
from .attribute import Attribute # Import Attribute model
# Import formula functions
from backend.core.battle.formulas import calculate_exp_needed, calculate_stats, calculate_stat_stage_modifier # Import necessary formulas
# Import BattleEvent and StatStageChangeEvent
from backend.core.battle.events import BattleEvent, StatStageChangeEvent
from backend.utils.logger import get_logger

# Forward declaration for type hinting if Pokemon, Skill, StatusEffect, Item are in this file or imported later
# For now, assuming they will be imported.
# If they are in different files, proper imports are needed:
# from backend.models.pokemon import Pokemon # 假设 Pokemon 模型定义在 backend.models.pokemon
from backend.models.skill import Skill # 假设 Skill 模型定义在 backend.models.skill
from backend.models.status_effect import StatusEffect # 假设 StatusEffect 模型定义在 backend.models.status_effect
from backend.models.item import Item # 假设 Item 模型定义在 backend.models.item
# 导入事件模型
from backend.models.event import (
    Event,
    PokemonLeveledUpEvent,
    PokemonLearnedSkillEvent,
    SkillReplacementRequiredEvent # 新增导入
)

if TYPE_CHECKING:
    from backend.data_access.repositories.metadata_repository import MetadataRepository
    from backend.models.race import Race # 假设 Race 模型定义在 backend.models.race

logger = get_logger(__name__)

# Constants for stat stage limits
MAX_STAT_STAGE = 6
MIN_STAT_STAGE = -6

@dataclass
class StatusEffectInstance:
    """Represents an active status effect on a Pokemon instance."""
    status_id: int
    turns_remaining: Optional[int] = None # None for permanent status like Poison/Burn, int for temporary like Sleep/Freeze

@dataclass
class VolatileStatusInstance:
    """Represents an active volatile (temporary) status effect on a Pokemon in battle."""
    status_type: str  # e.g., "flinch", "confusion", "encore", "taunt", "protect"
    turns_remaining: Optional[int] = None # None for statuses that last until a condition is met or end of turn
    source_skill_id: Optional[int] = None # ID of the skill that caused this status
    # Add other relevant fields, e.g., for confusion, the chance to hit self
    # For encore, the skill_id being encored
    # For protect, the success rate if used consecutively
    data: Dict[str, Any] = field(default_factory=dict) # For storing additional status-specific data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_type": self.status_type,
            "turns_remaining": self.turns_remaining,
            "source_skill_id": self.source_skill_id,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VolatileStatusInstance":
        return cls(
            status_type=data["status_type"],
            turns_remaining=data.get("turns_remaining"),
            source_skill_id=data.get("source_skill_id"),
            data=data.get("data", {}),
        )

@dataclass
class Pokemon:
    """
    Represents a specific instance of a Pokemon owned by a player.

    This model holds the state of a single Pokemon, including its unique ID,
    current stats, experience, status effects, and learned skills with their
    current PP.
    """
    pokemon_id: Optional[int] = None # Unique ID for this instance (from database)
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4())) # Unique ID for battle tracking
    race_id: int # ID of the Pokemon race (e.g., 1 for Bulbasaur)
    owner_id: Optional[str] = None # ID of the player who owns this pokemon (None for wild)
    nickname: str # Nickname of the pokemon
    level: int = 1
    current_hp: Optional[int] = None # Current HP (Optional because it might be loaded after max_hp)
    experience: int = 0
    # Calculated stats (stored for convenience, should be recalculated on level up/stat change)
    max_hp: Optional[int] = None
    attack: Optional[int] = None
    defense: Optional[int] = None
    special_attack: Optional[int] = None
    special_defense: Optional[int] = None
    speed: Optional[int] = None

    # Skills learned by this instance, including current PP
    skills: List[PokemonSkill] = field(default_factory=list) # Changed type hint
    status_effects: List[StatusEffectInstance] = field(default_factory=list) # Active status effects
    volatile_status: List[VolatileStatusInstance] = field(default_factory=list) # Active temporary battle statuses

    # Active status effects on this pokemon instance
    status_effect: Optional[StatusEffectInstance] = None

    # Individual Values (IVs) - hidden stats (0-31)
    individual_values: Dict[str, int] = field(default_factory=lambda: {
        "hp": random.randint(0, 31),
        "attack": random.randint(0, 31),
        "defense": random.randint(0, 31),
        "special_attack": random.randint(0, 31),
        "special_defense": random.randint(0, 31),
        "speed": random.randint(0, 31),
    })

    # Effort Values (EVs) - gained from defeating other pokemon (max 252 per stat, 510 total)
    effort_values: Dict[str, int] = field(default_factory=lambda: {
        "hp": 0, "attack": 0, "defense": 0,
        "special_attack": 0, "special_defense": 0, "speed": 0,
    })

    # Nature - affects stat growth (simplified for now)
    nature_id: Optional[int] = None # ID of the nature

    # Ability - passive effect (simplified for now)
    ability_id: Optional[int] = None # ID of the ability

    # Race data - will be loaded and attached by service/repository
    race: Optional[Race] = field(default=None, repr=False) # Exclude from repr for cleaner debug output

    # Battle-specific temporary data (not saved to DB)
    stat_stages: Dict[str, int] = field(default_factory=lambda: {
        "attack": 0, "defense": 0, "special_attack": 0,
        "special_defense": 0, "speed": 0, "accuracy": 0, "evasion": 0
    })
    # Other temporary battle states like volatile status effects, etc.

    # Sleep and freeze turns
    sleep_turns: int = field(default=0)
    freeze_turns: int = field(default=0)

    # New attributes
    major_status = None  # 主要状态效果（如中毒、灼伤等）
    volatile_statuses = []  # 易变状态效果列表（如混乱、畏缩等）

    # 新增：战斗中的能力等级
    # 键: "attack", "defense", "special_attack", "special_defense", "speed", "accuracy", "evasion"
    # 值: 整数，范围通常是 -6 到 +6
    battle_stat_stages: Dict[str, int] = field(default_factory=lambda: {
        "attack": 0,
        "defense": 0,
        "special_attack": 0,
        "special_defense": 0,
        "speed": 0,
        "accuracy": 0,  # 命中率等级
        "evasion": 0    # 闪避率等级
    })
    
    # 标记是否在战斗中，用于决定某些效果是否适用或如何清除
    in_battle: bool = False 

    def __post_init__(self):
        """Post-initialization to set current_hp to max_hp if not set."""
        if self.current_hp <= 0 and self.max_hp is not None:
            self.current_hp = self.max_hp
        
        # 确保 battle_stat_stages 总是初始化
        if not self.battle_stat_stages:
            self.battle_stat_stages = {
                "attack": 0, "defense": 0, "special_attack": 0,
                "special_defense": 0, "speed": 0, "accuracy": 0, "evasion": 0
            }

    def is_fainted(self) -> bool:
        """Checks if the pokemon has fainted."""
        return self.current_hp is not None and self.current_hp <= 0

    def heal(self, amount: int) -> int:
        """Heals the pokemon by a specific amount, not exceeding max HP."""
        if self.current_hp is None or self.max_hp is None:
             logger.warning(f"Attempted to heal {self.nickname} but HP data is incomplete.")
             return 0 # Cannot heal if HP data is missing

        old_hp = self.current_hp
        self.current_hp = min(self.current_hp + amount, self.max_hp)
        healed_amount = self.current_hp - old_hp
        logger.debug(f"Healed {self.nickname} by {healed_amount}. Current HP: {self.current_hp}/{self.max_hp}")
        return healed_amount

    def heal_percentage(self, percentage: float) -> int:
        """Heals the pokemon by a percentage of max HP."""
        if self.max_hp is None:
             logger.warning(f"Attempted to heal {self.nickname} by percentage but max HP is missing.")
             return 0 # Cannot heal if max HP is missing

        heal_amount = math.ceil(self.max_hp * percentage)
        return self.heal(heal_amount)

    def take_damage(self, amount: int) -> int:
        """Applies damage to the pokemon."""
        if self.current_hp is None:
             logger.warning(f"Attempted to damage {self.nickname} but current HP is missing.")
             return 0 # Cannot take damage if current HP is missing

        old_hp = self.current_hp
        self.current_hp = max(0, self.current_hp - amount)
        damage_taken = old_hp - self.current_hp
        logger.debug(f"{self.nickname} took {damage_taken} damage. Current HP: {self.current_hp}/{self.max_hp}")
        return damage_taken

    def apply_status_effect(self, status_effect: StatusEffect) -> List[str]:
        """
        应用状态效果到宝可梦身上，根据状态类型处理互斥规则。
        
        状态效果规则：
        - 主要状态（睡眠、中毒、麻痹、烧伤、冰冻等）一次只能有一个
        - 次要状态（混乱、着迷等）可以与主要状态共存
        - 某些特定状态效果可能有特殊互斥规则
        
        Args:
            status_effect: 要应用的状态效果
            
        Returns:
            包含操作结果消息的列表
        """
        messages: List[str] = []
        
        # 检查状态效果类型
        if status_effect.effect_type == "primary":
            # 主要状态效果：移除所有现有的主要状态
            removed_effects = []
            for se in self.status_effects[:]:
                if se.effect_type == "primary":
                    removed_effects.append(se.name)
                    self.status_effects.remove(se)
            
            if removed_effects:
                effect_names = "、".join(removed_effects)
                messages.append(f"{self.nickname} 的 {effect_names} 状态解除了。")
            
            # 添加新的主要状态
            self.status_effects.append(status_effect)
            messages.append(f"{self.nickname} 进入了 {status_effect.name} 状态！")
            logger.debug(f"Applied primary status effect {status_effect.name} to {self.nickname}.")
        
        elif status_effect.effect_type == "secondary":
            # 次要状态效果：检查是否已有相同的状态效果
            if any(se.status_id == status_effect.status_id for se in self.status_effects):
                messages.append(f"{self.nickname} 已经处于 {status_effect.name} 状态。")
                logger.debug(f"{self.nickname} already has secondary status effect {status_effect.name}.")
            else:
                # 检查互斥的次要状态
                incompatible_statuses = status_effect.incompatible_with if hasattr(status_effect, 'incompatible_with') else []
                for se in self.status_effects[:]:
                    if se.status_id in incompatible_statuses:
                        messages.append(f"{self.nickname} 的 {se.name} 状态被解除了。")
                        self.status_effects.remove(se)
                
                # 添加新的次要状态
                self.status_effects.append(status_effect)
                messages.append(f"{self.nickname} 进入了 {status_effect.name} 状态！")
                logger.debug(f"Applied secondary status effect {status_effect.name} to {self.nickname}.")
        
        else:
            # 其他类型状态效果（如场地效果、天气效果等）
            if any(se.status_id == status_effect.status_id for se in self.status_effects):
                messages.append(f"{self.nickname} 已经处于 {status_effect.name} 状态。")
                logger.debug(f"{self.nickname} already has status effect {status_effect.name}.")
            else:
                self.status_effects.append(status_effect)
                messages.append(f"{self.nickname} 获得了 {status_effect.name} 效果！")
                logger.debug(f"Applied status effect {status_effect.name} to {self.nickname}.")
        
        return messages

    def remove_status_effect(self, status_id: int) -> List[str]:
        """
        移除特定ID的状态效果。
        
        Args:
            status_id: 要移除的状态效果ID
            
        Returns:
            包含操作结果消息的列表
        """
        messages: List[str] = []
        removed_effect = None
        
        # 寻找并移除状态效果
        for se in self.status_effects[:]:
            if se.status_id == status_id:
                removed_effect = se
                self.status_effects.remove(se)
                break
                
        if removed_effect:
            messages.append(f"{self.nickname} 的 {removed_effect.name} 状态解除了。")
            logger.debug(f"Removed status effect {removed_effect.name} from {self.nickname}.")
        else:
            logger.debug(f"Attempted to remove status effect with ID {status_id} from {self.nickname}, but it was not found.")
        
        return messages

    def apply_stat_stage_change(self, stat_type: str, stages: int, event_publisher: Callable[[BattleEvent], None]):
        """
        Applies a change to a specific stat stage.
        Publishes a StatStageChangeEvent.
        """
        if stat_type not in self.stat_stages:
            logger.warning(f"Attempted to change invalid stat stage type: {stat_type}")
            return # Do nothing for invalid stat types

        current_stage = self.stat_stages[stat_type]
        new_stage = current_stage + stages

        # Cap stages between MIN_STAT_STAGE and MAX_STAT_STAGE
        new_stage = max(MIN_STAT_STAGE, min(MAX_STAT_STAGE, new_stage))

        stages_actually_changed = new_stage - current_stage

        if stages_actually_changed == 0:
            message = f"{self.nickname} 的 {stat_type} 没有变化。"
            logger.debug(message)
            # Still publish event even if no change, to signal the attempt
            event_publisher(StatStageChangeEvent(
                pokemon=self,
                stat_type=stat_type,
                stages_changed=0,
                new_stage=new_stage,
                message=message
            ))
            return # No change, no message needed

        self.stat_stages[stat_type] = new_stage

        # Generate message based on change
        if stages_actually_changed > 0:
            message = f"{self.nickname} 的 {stat_type} 提升了 {abs(stages_actually_changed)} 级！"
        else:
            message = f"{self.nickname} 的 {stat_type} 降低了 {abs(stages_actually_changed)} 级！"

        logger.debug(f"Stat stage change: {self.nickname}'s {stat_type} changed by {stages_actually_changed} to {new_stage}. Message: {message}")

        # Publish the event
        event_publisher(StatStageChangeEvent(
            pokemon=self,
            stat_type=stat_type,
            stages_changed=stages_actually_changed,
            new_stage=new_stage,
            message=message
        ))

    def get_modified_stat(self, stat_type: str) -> Optional[int]:
        """Calculates the effective stat value considering stat stages."""
        if self.race is None:
             logger.warning(f"Cannot calculate modified stat for {self.nickname}: Race data missing.")
             return None

        base_stat = getattr(self, stat_type, None) # Get calculated stat (attack, defense, etc.)
        if base_stat is None:
             logger.warning(f"Cannot calculate modified stat for {self.nickname}: Unknown stat type {stat_type}.")
             return None

        stage = self.stat_stages.get(stat_type, 0)
        modifier = calculate_stat_stage_modifier(stage)

        # Apply modifier (multiplicative for attack, defense, sp_attack, sp_defense, speed)
        # Accuracy and Evasion stages are handled differently in hit calculation
        if stat_type in ["attack", "defense", "special_attack", "special_defense", "speed"]:
             return math.floor(base_stat * modifier)
        # For accuracy and evasion, the stage is used directly in hit calculation, not to modify the stat value itself
        # Return the base stat for these, or handle them in the hit calculation logic
        return base_stat # Or raise an error/return None if this method shouldn't be called for accuracy/evasion

    async def add_exp(self, amount: int, metadata_repo: 'MetadataRepository') -> Tuple[List[str], List[Union[PokemonLeveledUpEvent, PokemonLearnedSkillEvent, SkillReplacementRequiredEvent]]]:
        """
        为宝可梦添加经验值，处理升级和学习技能。
        
        Args:
            amount (int): 要添加的经验值
            metadata_repo (MetadataRepository): 元数据仓库，用于获取宝可梦种族数据和技能数据
            
        Returns:
            Tuple[List[str], List[Union[PokemonLeveledUpEvent, PokemonLearnedSkillEvent, SkillReplacementRequiredEvent]]]:
                一个元组，包含消息列表和事件列表
        """
        messages: List[str] = []
        events: List[Union[PokemonLeveledUpEvent, PokemonLearnedSkillEvent, SkillReplacementRequiredEvent]] = []

        # 确保 race_data 已加载
        if not self.race:
             # 尝试从 metadata_repo 加载 race_data
             if metadata_repo:
                 self.race = await metadata_repo.get_race_by_id(self.race_id)
                 if not self.race:
                     logger.error(f"Race data not found for Pokemon instance {self.instance_id} with race_id {self.race_id}")
                     return messages, events # 无法处理，返回空列表
             else:
                 logger.error(f"MetadataRepository not provided to add_exp for Pokemon instance {self.instance_id}")
                 return messages, events # 无法处理，返回空列表

        # 1. Add experience
        self.experience += amount
        logger.debug(f"{self.nickname} gained {amount} EXP. Total EXP: {self.experience}")
        messages.append(f"{self.nickname} 获得了 {amount} 点经验值。")

        # 2. Check for level up
        leveled_up = False
        while self.level < 100 and self.experience >= calculate_exp_needed(self.level + 1, self.race.growth_rate):
            self.experience -= calculate_exp_needed(self.level + 1, self.race.growth_rate) # Deduct EXP for the current level
            self.level += 1
            leveled_up = True
            messages.append(f"{self.nickname} 升到了等级 {self.level}！")
            logger.info(f"{self.nickname} (Instance ID: {self.instance_id}) leveled up to {self.level}.")
            events.append(PokemonLeveledUpEvent(
                pokemon_instance_id=self.instance_id,
                pokemon_name=self.nickname or self.race.name,
                new_level=self.level,
                message=f"{self.nickname} 升到了等级 {self.level}！"
            ))

            # 3. Check for learnable skills at the new level
            # Use race_data to find skills learned at this level
            learnable_skills_at_level = self.race.get_learnable_skills_at_level(self.level) # 假设 Race 模型有这个方法

            current_skill_ids = {skill.skill_id for skill in self.skills}

            for skill_id in learnable_skills_at_level:
                if skill_id not in current_skill_ids:
                    # Try to learn the skill
                    skill_to_learn_obj = await metadata_repo.get_skill_by_id(skill_id)
                    if skill_to_learn_obj:
                        if len(self.skills) < 4: # 假设最多4个技能
                            self.skills.append(skill_to_learn_obj)
                            message = f"{self.nickname} 学会了 {skill_to_learn_obj.name}！"
                            messages.append(message)
                            logger.info(message)
                            events.append(PokemonLearnedSkillEvent(
                                pokemon_instance_id=self.instance_id,
                                skill_id=skill_to_learn_obj.skill_id,
                                skill_name=skill_to_learn_obj.name,
                                message=message
                            ))
                        else:
                            # 当技能已满时的处理
                            message = f"{self.nickname} 想学习 {skill_to_learn_obj.name}，但是已经学会了4个技能。需要替换一个技能吗？"
                            messages.append(message)
                            logger.warning(f"{self.nickname} tried to learn skill {skill_id} but already knows 4 skills. Triggering replacement event.")
                            events.append(SkillReplacementRequiredEvent(
                                pokemon_instance_id=self.instance_id,
                                pokemon_name=self.nickname or self.race.name,
                                new_skill_id=skill_id,
                                new_skill_name=skill_to_learn_obj.name,
                                current_skills=[s.to_dict() for s in self.skills],  # 提供当前技能信息以供选择
                                message=message
                            ))
                            # 触发替换事件后，宝可梦模型不应该自己替换技能，而是等待服务层或命令层的用户输入。
                            # 所以这里不修改 self.skills

            else:
                # Not enough EXP for the next level yet
                break # Exit the while loop

        # 如果没有升级，但仍未满级，记录还需要多少经验
        if not leveled_up and self.level < 100:
             logger.debug(f"{self.nickname} 还需要 {calculate_exp_needed(self.level + 1, self.race.growth_rate) - self.experience} 点经验升级。")

        # 返回消息和事件列表
        return messages, events

    def use_skill_pp(self, skill_id: int, amount: int = 1) -> bool:
        """Decreases the PP of a specific skill."""
        for pokemon_skill in self.skills:
            if pokemon_skill.skill_id == skill_id:
                if pokemon_skill.current_pp >= amount:
                    pokemon_skill.current_pp -= amount
                    logger.debug(f"{self.nickname} used skill {skill_id}. Remaining PP: {pokemon_skill.current_pp}")
                    return True
                else:
                    logger.debug(f"{self.nickname} tried to use skill {skill_id} but not enough PP.")
                    return False # Not enough PP
        logger.warning(f"{self.nickname} tried to use skill {skill_id} but it's not in their moveset.")
        return False # Skill not found in moveset

    def get_skill_pp(self, skill_id: int) -> Optional[int]:
        """Gets the current PP of a specific skill."""
        for pokemon_skill in self.skills:
            if pokemon_skill.skill_id == skill_id:
                return pokemon_skill.current_pp
        return None # Skill not found

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Pokemon instance to a dictionary."""
        return {
            "pokemon_id": self.pokemon_id,
            "instance_id": self.instance_id,
            "race_id": self.race_id,
            "owner_id": self.owner_id,
            "nickname": self.nickname,
            "level": self.level,
            "current_hp": self.current_hp,
            "experience": self.experience,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "special_attack": self.special_attack,
            "special_defense": self.special_defense,
            "speed": self.speed,
            "skills": [skill.to_dict() for skill in self.skills],
            "status_effects": [status.to_dict() for status in self.status_effects],
            "volatile_status": [status.to_dict() for status in self.volatile_status],
            "battle_stat_stages": self.battle_stat_stages,
            "is_fainted": self.is_fainted,
            "last_used_skill_id": self.last_used_skill_id,
            "is_in_battle": self.is_in_battle,
            "is_in_storage": self.is_in_storage,
            "ivs": self.ivs,
            "evs": self.evs,
            "nature": self.nature,
            "gender": self.gender,
            "shiny": self.shiny,
            "friendship": self.friendship,
            "held_item_id": self.held_item_id,
            "catch_date": self.catch_date.isoformat() if self.catch_date else None,
            "met_location": self.met_location,
            "met_level": self.met_level,
            "pokerus_status": self.pokerus_status,
            "ability_id": self.ability_id,
            "form_id": self.form_id,
            "tera_type_id": self.tera_type_id,
            "is_tera": self.is_tera,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pokemon":
        """Deserializes a Pokemon instance from a dictionary."""
        # Handle date deserialization
        catch_date_str = data.get("catch_date")
        catch_date = datetime.datetime.fromisoformat(catch_date_str) if catch_date_str else None

        pokemon = cls(
            pokemon_id=data.get("pokemon_id"),
            instance_id=data.get("instance_id", str(uuid.uuid4())),
            race_id=data["race_id"],
            owner_id=data.get("owner_id"),
            nickname=data["nickname"],
            level=data.get("level", 1),
            current_hp=data.get("current_hp"),
            experience=data.get("experience", 0),
            max_hp=data.get("max_hp"),
            attack=data.get("attack"),
            defense=data.get("defense"),
            special_attack=data.get("special_attack"),
            special_defense=data.get("special_defense"),
            speed=data.get("speed"),
            skills=[PokemonSkill.from_dict(s) for s in data.get("skills", [])],
            status_effects=[StatusEffectInstance.from_dict(se) for se in data.get("status_effects", [])],
            volatile_status=[VolatileStatusInstance.from_dict(vs) for vs in data.get("volatile_status", [])],
            battle_stat_stages=data.get("battle_stat_stages", cls.get_default_battle_stat_stages()),
            is_fainted=data.get("is_fainted", False),
            last_used_skill_id=data.get("last_used_skill_id"),
            is_in_battle=data.get("is_in_battle", False),
            is_in_storage=data.get("is_in_storage", False),
            ivs=data.get("ivs", {stat: random.randint(0, 31) for stat in ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]}),
            evs=data.get("evs", {stat: 0 for stat in ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]}),
            nature=data.get("nature", "Hardy"), # Default to a neutral nature
            gender=data.get("gender", "Male"), # Default gender
            shiny=data.get("shiny", False),
            friendship=data.get("friendship", 70), # Default friendship
            held_item_id=data.get("held_item_id"),
            catch_date=catch_date,
            met_location=data.get("met_location"),
            met_level=data.get("met_level"),
            pokerus_status=data.get("pokerus_status", 0), # 0: none, 1: infected, 2: cured
            ability_id=data.get("ability_id"),
            form_id=data.get("form_id"),
            tera_type_id=data.get("tera_type_id"),
            is_tera=data.get("is_tera", False),
        )
        # Ensure current_hp is set, defaulting to max_hp if not provided or if None after calculation
        if pokemon.max_hp is not None and pokemon.current_hp is None:
            pokemon.current_hp = pokemon.max_hp
        if pokemon.current_hp is not None and pokemon.max_hp is not None: # Ensure current_hp doesn't exceed max_hp
            pokemon.current_hp = min(pokemon.current_hp, pokemon.max_hp)
        return pokemon

    def remove_volatile_status(self, logic_key: str) -> bool:
        """
        移除指定的易变状态效果。
        
        Args:
            logic_key: 要移除的状态效果的逻辑键
            
        Returns:
            如果成功移除状态效果则返回True，否则返回False
        """
        for status in self.volatile_statuses[:]:
            if status.effect_logic_key == logic_key:
                self.volatile_statuses.remove(status)
                return True
        return False
        
    def has_volatile_status(self, logic_key: str) -> bool:
        """
        检查宝可梦是否具有指定的易变状态效果。
        
        Args:
            logic_key: 要检查的状态效果的逻辑键
            
        Returns:
            如果宝可梦具有该状态效果则返回True，否则返回False
        """
        return any(status.effect_logic_key == logic_key for status in self.volatile_statuses)

    def get_stat(self, stat_name: str) -> int:
        """
        获取宝可梦的特定属性值，考虑战斗中的等级修正。
        
        Args:
            stat_name: 属性名称 ('hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed', 'accuracy', 'evasion')
            
        Returns:
            计算后的属性值
        """
        if stat_name == 'hp':
            return self.max_hp
        
        # 检查属性是否存在
        if not hasattr(self, stat_name):
            logger.warning(f"Attempted to get unknown stat '{stat_name}' for {self.nickname}")
            return 0
        
        # 获取基础属性值
        base_value = getattr(self, stat_name)
        
        # 如果不在战斗中，返回基础值
        if not self.in_battle:
            return base_value
        
        # 在战斗中考虑能力等级修正
        if stat_name in self.battle_stat_stages:
            stage = self.battle_stat_stages[stat_name]
            multiplier = 1.0
            
            # 根据能力等级计算修正系数
            if stage > 0:
                multiplier = (2 + stage) / 2
            elif stage < 0:
                multiplier = 2 / (2 - stage)
            
            return int(base_value * multiplier)
        else:
            return base_value

    def recalculate_stats(self) -> None:
        """
        重新计算宝可梦的所有属性值，基于当前等级、种族值、个体值和努力值。
        在进化或等级提升时需要调用此方法。
        """
        if not self.race:
            logger.warning(f"Cannot recalculate stats for {self.nickname}: race data not available")
            return
        
        # 计算HP
        if hasattr(self.race, 'base_hp'):
            base_hp = self.race.base_hp
            self.max_hp = math.floor(((2 * base_hp + self.iv_hp + (self.ev_hp // 4)) * self.level) // 100 + self.level + 10)
            # 确保当前HP不超过最大HP
            if self.current_hp > self.max_hp:
                self.current_hp = self.max_hp
            
        # 计算其他属性
        for stat in ['attack', 'defense', 'special_attack', 'special_defense', 'speed']:
            base_value = getattr(self.race, f'base_{stat}', 0)
            iv_value = getattr(self, f'iv_{stat}', 0)
            ev_value = getattr(self, f'ev_{stat}', 0)
            
            # 获取属性修正系数（根据性格）
            nature_modifier = 1.0
            if hasattr(self, 'nature') and self.nature:
                if stat == self.nature.increased_stat:
                    nature_modifier = 1.1
                elif stat == self.nature.decreased_stat:
                    nature_modifier = 0.9
                
            # 计算属性值
            value = math.floor((((2 * base_value + iv_value + (ev_value // 4)) * self.level) // 100 + 5) * nature_modifier)
            setattr(self, stat, value)
            
        logger.debug(f"Recalculated stats for {self.nickname} at level {self.level}")

    def reset_battle_stats(self):
        """重置战斗相关的临时状态，例如能力等级。"""
        self.battle_stat_stages = {
            "attack": 0, "defense": 0, "special_attack": 0,
            "special_defense": 0, "speed": 0, "accuracy": 0, "evasion": 0
        }
        # 也可以在这里清除一些仅战斗中有效的状态效果
        # self.status_effects = [se for se in self.status_effects if not se.battle_only]
        logger.debug(f"宝可梦 {self.nickname} (ID: {self.pokemon_id}) 的战斗能力等级已重置。")

    def has_status_effect(self, status_id: int) -> bool:
        """Checks if the pokemon has a specific status effect."""
        return any(se.status_id == status_id for se in self.status_effects)

    async def replace_skill(self, old_skill_id: int, new_skill_id: int, metadata_repo: 'MetadataRepository') -> Tuple[bool, str]:
        """
        替换宝可梦的一个技能。
        
        Args:
            old_skill_id (int): 要替换的旧技能ID
            new_skill_id (int): 要学习的新技能ID
            metadata_repo (MetadataRepository): 元数据仓库，用于获取新技能的详细信息
            
        Returns:
            Tuple[bool, str]: 一个元组，包含操作是否成功的布尔值和描述结果的消息
        """
        # 验证旧技能是否存在于宝可梦的技能列表中
        old_skill_index = None
        old_skill = None
        for i, skill in enumerate(self.skills):
            if skill.skill_id == old_skill_id:
                old_skill_index = i
                old_skill = skill
                break
                
        if old_skill_index is None:
            return False, f"{self.nickname or self.race.name} 没有ID为 {old_skill_id} 的技能，无法替换。"
            
        # 从元数据仓库获取新技能信息
        new_skill_data = await metadata_repo.get_skill_by_id(new_skill_id)
        if not new_skill_data:
            return False, f"无法找到ID为 {new_skill_id} 的技能数据，替换失败。"
            
        # 执行技能替换
        old_skill_name = old_skill.name
        self.skills[old_skill_index] = new_skill_data
        
        logger.info(f"{self.nickname or self.race.name} 忘记了 {old_skill_name}，学会了 {new_skill_data.name}！")
        return True, f"{self.nickname or self.race.name} 忘记了 {old_skill_name}，学会了 {new_skill_data.name}！"

    def clear_all_status_effects(self) -> List[str]:
        """
        清除宝可梦身上的所有状态效果。
        
        Returns:
            包含操作结果消息的列表
        """
        messages: List[str] = []
        
        if not self.status_effects:
            messages.append(f"{self.nickname} 没有任何状态效果。")
            return messages
        
        effect_names = [se.name for se in self.status_effects]
        self.status_effects = []
        
        if effect_names:
            status_text = "、".join(effect_names)
            messages.append(f"{self.nickname} 的所有状态效果 ({status_text}) 已清除。")
            logger.debug(f"Cleared all status effects from {self.nickname}.")
        
        return messages

    def restore_pp(self, skill_index: Optional[int] = None, amount: Optional[int] = None) -> List[str]:
        """
        恢复宝可梦技能的PP值。
        
        Args:
            skill_index: 要恢复的技能索引，None表示恢复所有技能
            amount: 要恢复的PP值，None表示完全恢复
            
        Returns:
            包含操作结果消息的列表
        """
        messages: List[str] = []
        
        if not self.skills:
            messages.append(f"{self.nickname} 没有任何技能。")
            return messages
        
        if skill_index is not None:
            # 恢复特定技能的PP
            if 0 <= skill_index < len(self.skills):
                skill = self.skills[skill_index]
                old_pp = skill.current_pp
                
                if amount is None:
                    skill.current_pp = skill.max_pp
                else:
                    skill.current_pp = min(skill.current_pp + amount, skill.max_pp)
                    
                pp_restored = skill.current_pp - old_pp
                
                if pp_restored > 0:
                    messages.append(f"{self.nickname} 的技能 {skill.name} 恢复了 {pp_restored} 点PP。")
                    logger.debug(f"Restored {pp_restored} PP for {self.nickname}'s skill {skill.name}")
                else:
                    messages.append(f"{self.nickname} 的技能 {skill.name} 的PP已满。")
            else:
                messages.append(f"技能索引 {skill_index} 超出范围。")
        else:
            # 恢复所有技能的PP
            pp_restored = False
            
            for skill in self.skills:
                old_pp = skill.current_pp
                
                if amount is None:
                    skill.current_pp = skill.max_pp
                else:
                    skill.current_pp = min(skill.current_pp + amount, skill.max_pp)
                    
                if skill.current_pp > old_pp:
                    pp_restored = True
                    
            if pp_restored:
                messages.append(f"{self.nickname} 的所有技能PP已恢复。")
                logger.debug(f"Restored PP for all skills of {self.nickname}")
            else:
                messages.append(f"{self.nickname} 的所有技能PP已满。")
            
        return messages

# Assuming calculate_stats and calculate_exp_needed are defined elsewhere and imported
# from .formulas import calculate_exp_needed # Import calculate_exp_needed
# from .battle_logic import calculate_stats # Import calculate_stats
