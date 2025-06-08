from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class PetSystemData:
    """
    宠物系统数据模型。
    对应数据库中的 pet_system_data 表。
    """
    system_id: int
    system_name: str
    system_description: Optional[str] = None
    system_effect: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the PetSystemData object to a dictionary."""
        return {
            "system_id": self.system_id,
            "system_name": self.system_name,
            "system_description": self.system_description,
            "system_effect": self.system_effect,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PetSystemData":
        """Creates a PetSystemData object from a dictionary."""
        return PetSystemData(
            system_id=data["system_id"],
            system_name=data["system_name"],
            system_description=data.get("system_description"),
            system_effect=data.get("system_effect"),
        )

# 如果 PetSystemData 需要 to_dict 或 from_dict 方法，也请添加类型提示
# def to_dict(self) -> Dict[str, Any]:
#     pass
# @staticmethod
# def from_dict(data: Dict[str, Any]) -> "PetSystemData":
#     pass 