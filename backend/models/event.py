from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Event:
    """
    事件数据模型。
    对应数据库中的 events 表。
    """
    event_id: int
    name: str
    description: Optional[str] = None
    reward_item_id: Optional[int] = None # 奖励道具ID
    dialog_id: Optional[int] = None # 关联的对话ID
    pet_id: Optional[int] = None # 关联的宝可梦ID

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Event object to a dictionary."""
        return {
            "event_id": self.event_id,
            "name": self.name,
            "description": self.description,
            "reward_item_id": self.reward_item_id,
            "dialog_id": self.dialog_id,
            "pet_id": self.pet_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Event":
        """Creates an Event object from a dictionary."""
        return Event(
            event_id=data["event_id"],
            name=data["name"],
            description=data.get("description"),
            reward_item_id=data.get("reward_item_id"),
            dialog_id=data.get("dialog_id"),
            pet_id=data.get("pet_id"),
        )

# 如果 Event 需要 to_dict 或 from_dict 方法，也请添加类型提示
# def to_dict(self) -> Dict[str, Any]:
#     pass
# @staticmethod
# def from_dict(data: Dict[str, Any]) -> "Event":
#     pass 