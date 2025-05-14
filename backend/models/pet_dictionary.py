from pydantic import BaseModel, ConfigDict
from typing import Optional

class PetDictionary(BaseModel):
    """
    宝可梦字典数据模型。
    对应数据库中的 pet_dictionary 表。
    """
    race_id: int
    name: str
    evo_level: int
    evolution_stage: int
    base_hp: int
    base_attack: int
    base_defence: int
    base_special_attack: int
    base_special_defence: int
    base_speed: int
    catch_rate: int
    growth_rate: str
    attribute_id1: int
    attribute_id2: Optional[int] = None # 属性2可能为空
    height: float
    weight: float
    description: str

    model_config = ConfigDict(from_attributes=True)
