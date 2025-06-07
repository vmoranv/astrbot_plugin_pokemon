from typing import Dict, List, Optional, Any
import random
from backend.models.pokemon import Pokemon
from backend.models.race import Race
from backend.models.skill import Skill
from backend.utils.logger import get_logger
from backend.core.battle.formulas import calculate_stats

logger = get_logger(__name__)

class PokemonFactory:
    """宝可梦工厂类，负责创建各种宝可梦实例"""
    
    def __init__(self, metadata_repo=None):
        """
        初始化宝可梦工厂
        
        Args:
            metadata_repo: 元数据仓库，用于获取宝可梦种族、技能等数据
        """
        self.metadata_repo = metadata_repo
        
    async def create_wild_pokemon(self, race_id: int, level: int) -> Pokemon:
        """
        创建野生宝可梦实例
        
        Args:
            race_id: 宝可梦种族ID
            level: 宝可梦等级
            
        Returns:
            创建的宝可梦实例
        """
        # 获取种族数据
        race = await self.metadata_repo.get_pokemon_race(race_id)
        if not race:
            logger.error(f"无法找到种族ID: {race_id}")
            return None
            
        # 随机生成个体值 (IVs)
        ivs = {
            "hp": random.randint(0, 31),
            "attack": random.randint(0, 31),
            "defense": random.randint(0, 31),
            "sp_attack": random.randint(0, 31),
            "sp_defense": random.randint(0, 31),
            "speed": random.randint(0, 31)
        }
        
        # 随机选择性格
        natures = ["hardy", "lonely", "brave", "adamant", "naughty", "bold", "docile", "relaxed", "impish", "lax", 
                   "timid", "hasty", "serious", "jolly", "naive", "modest", "mild", "quiet", "bashful", "rash", 
                   "calm", "gentle", "sassy", "careful", "quirky"]
        nature = random.choice(natures)
        
        # 获取该种族此等级可学会的技能
        known_skills = await self.metadata_repo.get_skills_for_race_at_level(race_id, level)
        if not known_skills:
            logger.warning(f"种族ID {race_id} 在等级 {level} 没有可用技能")
            known_skills = []
        
        # 创建宝可梦实例
        pokemon = Pokemon(
            instance_id=None,  # 数据库将分配ID
            species_id=race_id,
            player_id=None,  # 野生宝可梦没有所属玩家
            nickname=None,
            level=level,
            experience=self._calculate_exp_for_level(level),
            ivs=ivs,
            evs={"hp": 0, "attack": 0, "defense": 0, "sp_attack": 0, "sp_defense": 0, "speed": 0},
            nature=nature,
            types=race.types,
            skills=[s.skill_id for s in known_skills[:4]],  # 最多4个技能
            current_hp=None,  # 稍后计算
            status_condition=None,
            friendship=70,  # 野生宝可梦的初始友好度
            catch_rate=race.catch_rate,
            is_shiny=random.random() < 0.0008,  # 闪光率约1/1250
            is_wild=True
        )
        
        # 计算能力值
        pokemon.stats = calculate_stats(pokemon, race)
        pokemon.current_hp = pokemon.stats["hp"]  # 野生宝可梦初始满HP
        
        return pokemon
    
    async def create_starter_pokemon(self, race_id: int, level: int = 5, nickname: str = None) -> Pokemon:
        """
        创建初始宝可梦实例
        
        Args:
            race_id: 宝可梦种族ID
            level: 宝可梦等级，默认为5
            nickname: 宝可梦昵称，默认为None
            
        Returns:
            创建的宝可梦实例
        """
        # 获取种族数据
        race = await self.metadata_repo.get_pokemon_race(race_id)
        if not race:
            logger.error(f"无法找到种族ID: {race_id}")
            return None
        
        # 初始宝可梦有较高的个体值
        ivs = {
            "hp": random.randint(20, 31),
            "attack": random.randint(20, 31),
            "defense": random.randint(20, 31),
            "sp_attack": random.randint(20, 31),
            "sp_defense": random.randint(20, 31),
            "speed": random.randint(20, 31)
        }
        
        # 获取该种族此等级可学会的技能
        known_skills = await self.metadata_repo.get_skills_for_race_at_level(race_id, level)
        if not known_skills:
            logger.warning(f"种族ID {race_id} 在等级 {level} 没有可用技能")
            known_skills = []
        
        # 创建宝可梦实例
        pokemon = Pokemon(
            instance_id=None,  # 数据库将分配ID
            species_id=race_id,
            player_id=None,  # 稍后分配
            nickname=nickname,
            level=level,
            experience=self._calculate_exp_for_level(level),
            ivs=ivs,
            evs={"hp": 0, "attack": 0, "defense": 0, "sp_attack": 0, "sp_defense": 0, "speed": 0},
            nature=random.choice(["hardy", "docile", "bashful", "quirky", "serious"]),  # 中性性格
            types=race.types,
            skills=[s.skill_id for s in known_skills],
            current_hp=None,  # 稍后计算
            status_condition=None,
            friendship=120,  # 初始宝可梦友好度较高
            catch_rate=race.catch_rate,
            is_shiny=random.random() < 0.001,  # 初始宝可梦闪光率更高
            is_wild=False
        )
        
        # 计算能力值
        pokemon.stats = calculate_stats(pokemon, race)
        pokemon.current_hp = pokemon.stats["hp"]  # 初始宝可梦满HP
        
        return pokemon
    
    def _calculate_exp_for_level(self, level: int) -> int:
        """
        计算指定等级所需的经验值
        
        Args:
            level: 宝可梦等级
            
        Returns:
            达到该等级所需的经验值
        """
        # 简化的经验计算公式，实际游戏中更复杂
        return level ** 3 

    async def create_pokemon(self, race_data: Race, level: int, moves: List[int] = None,
                             is_wild: bool = False, nickname: str = None,
                             original_trainer_id: str = None) -> Pokemon:
        """
        通用宝可梦创建方法
        
        Args:
            race_data: 宝可梦种族数据
            level: 等级
            moves: 指定技能ID列表
            is_wild: 是否为野生宝可梦
            nickname: 昵称
            original_trainer_id: 原始训练师ID
            
        Returns:
            创建的宝可梦实例
        """
        if is_wild:
            pokemon = await self.create_wild_pokemon(race_data.race_id, level)
        else:
            pokemon = await self.create_starter_pokemon(race_data.race_id, level, nickname)
        
        # 设置原始训练师
        if original_trainer_id:
            pokemon.original_trainer_id = original_trainer_id
        
        # 设置自定义技能
        if moves:
            pokemon.skills = moves[:4]  # 最多4个技能
        
        return pokemon 