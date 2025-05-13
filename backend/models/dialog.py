from typing import List, Dict, Any

class Dialog:
    """Represents a piece of dialogue in the game."""
    def __init__(self,
                 dialog_id: int,
                 text: str,
                 options: List[Dict[str, Any]] = None, # List of {text: str, next_dialog_id: int, action: str}
                 requires_item: int = None, # Item ID required to see this dialog/option
                 requires_task_status: Dict[int, Any] = None # {task_id: required_status}
                ):
        self.dialog_id = dialog_id
        self.text = text
        self.options = options if options is not None else []
        self.requires_item = requires_item
        self.requires_task_status = requires_task_status if requires_task_status is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Dialog object to a dictionary."""
        return {
            "dialog_id": self.dialog_id,
            "text": self.text,
            "options": self.options,
            "requires_item": self.requires_item,
            "requires_task_status": self.requires_task_status,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Dialog":
        """Creates a Dialog object from a dictionary."""
        return Dialog(
            dialog_id=data["dialog_id"],
            text=data["text"],
            options=data.get("options", []),
            requires_item=data.get("requires_item"),
            requires_task_status=data.get("requires_task_status", {})
        )

    # Add methods if needed, e.g., filter_available_options
