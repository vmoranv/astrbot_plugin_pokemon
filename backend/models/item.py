from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Item:
    """
    道具数据模型。
    对应数据库中的 items 表。
    """
    item_id: int
    name: str
    description: Optional[str] = None
    effect_type: Optional[str] = None # 效果类型，例如 "heal", "boost", "pokeball"
    use_target: Optional[str] = None # 使用目标，例如 "self_pet", "opponent_pet", "wild_pet"
    use_effect: Optional[str] = None # 对应核心逻辑中的使用效果处理函数
    price: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Item object to a dictionary."""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "effect_type": self.effect_type,
            "use_target": self.use_target,
            "use_effect": self.use_effect,
            "price": self.price,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Item":
        """Creates an Item object from a dictionary."""
        return Item(
            item_id=data["item_id"],
            name=data["name"],
            description=data.get("description"),
            effect_type=data.get("effect_type"),
            use_target=data.get("use_target"),
            use_effect=data.get("use_effect"),
            price=data.get("price", 0)
        )

    # Add methods if needed, e.g., apply_effect (might call core logic)
