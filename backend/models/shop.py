from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Shop:
    """
    商店数据模型。

    对应数据库中的 shops 表。存储了游戏中各种商店的信息，包括关联的 NPC 和出售的物品类型。

    属性:
        shop_id (int): 商店的唯一标识符。
        name (str): 商店的名称。
        shop_type (str): 商店的类型 ('item', 'skill_tm' 等)，决定商店出售的商品种类。
        npc_id (Optional[int]): 商店关联的 NPC ID，关联 npcs 表，如果没有关联 NPC 则为 None。
        item_id (Optional[int]): 如果是出售单一道具的商店，关联的道具 ID，关联 items 表，否则为 None。
    """
    shop_id: int
    name: str
    shop_type: str # 商店类型，例如 "item", "skill_tm"
    npc_id: Optional[int] = None # 商店关联的NPC ID
    item_id: Optional[int] = None # 如果是道具商店，关联的道具ID

    def to_dict(self) -> Dict[str, Any]:
        """
        将 Shop 对象转换为字典。

        返回:
            Dict[str, Any]: 包含商店数据的字典。
        """
        return {
            "shop_id": self.shop_id,
            "name": self.name,
            "npc_id": self.npc_id,
            "shop_type": self.shop_type,
            "item_id": self.item_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Shop":
        """
        从字典创建 Shop 对象。

        参数:
            data (Dict[str, Any]): 包含商店数据的字典。

        返回:
            Shop: 创建的 Shop 对象。
        """
        return Shop(
            shop_id=data["shop_id"],
            name=data["name"],
            shop_type=data["shop_type"],
            npc_id=data.get("npc_id"),
            item_id=data.get("item_id"),
        )

# 如果 Shop 需要 to_dict 或 from_dict 方法，也请添加类型提示
# def to_dict(self) -> Dict[str, Any]:
#     pass
# @staticmethod
# def from_dict(data: Dict[str, Any]) -> "Shop":
#     pass 