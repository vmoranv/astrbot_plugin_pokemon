from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Ability:
    """
    宝可梦特性数据模型。
    对应数据库中的 abilities 表。
    """
    ability_id: int
    name: str
    description: Optional[str] = None
    effect_type: Optional[str] = None  # 特性类型，例如 "battle_entry", "status_immunity", "weather"
    effect_trigger: Optional[str] = None  # 触发条件，例如 "on_entry", "on_hit", "on_status"
    effect_value: Optional[str] = None  # 特性效果值，可能是数值或其他数据

    def to_dict(self) -> Dict[str, Any]:
        """将特性对象转换为字典。"""
        return {
            "ability_id": self.ability_id,
            "name": self.name,
            "description": self.description,
            "effect_type": self.effect_type,
            "effect_trigger": self.effect_trigger,
            "effect_value": self.effect_value
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Ability":
        """从字典创建特性对象。"""
        return Ability(
            ability_id=data["ability_id"],
            name=data["name"],
            description=data.get("description"),
            effect_type=data.get("effect_type"),
            effect_trigger=data.get("effect_trigger"),
            effect_value=data.get("effect_value")
        ) 