from typing import List, Dict, Any
# Assuming Skill, StatusEffect, Race models will be defined
# from .skill import Skill
# from .status_effect import StatusEffect
# from ..core.battle import formulas # Example dependency for calculations
from dataclasses import dataclass
from typing import Optional
import datetime

@dataclass
class Pokemon:
    """
    宝可梦实例数据模型。
    对应数据库中的 pokemon_instances 表。
    """
    pet_id: int
    race_id: int
    nickname: Optional[str] = None
    level: int = 1
    exp: int = 0
    current_hp: int = 0
    max_hp: int = 0
    attack: int = 0
    defence: int = 0
    special_attack: int = 0
    special_defence: int = 0
    speed: int = 0
    nature_id: Optional[int] = None # 性格ID
    ability_id: Optional[int] = None # 能力ID
    caught_date: Optional[datetime.datetime] = None # 捕捉日期
    skill1_id: Optional[int] = None
    skill2_id: Optional[int] = None
    skill3_id: Optional[int] = None
    skill4_id: Optional[int] = None
    skill1_pp: int = 0
    skill2_pp: int = 0
    skill3_pp: int = 0
    skill4_pp: int = 0
    is_in_party: bool = False # 是否在队伍中

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Pokemon object to a dictionary."""
        return {
            "pet_id": self.pet_id,
            "race_id": self.race_id,
            "nickname": self.nickname,
            "level": self.level,
            "exp": self.exp,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defence": self.defence,
            "special_attack": self.special_attack,
            "special_defence": self.special_defence,
            "speed": self.speed,
            "nature_id": self.nature_id,
            "ability_id": self.ability_id,
            "caught_date": self.caught_date.isoformat() if self.caught_date else None,
            "skill1_id": self.skill1_id,
            "skill2_id": self.skill2_id,
            "skill3_id": self.skill3_id,
            "skill4_id": self.skill4_id,
            "skill1_pp": self.skill1_pp,
            "skill2_pp": self.skill2_pp,
            "skill3_pp": self.skill3_pp,
            "skill4_pp": self.skill4_pp,
            "is_in_party": self.is_in_party,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Pokemon":
        """Creates a Pokemon object from a dictionary."""
        return Pokemon(
            pet_id=data["pet_id"],
            race_id=data["race_id"],
            nickname=data.get("nickname"),
            level=data.get("level", 1),
            exp=data.get("exp", 0),
            current_hp=data.get("current_hp", 0),
            max_hp=data.get("max_hp", 0),
            attack=data.get("attack", 0),
            defence=data.get("defence", 0),
            special_attack=data.get("special_attack", 0),
            special_defence=data.get("special_defence", 0),
            speed=data.get("speed", 0),
            nature_id=data.get("nature_id"),
            ability_id=data.get("ability_id"),
            caught_date=datetime.datetime.fromisoformat(data["caught_date"]) if data.get("caught_date") else None,
            skill1_id=data.get("skill1_id"),
            skill2_id=data.get("skill2_id"),
            skill3_id=data.get("skill3_id"),
            skill4_id=data.get("skill4_id"),
            skill1_pp=data.get("skill1_pp", 0),
            skill2_pp=data.get("skill2_pp", 0),
            skill3_pp=data.get("skill3_pp", 0),
            skill4_pp=data.get("skill4_pp", 0),
            is_in_party=data.get("is_in_party", False),
        )

    # Add methods for battle calculations, leveling up, etc.
