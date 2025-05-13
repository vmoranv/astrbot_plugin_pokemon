from typing import List, Dict, Any
# Assuming Pokemon and Item models will be defined
# from .pokemon import Pokemon
# from .item import Item

class Player:
    """Represents a player in the game."""
    def __init__(self,
                 player_id: str,
                 name: str,
                 location_id: str,
                 money: int = 0,
                 inventory: Dict[int, int] = None, # {item_id: quantity}
                 pokemon_party: List[int] = None, # List of pokemon instance IDs
                 pokemon_box: List[int] = None,   # List of pokemon instance IDs
                 tasks: Dict[int, Any] = None,    # {task_id: progress}
                 achievements: List[int] = None   # List of achievement IDs
                ):
        self.player_id = player_id
        self.name = name
        self.location_id = location_id
        self.money = money
        self.inventory = inventory if inventory is not None else {}
        self.pokemon_party = pokemon_party if pokemon_party is not None else []
        self.pokemon_box = pokemon_box if pokemon_box is not None else []
        self.tasks = tasks if tasks is not None else {}
        self.achievements = achievements if achievements is not None else []

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Player object to a dictionary."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "location_id": self.location_id,
            "money": self.money,
            "inventory": self.inventory,
            "pokemon_party": self.pokemon_party,
            "pokemon_box": self.pokemon_box,
            "tasks": self.tasks,
            "achievements": self.achievements,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Player":
        """Creates a Player object from a dictionary."""
        return Player(
            player_id=data["player_id"],
            name=data["name"],
            location_id=data["location_id"],
            money=data.get("money", 0),
            inventory=data.get("inventory", {}),
            pokemon_party=data.get("pokemon_party", []),
            pokemon_box=data.get("pokemon_box", []),
            tasks=data.get("tasks", {}),
            achievements=data.get("achievements", []),
        )

    # Add methods for inventory management, party management, etc.
    # def add_item(self, item_id: int, quantity: int = 1):
    #     self.inventory[item_id] = self.inventory.get(item_id, 0) + quantity

    # def remove_item(self, item_id: int, quantity: int = 1):
    #     if self.inventory.get(item_id, 0) < quantity:
    #         raise InsufficientItemException(f"Not enough item {item_id}")
    #     self.inventory[item_id] -= quantity
    #     if self.inventory[item_id] <= 0:
    #         del self.inventory[item_id]

    # def add_pokemon_to_box(self, pokemon_instance_id: int):
    #     self.pokemon_box.append(pokemon_instance_id)

    # def add_pokemon_to_party(self, pokemon_instance_id: int):
    #     if len(self.pokemon_party) >= 6: # Example party limit
    #          # Handle full party case
    #          pass
    #     self.pokemon_party.append(pokemon_instance_id)
