from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Achievement:
    """
    成就数据模型。
    对应数据库中的 achievements 表。
    """
    achievement_id: int
    name: str
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Achievement object to a dictionary."""
        return {
            "achievement_id": self.achievement_id,
            "name": self.name,
            "description": self.description,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Achievement":
        """Creates an Achievement object from a dictionary."""
        return Achievement(
            achievement_id=data["achievement_id"],
            name=data["name"],
            description=data.get("description"),
        )

# 如果 Achievement 需要 to_dict 或 from_dict 方法，也请添加类型提示
# def to_dict(self) -> Dict[str, Any]:
#     pass
# @staticmethod
# def from_dict(data: Dict[str, Any]) -> "Achievement":
#     pass 