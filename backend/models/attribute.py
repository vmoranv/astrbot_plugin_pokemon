from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Attribute:
    """
    属性数据模型。
    对应数据库中的 attributes 表。
    """
    attribute_id: int
    attribute_name: str
    # 假设这些是关联的属性ID，可能需要更复杂的结构来表示克制关系
    attacking_id: Optional[int] = None
    defending_id: Optional[int] = None
    super_effective_id: Optional[int] = None
    none_effective_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Attribute object to a dictionary."""
        return {
            "attribute_id": self.attribute_id,
            "attribute_name": self.attribute_name,
            "attacking_id": self.attacking_id,
            "defending_id": self.defending_id,
            "super_effective_id": self.super_effective_id,
            "none_effective_id": self.none_effective_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Attribute":
        """Creates an Attribute object from a dictionary."""
        return Attribute(
            attribute_id=data["attribute_id"],
            attribute_name=data["attribute_name"],
            attacking_id=data.get("attacking_id"),
            defending_id=data.get("defending_id"),
            super_effective_id=data.get("super_effective_id"),
            none_effective_id=data.get("none_effective_id"),
        ) 