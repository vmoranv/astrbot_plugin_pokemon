from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class Map:
    """
    地图数据模型。
    对应数据库中的 maps 表。
    """
    map_id: int
    name: str
    description: Optional[str] = None
    encounter_rate: float = 0.0 # 遇敌率
    background_image_path: Optional[str] = None
    npc_id: Optional[int] = None # 地图上的NPC ID
    common_pet_id: Optional[int] = None # 普通宝可梦ID
    common_pet_rate: float = 0.0 # 普通宝可梦出现率
    rare_pet_id: Optional[int] = None # 稀有宝可梦ID
    rare_pet_rate: float = 0.0 # 稀有宝可梦出现率
    rare_pet_time: Optional[str] = None # 稀有宝可梦出现时间段，例如 "day", "night"
    adjacent_maps: List[int] = field(default_factory=list) # 新增：相邻地图ID列表

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Map object to a dictionary."""
        return {
            "map_id": self.map_id,
            "name": self.name,
            "description": self.description,
            "encounter_rate": self.encounter_rate,
            "background_image_path": self.background_image_path,
            "npc_id": self.npc_id,
            "common_pet_id": self.common_pet_id,
            "common_pet_rate": self.common_pet_rate,
            "rare_pet_id": self.rare_pet_id,
            "rare_pet_rate": self.rare_pet_rate,
            "rare_pet_time": self.rare_pet_time,
            "adjacent_maps": self.adjacent_maps, # 包含 adjacent_maps
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Map":
        """Creates a Map object from a dictionary."""
        return Map(
            map_id=data["map_id"],
            name=data["name"],
            description=data.get("description"),
            encounter_rate=data.get("encounter_rate", 0.0),
            background_image_path=data.get("background_image_path"),
            npc_id=data.get("npc_id"),
            common_pet_id=data.get("common_pet_id"),
            common_pet_rate=data.get("common_pet_rate", 0.0),
            rare_pet_id=data.get("rare_pet_id"),
            rare_pet_rate=data.get("rare_pet_rate", 0.0),
            rare_pet_time=data.get("rare_pet_time"),
            adjacent_maps=data.get("adjacent_maps", []), # 从字典获取 adjacent_maps，默认为空列表
        )

    # Add methods if needed, e.g., check_can_move_to
