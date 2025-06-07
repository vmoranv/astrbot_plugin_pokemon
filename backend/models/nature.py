from dataclasses import dataclass
from typing import Optional

@dataclass
class Nature:
    """宝可梦性格模型"""
    nature_id: int
    name: str
    increased_stat: Optional[str] = None  # 提升的能力值
    decreased_stat: Optional[str] = None  # 降低的能力值
    description: Optional[str] = None
    
    def get_stat_modifier(self, stat: str) -> float:
        """
        获取特定能力值的性格修正系数
        
        Args:
            stat: 能力值名称
            
        Returns:
            修正系数（1.1为提升，0.9为降低，1.0为无影响）
        """
        if stat == self.increased_stat:
            return 1.1
        elif stat == self.decreased_stat:
            return 0.9
        else:
            return 1.0
