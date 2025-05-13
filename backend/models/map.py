from typing import List, Dict, Any

class Map:
    """Represents a location or map in the game world."""
    def __init__(self,
                 map_id: str,
                 name: str,
                 description: str = "",
                 adjacent_maps: List[str] = None, # List of map_ids
                 encounter_pool: Dict[int, float] = None, # {race_id: encounter_chance}
                 npcs: List[int] = None, # List of NPC IDs
                 items: List[int] = None # List of item IDs found here
                ):
        self.map_id = map_id
        self.name = name
        self.description = description
        self.adjacent_maps = adjacent_maps if adjacent_maps is not None else []
        self.encounter_pool = encounter_pool if encounter_pool is not None else {}
        self.npcs = npcs if npcs is not None else []
        self.items = items if items is not None else []

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Map object to a dictionary."""
        return {
            "map_id": self.map_id,
            "name": self.name,
            "description": self.description,
            "adjacent_maps": self.adjacent_maps,
            "encounter_pool": self.encounter_pool,
            "npcs": self.npcs,
            "items": self.items,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Map":
        """Creates a Map object from a dictionary."""
        return Map(
            map_id=data["map_id"],
            name=data["name"],
            description=data.get("description", ""),
            adjacent_maps=data.get("adjacent_maps", []),
            encounter_pool=data.get("encounter_pool", {}),
            npcs=data.get("npcs", []),
            items=data.get("items", [])
        )

    # Add methods if needed, e.g., check_can_move_to
