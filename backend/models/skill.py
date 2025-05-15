from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TypedDict, List

# 定义一个 TypedDict 来描述从字典创建 Skill 对象时期望的字典结构
class SkillData(TypedDict):
    """
    用于从字典创建 Skill 对象时的数据结构。
    """
    skill_id: int
    name: str
    type: int
    category: str
    target_type: str
    power: Optional[int]
    accuracy: Optional[int]
    critical_rate: Optional[int]
    pp: int
    priority: int
    effect_logic_key: Optional[str]
    description: Optional[str]

@dataclass
class SecondaryEffect:
    """Represents a secondary effect of a skill."""
    effect_type: str # e.g., "status", "stat_change", "heal"
    target: str # "self", "target", "all_opponents", etc.
    chance: float # Chance of the effect occurring (0.0 to 1.0)
    # Effect details - structure depends on effect_type
    # For status: {"status_id": int}
    # For stat_change: {"stat": str, "stages": int}
    # For heal: {"heal_percentage": float} or {"heal_amount": int}
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Skill:
    """
    技能数据模型。

    对应数据库中的 skills 表。存储了游戏中所有技能的基本信息和效果关联。

    属性:
        skill_id (int): 技能的唯一标识符。
        name (str): 技能的名称。
        skill_type (str): 技能的属性ID，关联 attributes 表。
        category (str): 技能的分类 ('物理', '特殊', '变化')。
        target_type (str): 技能的目标类型 ('single', 'all_opponents', 'self' 等)。
        power (Optional[int]): 技能的威力，对于变化技能为 None。
        accuracy (Optional[int]): 技能的命中率 (0-100)，对于必中技能为 None。
        critical_rate (Optional[int]): 技能的额外暴击率 (0-100)，默认为 0。
        pp (Optional[int]): 技能的最大使用次数，默认为 0。
        priority (int): 技能的优先级，影响出招顺序，默认为 0。
        effect_logic_key (str): 关联核心逻辑中处理技能效果的键。
        description (str): 技能的详细描述。
    """
    skill_id: int
    name: str
    skill_type: str
    category: str
    target_type: str
    power: Optional[int] = None
    accuracy: Optional[int] = None
    critical_rate: Optional[int] = None
    pp: Optional[int] = None
    priority: Optional[int] = 0
    effect_logic_key: str = ""
    description: str = ""
    effect_chance: Optional[float] = None # Chance of applying a primary effect (e.g., status) - Note: Secondary effects have their own chance
    critical_hit_ratio: int = 1 # Critical hit ratio (1 for normal, 2 for high crit)
    secondary_effects: List[SecondaryEffect] = field(default_factory=list) # List of secondary effects

    def to_dict(self) -> Dict[str, Any]:
        """
        将 Skill 对象转换为字典。

        返回:
            Dict[str, Any]: 包含技能数据的字典。
        """
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "type": self.skill_type,
            "power": self.power,
            "accuracy": self.accuracy,
            "critical_rate": self.critical_rate,
            "pp": self.pp,
            "category": self.category,
            "priority": self.priority,
            "target_type": self.target_type,
            "effect_logic_key": self.effect_logic_key,
            "description": self.description,
            "effect_chance": self.effect_chance,
            "critical_hit_ratio": self.critical_hit_ratio,
            "secondary_effects": [se.__dict__ for se in self.secondary_effects], # Convert SecondaryEffect to dict
        }

    @staticmethod
    def from_dict(data: SkillData) -> "Skill": # 更新类型提示为 SkillData
        """
        从字典创建 Skill 对象。

        参数:
            data (SkillData): 包含技能数据的字典，应遵循 SkillData TypedDict 定义的结构。

        返回:
            Skill: 创建的 Skill 对象。
        """
        return Skill(
            skill_id=data["skill_id"],
            name=data["name"],
            skill_type=data["type"],
            power=data.get("power"),
            accuracy=data.get("accuracy"),
            critical_rate=data.get("critical_rate"),
            pp=data.get("pp", 0),
            category=data["category"],
            priority=data.get("priority", 0),
            target_type=data["target_type"],
            effect_logic_key=data.get("effect_logic_key", ""),
            description=data.get("description", ""),
            effect_chance=data.get("effect_chance"),
            critical_hit_ratio=data.get("critical_hit_ratio", 1),
            secondary_effects=[SecondaryEffect(**se_data) for se_data in data.get("secondary_effects", [])], # Load secondary effects
        ) 