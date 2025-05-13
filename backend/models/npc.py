from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class NPC:
    """
    表示游戏中的一个 NPC (非玩家角色)。
    """
    npc_id: str
    name: str
    description: str
    dialog_id: str # 关联的对话 ID

@dataclass
class Npc:
    """
    NPC 数据模型。

    对应数据库中的 npcs 表。存储了游戏中非玩家角色的信息，如商店老板、训练师等。

    属性:
        npc_id (int): NPC 的唯一标识符。
        name (str): NPC 的名称。
        interaction_type (str): NPC 的互动类型 ('dialog', 'battle', 'shop' 等)。
        pet_id (Optional[int]): NPC 可能携带的宝可梦ID，关联 pokemon 表，如果没有宝可梦则为 None。
        initial_dialog_id (Optional[int]): NPC 的初始对话ID，关联 dialogs 表，如果没有初始对话则为 None。
    """
    npc_id: int
    name: str
    interaction_type: str # 互动类型，例如 "dialog", "battle", "shop"
    pet_id: Optional[int] = None # NPC 可能携带的宝可梦ID
    initial_dialog_id: Optional[int] = None # 初始对话ID

    def to_dict(self) -> Dict[str, Any]:
        """
        将 Npc 对象转换为字典。

        返回:
            Dict[str, Any]: 包含 NPC 数据的字典。
        """
        return {
            "npc_id": self.npc_id,
            "pet_id": self.pet_id,
            "name": self.name,
            "interaction_type": self.interaction_type,
            "initial_dialog_id": self.initial_dialog_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Npc":
        """
        从字典创建 Npc 对象。

        参数:
            data (Dict[str, Any]): 包含 NPC 数据的字典。

        返回:
            Npc: 创建的 Npc 对象。
        """
        return Npc(
            npc_id=data["npc_id"],
            name=data["name"],
            interaction_type=data["interaction_type"],
            pet_id=data.get("pet_id"),
            initial_dialog_id=data.get("initial_dialog_id"),
        )

# 如果 Npc 需要 to_dict 或 from_dict 方法，也请添加类型提示
# def to_dict(self) -> Dict[str, Any]:
#     pass
# @staticmethod
# def from_dict(data: Dict[str, Any]) -> "Npc":
#     pass 