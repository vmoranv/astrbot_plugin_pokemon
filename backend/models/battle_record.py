from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import datetime

@dataclass
class BattleRecord:
    """
    战斗记录数据模型。
    对应数据库中的 battle_records 表。
    """
    battle_id: int
    player1_id: int
    player2_id: int
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    winner_id: Optional[int] = None
    preload_effect_id: Optional[int] = None # 预加载特效ID
    skill_target_id: Optional[int] = None # 技能目标ID
    skill_id: Optional[int] = None # 技能ID
    status_effect_id: Optional[int] = None # 状态效果ID
    field_effect_id: Optional[int] = None # 场地效果ID
    item_id: Optional[int] = None # 道具ID

    def to_dict(self) -> Dict[str, Any]:
        """Converts the BattleRecord object to a dictionary."""
        return {
            "battle_id": self.battle_id,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "winner_id": self.winner_id,
            "preload_effect_id": self.preload_effect_id,
            "skill_target_id": self.skill_target_id,
            "skill_id": self.skill_id,
            "status_effect_id": self.status_effect_id,
            "field_effect_id": self.field_effect_id,
            "item_id": self.item_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "BattleRecord":
        """Creates a BattleRecord object from a dictionary."""
        return BattleRecord(
            battle_id=data["battle_id"],
            player1_id=data["player1_id"],
            player2_id=data["player2_id"],
            start_time=datetime.datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            winner_id=data.get("winner_id"),
            preload_effect_id=data.get("preload_effect_id"),
            skill_target_id=data.get("skill_target_id"),
            skill_id=data.get("skill_id"),
            status_effect_id=data.get("status_effect_id"),
            field_effect_id=data.get("field_effect_id"),
            item_id=data.get("item_id"),
        )

    # Add methods for battle logic if needed 