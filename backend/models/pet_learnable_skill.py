from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class PetLearnableSkill:
    """
    宝可梦可学习技能数据模型。
    对应数据库中的 pet_learnable_skills 表。
    """
    race_id: int
    skill_id: int
    learn_method: str # 学习方式，例如 "level_up", "tm", "egg"
    learn_level: Optional[int] = None # 如果是升级学习，需要等级

    def to_dict(self) -> Dict[str, Any]:
        """Converts the PetLearnableSkill object to a dictionary."""
        return {
            "race_id": self.race_id,
            "skill_id": self.skill_id,
            "learn_method": self.learn_method,
            "learn_level": self.learn_level,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PetLearnableSkill":
        """Creates a PetLearnableSkill object from a dictionary."""
        return PetLearnableSkill(
            race_id=data["race_id"],
            skill_id=data["skill_id"],
            learn_method=data["learn_method"],
            learn_level=data.get("learn_level"),
        ) 