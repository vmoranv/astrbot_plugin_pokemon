from typing import Dict, Any

class Item:
    """Represents an item in the game."""
    def __init__(self,
                 item_id: int,
                 name: str,
                 description: str = "",
                 item_type: str = "consumable", # e.g., "consumable", "equipment", "key_item", "pokeball"
                 value: int = 0, # Sell/buy value
                 effects: Dict[str, Any] = None # {effect_type: value} e.g., {"heal_hp": 50}
                ):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.item_type = item_type
        self.value = value
        self.effects = effects if effects is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Item object to a dictionary."""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type,
            "value": self.value,
            "effects": self.effects,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Item":
        """Creates an Item object from a dictionary."""
        return Item(
            item_id=data["item_id"],
            name=data["name"],
            description=data.get("description", ""),
            item_type=data.get("item_type", "consumable"),
            value=data.get("value", 0),
            effects=data.get("effects", {})
        )

    # Add methods if needed, e.g., apply_effect (might call core logic)
