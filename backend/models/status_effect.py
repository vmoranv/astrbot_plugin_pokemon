from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class StatusEffect:
    """
    状态效果数据模型。
    对应数据库中的 status_effects 表。
    """
    status_effect_id: int
    name: str
    description: Optional[str] = None
    effect_logic_key: Optional[str] = None # 对应核心逻辑中的效果处理函数
    length: Optional[int] = None # 持续回合数或其他长度单位

    def to_dict(self) -> Dict[str, Any]:
        """Converts the StatusEffect object to a dictionary."""
        return {
            "status_effect_id": self.status_effect_id,
            "name": self.name,
            "description": self.description,
            "effect_logic_key": self.effect_logic_key,
            "length": self.length,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "StatusEffect":
        """Creates a StatusEffect object from a dictionary."""
        return StatusEffect(
            status_effect_id=data["status_effect_id"],
            name=data["name"],
            description=data.get("description"),
            effect_logic_key=data.get("effect_logic_key"),
            length=data.get("length"),
        ) 