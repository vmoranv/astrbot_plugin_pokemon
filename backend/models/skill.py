from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TypedDict

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
        ) 