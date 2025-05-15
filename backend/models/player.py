from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import datetime
# Assuming Pokemon and Item models will be defined
# from .pokemon import Pokemon
# from .item import Item

@dataclass
class Player:
    """
    玩家数据模型。
    对应数据库中的 player_records, player_repository, player_party,
    player_quest_progress, player_achievements, friends 表。
    这是一个聚合模型，包含了玩家在 game_record.db 中的所有相关数据。
    """
    player_id: int
    location_id: Optional[int] = None # 位置ID
    last_login_time: Optional[datetime.datetime] = None # 最后登录时间
    money: int = 0 # 金钱

    # 玩家拥有的道具 (item_id -> quantity)
    items: Dict[int, int] = field(default_factory=dict)

    # 玩家仓库中的宝可梦ID列表
    repository_pet_ids: List[int] = field(default_factory=list)

    # 玩家队伍中的宝可梦ID列表
    party_pet_ids: List[int] = field(default_factory=list)

    # 玩家任务进度 (task_id -> status)
    quest_progress: Dict[int, str] = field(default_factory=dict)

    # 玩家成就 (achievement_id -> unlock_date)
    achievements: Dict[int, datetime.datetime] = field(default_factory=dict)

    # 好友列表 (friend_id -> friendship_level)
    friends: Dict[int, int] = field(default_factory=dict)

    # 玩家队伍中的宝可梦ID列表
    party_pokemon_ids: List[int] = field(default_factory=list)

    # 玩家背包中的宝可梦ID列表
    box_pokemon_ids: List[int] = field(default_factory=list)

    # S2 refinement: Temporarily store encountered wild pokemon details
    # This is a simple in-memory storage. For a distributed system,
    # this might need to be stored in the database or a cache.
    encountered_wild_pokemon: Optional[Dict[str, Any]] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Player object to a dictionary."""
        return {
            "player_id": self.player_id,
            "location_id": self.location_id,
            "last_login_time": self.last_login_time.isoformat() if self.last_login_time else None,
            "money": self.money,
            "items": self.items,
            "repository_pet_ids": self.repository_pet_ids,
            "party_pet_ids": self.party_pet_ids,
            "quest_progress": self.quest_progress,
            "achievements": {
                ach_id: date.isoformat() for ach_id, date in self.achievements.items()
            },
            "friends": self.friends,
            "party_pokemon_ids": self.party_pokemon_ids,
            "box_pokemon_ids": self.box_pokemon_ids,
            "encountered_wild_pokemon": self.encountered_wild_pokemon,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Player":
        """Creates a Player object from a dictionary."""
        return Player(
            player_id=data["player_id"],
            location_id=data.get("location_id"),
            last_login_time=datetime.datetime.fromisoformat(data["last_login_time"]) if data.get("last_login_time") else None,
            money=data.get("money", 0),
            items=data.get("items", {}),
            repository_pet_ids=data.get("repository_pet_ids", []),
            party_pet_ids=data.get("party_pet_ids", []),
            quest_progress=data.get("quest_progress", {}),
            achievements={
                int(ach_id): datetime.datetime.fromisoformat(date_str) for ach_id, date_str in data.get("achievements", {}).items()
            },
            friends=data.get("friends", {}),
            party_pokemon_ids=data.get("party_pokemon_ids", []),
            box_pokemon_ids=data.get("box_pokemon_ids", []),
            encountered_wild_pokemon=data.get("encountered_wild_pokemon"),
        )

    # Add methods for managing items, pets, quests, etc.
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
