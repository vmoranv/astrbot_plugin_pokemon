from typing import List, Dict, Any, Optional, Callable
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
        """Applies a status effect to the pokemon."""
        messages: List[str] = []
        # Check if pokemon is already affected by this status or an incompatible one
        # TODO: Implement proper status effect application logic (S2 refinement)
        # For now, a simple check if status type is already present
        if any(se.status_id == status_effect.status_id for se in self.status_effects):
             messages.append(f"{self.nickname} 已经处于 {status_effect.name} 状态。")
             logger.debug(f"{self.nickname} already has status effect {status_effect.name}.")
        else:
             self.status_effects.append(status_effect)
             messages.append(f"{self.nickname} 进入了 {status_effect.name} 状态！")
             logger.debug(f"Applied status effect {status_effect.name} to {self.nickname}.")
        return messages

    def remove_status_effect(self, status_id: int) -> List[str]:
        """Removes a status effect by its ID."""
        messages: List[str] = []
        original_count = len(self.status_effects)
        self.status_effects = [se for se in self.status_effects if se.status_id != status_id]
        if len(self.status_effects) < original_count:
             # Need metadata to get status name
             # Assuming status effect metadata is available or can be fetched
             # For now, just use ID
             messages.append(f"{self.nickname} 的状态 {status_id} 解除了。")
             logger.debug(f"Removed status effect with ID {status_id} from {self.nickname}.")
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

    def add_exp(self, exp_gained: int, metadata_repo) -> List[str]:
        """Adds experience points and handles level ups."""
        messages: List[str] = []
        if self.race is None:
             logger.warning(f"Cannot add EXP to {self.nickname}: Race data missing.")
             return messages

        self.experience += exp_gained
        messages.append(f"{self.nickname} 获得了 {exp_gained} 点经验值！")

        # Check for level up
        while True:
            exp_needed_for_next_level = calculate_exp_needed(self.level + 1, self.race.growth_rate)
            if self.experience >= exp_needed_for_next_level:
                self.level += 1
                messages.append(f"{self.nickname} 升级了！现在是 {self.level} 级！")

                # Recalculate stats on level up
                calculate_stats(self, self.race, metadata_repo) # Pass metadata_repo for nature/attribute data
                messages.append(f"{self.nickname} 的能力值提高了！")

                # Check for new skills learned by level up
                if self.race and self.race.learnable_skills:
                    newly_learned_skills = [
                        ls for ls in self.race.learnable_skills
                        if ls.level == self.level
                    ]
                    for learnable_skill in newly_learned_skills:
                        skill_id = learnable_skill.skill_id
                        # Check if the pokemon already knows this skill
                        if not any(ps.skill_id == skill_id for ps in self.skills): # Check against PokemonSkill list
                            if len(self.skills) < 4:
                                # Learn the new skill
                                skill_data = metadata_repo.get_skill_by_id(skill_id)
                                if skill_data:
                                     # Add the new skill with its max PP
                                     self.skills.append(PokemonSkill(skill_id=skill_id, current_pp=skill_data.pp)) # Add as PokemonSkill
                                     messages.append(f"{self.nickname} 学会了 {skill_data.name}！")
                                else:
                                     messages.warning(f"Skill data not found for ID {skill_id} when {self.nickname} leveled up.")
                            else:
                                # TODO: Implement skill replacement logic (S3 refinement)
                                # For now, just inform the player they couldn't learn it
                                skill_data = metadata_repo.get_skill_by_id(skill_id)
                                if skill_data:
                                     messages.append(f"{self.nickname} 想学习 {skill_data.name}，但是已经学会了4个技能。")
                                else:
                                     messages.append(f"{self.nickname} 想学习新技能 (ID: {skill_id})，但是已经学会了4个技能。")
                                logger.warning(f"{self.nickname} tried to learn skill {skill_id} but already knows 4 skills. Skill replacement not implemented.")

            else:
                # Not enough EXP for the next level yet
                break # Exit the while loop

        return messages

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
        Returns the current value of a specific stat.
        
        Args:
            stat_name: The name of the stat to retrieve.
            
        Returns:
            The current value of the specified stat.
        """
        if stat_name in self.battle_stat_stages:
            return self.battle_stat_stages[stat_name]
        else:
            logger.warning(f"Unknown stat: {stat_name}")
            return 0

    def recalculate_stats(self):
        """
        Recalculates the stats of the Pokemon based on its current level, race, and IVs/EVs.
        """
        if self.race is None:
            logger.warning(f"Cannot recalculate stats for {self.nickname}: Race data missing.")
            return

        calculate_stats(self, self.race, None) # Pass None for metadata_repo

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

# Assuming calculate_stats and calculate_exp_needed are defined elsewhere and imported
# from .formulas import calculate_exp_needed # Import calculate_exp_needed
# from .battle_logic import calculate_stats # Import calculate_stats
