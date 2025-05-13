from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Task:
    """
    任务数据模型。
    对应数据库中的 tasks 表。
    """
    task_id: int
    name: str
    description: Optional[str] = None
    reward_money: int = 0
    reward_item_id: Optional[int] = None # 奖励道具ID
    reward_item_quantity: int = 0
    prerequisite_task_id: Optional[int] = None # 前置任务ID
    start_dialog_id: Optional[int] = None # 任务开始对话ID
    completion_dialog_id: Optional[int] = None # 任务完成对话ID

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Task object to a dictionary."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "reward_money": self.reward_money,
            "reward_item_id": self.reward_item_id,
            "reward_item_quantity": self.reward_item_quantity,
            "prerequisite_task_id": self.prerequisite_task_id,
            "start_dialog_id": self.start_dialog_id,
            "completion_dialog_id": self.completion_dialog_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Task":
        """Creates a Task object from a dictionary."""
        return Task(
            task_id=data["task_id"],
            name=data["name"],
            description=data.get("description"),
            reward_money=data.get("reward_money", 0),
            reward_item_id=data.get("reward_item_id"),
            reward_item_quantity=data.get("reward_item_quantity", 0),
            prerequisite_task_id=data.get("prerequisite_task_id"),
            start_dialog_id=data.get("start_dialog_id"),
            completion_dialog_id=data.get("completion_dialog_id"),
        ) 