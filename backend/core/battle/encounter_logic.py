import random
from typing import Optional, Tuple, List, Dict, Any
from backend.data_access.repositories.metadata_repository import MetadataRepository
from backend.utils.logger import get_logger
from backend.models.pokemon import Pokemon

logger = get_logger(__name__)

class EncounterLogic:
    """Core logic for determining wild pokemon encounters."""

    def __init__(self):
        self.metadata_repo = MetadataRepository()

    async def check_encounter(self, location_id: str) -> bool:
        """
        Determines if a wild pokemon encounter occurs at the given location.
        Probability is based on the location's base encounter chance.
        """
        location_data = await self.metadata_repo.get_location_data(location_id)
        if not location_data:
            logger.error(f"Location data not found for location_id: {location_id}")
            return False # Cannot have encounter if location data is missing

        base_chance = location_data.get('base_encounter_chance', 0.0) # Default to 0 if not specified

        encounter_chance = base_chance

        # Perform the random check
        return random.random() < encounter_chance

    async def get_wild_pokemon_details(self, location_id: str) -> Optional[Tuple[int, int]]:
        """
        If an encounter occurs, selects a random wild pokemon race and level
        based on the location's encounter data and weights.
        Returns a tuple of (pokemon_race_id, level) or None if no encounter data.
        """
        encounter_data = await self.metadata_repo.get_location_encounters(location_id)
        if not encounter_data:
            logger.warning(f"No encounter data found for location_id: {location_id}")
            return None # No pokemon to encounter

        # Calculate total weight
        total_weight = sum(item['weight'] for item in encounter_data)
        if total_weight <= 0:
            logger.warning(f"Total weight for encounters at location {location_id} is zero or negative.")
            return None # Cannot select if total weight is zero

        # Select a pokemon based on weights
        # Use random.choices for weighted selection (requires Python 3.6+)
        # If using older Python, implement manual weighted selection
        selected_encounter = random.choices(encounter_data, weights=[item['weight'] for item in encounter_data], k=1)[0]

        race_id = selected_encounter['pokemon_race_id']
        min_level = selected_encounter['min_level']
        max_level = selected_encounter['max_level']

        # Select a random level within the range
        # Ensure min_level <= max_level
        if min_level > max_level:
             logger.error(f"Invalid level range for race {race_id} at location {location_id}: min_level {min_level} > max_level {max_level}")
             # Fallback or raise error? Let's return None for now.
             return None

        level = random.randint(min_level, max_level)

        logger.debug(f"Selected wild pokemon race {race_id} at level {level} for location {location_id}")
        return (race_id, level)

    async def wild_pokemon_generator(self, location_id: str, player_level: int) -> Optional[Pokemon]:
        """
        根据位置和玩家等级生成野生宝可梦。
        
        Args:
            location_id: 位置ID
            player_level: 玩家等级
            
        Returns:
            Optional[Pokemon]: 生成的野生宝可梦，如果无法生成则返回None
        """
        try:
            # 获取该位置可遇到的宝可梦列表
            available_pokemons = await self.metadata_repo.get_pokemons_by_location(location_id)
            
            if not available_pokemons:
                logger.warning(f"位置 {location_id} 没有可遇到的宝可梦")
                return None
            
            # 根据稀有度权重选择宝可梦种族
            weights = [p.get("encounter_rate", 10) for p in available_pokemons]
            selected_pokemon_data = random.choices(available_pokemons, weights=weights, k=1)[0]
            
            # 计算宝可梦等级，基于玩家等级并添加随机波动
            min_level = max(1, player_level - 5)
            max_level = player_level + 2
            pokemon_level = random.randint(min_level, max_level)
            
            # 获取宝可梦种族数据
            race_id = selected_pokemon_data.get("race_id")
            race = await self.metadata_repo.get_pokemon_race(race_id)
            
            if not race:
                logger.error(f"无法获取宝可梦种族数据，race_id: {race_id}")
                return None
            
            # 创建随机个体值
            iv_hp = random.randint(0, 31)
            iv_attack = random.randint(0, 31)
            iv_defense = random.randint(0, 31)
            iv_special_attack = random.randint(0, 31)
            iv_special_defense = random.randint(0, 31)
            iv_speed = random.randint(0, 31)
            
            # 创建野生宝可梦实例
            wild_pokemon = Pokemon(
                instance_id=-1,  # 临时ID，如果捕获会分配正式ID
                race_id=race_id,
                race=race,
                nickname=race.name,  # 野生宝可梦的昵称默认为种族名称
                level=pokemon_level,
                exp=0,  # 野生宝可梦没有经验值
                iv_hp=iv_hp,
                iv_attack=iv_attack,
                iv_defense=iv_defense,
                iv_special_attack=iv_special_attack,
                iv_special_defense=iv_special_defense,
                iv_speed=iv_speed,
                # 其他属性使用默认值
            )
            
            # 计算属性值
            wild_pokemon.recalculate_stats()
            
            # 设置满HP
            wild_pokemon.current_hp = wild_pokemon.max_hp
            
            # 学习适合当前等级的技能
            await self._load_pokemon_skills(wild_pokemon)
            
            return wild_pokemon
            
        except Exception as e:
            logger.error(f"生成野生宝可梦时发生错误: {e}", exc_info=True)
            return None
        
    async def _load_pokemon_skills(self, pokemon: Pokemon) -> None:
        """
        加载宝可梦可学习的技能。
        
        Args:
            pokemon: 要加载技能的宝可梦
        """
        if not pokemon.race:
            logger.warning(f"无法加载技能：宝可梦 {pokemon.nickname} 缺少种族信息")
            return
        
        # 获取该宝可梦种族直到当前等级可学习的所有技能
        learnable_skills = await self.metadata_repo.get_skills_learnable_until_level(
            pokemon.race.race_id, pokemon.level
        )
        
        # 随机选择最多4个技能
        skills_to_learn = []
        if len(learnable_skills) <= 4:
            skills_to_learn = learnable_skills
        else:
            # 按技能学习等级倒序排列，优先选择高等级技能
            sorted_skills = sorted(learnable_skills, key=lambda s: s.get("learn_level", 0), reverse=True)
            skills_to_learn = sorted_skills[:4]
        
        # 加载技能对象
        pokemon.skills = []
        for skill_data in skills_to_learn:
            skill_id = skill_data.get("skill_id")
            skill = await self.metadata_repo.get_skill(skill_id)
            if skill:
                pokemon.skills.append(skill)

# Instantiate the logic class (or use a singleton pattern if preferred)
encounter_logic = EncounterLogic()
