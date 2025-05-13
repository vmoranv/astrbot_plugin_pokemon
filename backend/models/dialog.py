from typing import List, Dict, Any
from dataclasses import dataclass
from typing import Optional

@dataclass
class Dialog:
    """
    对话数据模型。
    对应数据库中的 dialogs 表。
    """
    dialog_id: int
    text: str
    next_dialog_id: Optional[int] = None # 下一个对话ID
    option1_text: Optional[str] = None # 选项1文本
    option1_next_dialog_id: Optional[int] = None # 选项1对应的下一个对话ID
    option2_text: Optional[str] = None # 选项2文本
    option2_next_dialog_id: Optional[int] = None # 选项2对应的下一个对话ID

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Dialog object to a dictionary."""
        return {
            "dialog_id": self.dialog_id,
            "text": self.text,
            "next_dialog_id": self.next_dialog_id,
            "option1_text": self.option1_text,
            "option1_next_dialog_id": self.option1_next_dialog_id,
            "option2_text": self.option2_text,
            "option2_next_dialog_id": self.option2_next_dialog_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Dialog":
        """Creates a Dialog object from a dictionary."""
        return Dialog(
            dialog_id=data["dialog_id"],
            text=data["text"],
            next_dialog_id=data.get("next_dialog_id"),
            option1_text=data.get("option1_text"),
            option1_next_dialog_id=data.get("option1_next_dialog_id"),
            option2_text=data.get("option2_text"),
            option2_next_dialog_id=data.get("option2_next_dialog_id"),
        )

    # Add methods if needed, e.g., filter_available_options
