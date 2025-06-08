import csv
from typing import Dict, Any, List, Optional
from backend.models.skill import Skill, SecondaryEffect
from backend.models.attribute import Attribute
from backend.models.race import Race, LearnableSkill
from backend.models.item import Item
from backend.models.ability import Ability
from backend.models.status_effect import StatusEffect # Import StatusEffect model
from backend.models.field_effect import FieldEffect
from backend.models.pokemon import Pokemon
from backend.utils.logger import get_logger
import os
import pandas as pd
import aiosqlite
import json

logger = get_logger(__name__)

# Define the base data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# --- Data Loading Functions ---

async def load_skills(file_path: str = os.path.join(DATA_DIR, 'skills.csv')) -> Dict[int, Skill]:
    """Loads skill data from a CSV file."""
    skills: Dict[int, Skill] = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert relevant fields to correct types
                skill_id = int(row['skill_id'])
                skill_type = int(row['type']) # Assuming type is stored as ID
                power = int(row['power']) if row['power'] else None
                accuracy = int(row['accuracy']) if row['accuracy'] else None
                critical_rate = int(row['critical_rate']) if row['critical_rate'] else None
                pp = int(row['pp']) if row['pp'] else 0
                priority = int(row['priority']) if row['priority'] else 0
                effect_chance = int(row['effect_chance']) if row.get('effect_chance') else None
                critical_hit_ratio = int(row['critical_hit_ratio']) if row.get('critical_hit_ratio') else 1

                # Load secondary effects if available
                secondary_effects_data = json.loads(row['secondary_effects']) if row.get('secondary_effects') else []

                skills[skill_id] = Skill(
                    skill_id=skill_id,
                    name=row['name'],
                    skill_type=skill_type,
                    power=power,
                    accuracy=accuracy,
                    critical_rate=critical_rate,
                    pp=pp,
                    category=row['category'],
                    priority=priority,
                    target_type=row['target_type'],
                    effect_logic_key=row.get('effect_logic_key'),
                    description=row.get('description'),
                    effect_chance=effect_chance,
                    critical_hit_ratio=critical_hit_ratio,
                    secondary_effects=[SecondaryEffect(**se_data) for se_data in secondary_effects_data]
                )
        logger.info(f"Loaded {len(skills)} skills.")
    except FileNotFoundError:
        logger.error(f"Skills CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading skills: {e}")
    return skills

async def load_attributes(file_path: str = os.path.join(DATA_DIR, 'attributes.csv')) -> Dict[int, Attribute]:
    """Loads attribute (type) data from a CSV file."""
    attributes: Dict[int, Attribute] = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                attribute_id = int(row['attribute_id'])
                attributes[attribute_id] = Attribute(
                    attribute_id=attribute_id,
                    attribute_name=row['attribute_name'],
                    attacking_id=int(row['attacking_id']) if row['attacking_id'] else None,
                    defending_id=int(row['defending_id']) if row['defending_id'] else None,
                    super_effective_id=int(row['super_effective_id']) if row['super_effective_id'] else None,
                    none_effective_id=int(row['none_effective_id']) if row['none_effective_id'] else None,
                )
        logger.info(f"Loaded {len(attributes)} attributes.")
    except FileNotFoundError:
        logger.error(f"Attributes CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading attributes: {e}")
    return attributes

async def load_races(file_path: str = os.path.join(DATA_DIR, 'races.csv')) -> Dict[int, Race]:
    """Loads pokemon race data from a CSV file."""
    races: Dict[int, Race] = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                race_id = int(row['race_id'])
                types = [int(t) for t in row['types'].split(',') if t] if row.get('types') else []
                learnable_skills_data = json.loads(row['learnable_skills']) if row.get('learnable_skills') else []

                races[race_id] = Race(
                    race_id=race_id,
                    name=row['name'],
                    types=types,
                    base_hp=int(row['base_hp']),
                    base_attack=int(row['base_attack']),
                    base_defense=int(row['base_defense']),
                    base_special_attack=int(row['base_special_attack']),
                    base_special_defense=int(row['base_special_defense']),
                    base_speed=int(row['base_speed']),
                    catch_rate=int(row['catch_rate']),
                    base_experience=int(row['base_experience']),
                    growth_rate=row['growth_rate'],
                    learnable_skills=[LearnableSkill(**ls_data) for ls_data in learnable_skills_data],
                    abilities=[int(a) for a in row['abilities'].split(',') if a] if row.get('abilities') else [], # Load ability IDs
                    held_item_id=int(row['held_item_id']) if row.get('held_item_id') else None, # Load held item ID
                )
        logger.info(f"Loaded {len(races)} races.")
    except FileNotFoundError:
        logger.error(f"Races CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading races: {e}")
    return races

async def load_items(file_path: str = os.path.join(DATA_DIR, 'items.csv')) -> Dict[int, Item]:
    """Loads item data from a CSV file."""
    items: Dict[int, Item] = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                item_id = int(row['item_id'])
                status_immunities = [s.strip() for s in row['status_immunities'].split(',') if s.strip()] if row.get('status_immunities') else []
                items[item_id] = Item(
                    item_id=item_id,
                    name=row['item_name'],
                    description=row.get('description'),
                    status_immunities=status_immunities,
                    item_type=row.get('item_type', 'consumable'),  # 道具类型：消耗品、装备等
                    price=int(row.get('price', 0)),  # 商店价格
                    effect_type=row.get('effect_type'),  # 效果类型
                    effect_value=int(row.get('effect_value', 0)),  # 效果值（如回复量）
                    target_type=row.get('target_type', 'single'),  # 目标类型：单体、全体
                    battle_only=row.get('battle_only', '0') == '1',  # 是否仅战斗中使用
                    is_key_item=row.get('is_key_item', '0') == '1',  # 是否为关键道具
                    can_be_sold=row.get('can_be_sold', '1') == '1',  # 是否可出售
                    use_effect=row.get('use_effect'),  # 使用效果
                    sprite_name=row.get('sprite_name')  # 精灵图名称
                )
        logger.info(f"Loaded {len(items)} items.")
    except FileNotFoundError:
        logger.error(f"Items CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading items: {e}")
    return items

async def load_abilities(file_path: str = os.path.join(DATA_DIR, 'abilities.csv')) -> Dict[int, Ability]:
    """Loads ability data from a CSV file."""
    abilities: Dict[int, Ability] = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ability_id = int(row['ability_id'])
                status_immunities = [s.strip() for s in row['status_immunities'].split(',') if s.strip()] if row.get('status_immunities') else []
                abilities[ability_id] = Ability(
                    ability_id=ability_id,
                    name=row['ability_name'],
                    description=row.get('description'),
                    status_immunities=status_immunities,
                    trigger_condition=row.get('trigger_condition'),  # 触发条件：被攻击时、行动前等
                    trigger_chance=float(row.get('trigger_chance', 100)) / 100.0,  # 触发概率
                    effect_type=row.get('effect_type'),  # 效果类型
                    effect_value=int(row.get('effect_value', 0)),  # 效果值
                    is_passive=row.get('is_passive', '1') == '1',  # 是否为被动能力
                    priority=int(row.get('priority', 0)),  # 触发优先级
                    can_be_nullified=row.get('can_be_nullified', '1') == '1',  # 是否可被无效化
                    is_hidden=row.get('is_hidden', '0') == '1'  # 是否为隐藏特性
                )
        logger.info(f"Loaded {len(abilities)} abilities.")
    except FileNotFoundError:
        logger.error(f"Abilities CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading abilities: {e}")
    return abilities

async def load_status_effects(file_path: str = os.path.join(DATA_DIR, 'status_effects.csv')) -> Dict[int, StatusEffect]:
    """Loads status effect data from a CSV file."""
    status_effects: Dict[int, StatusEffect] = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                status_id = int(row['status_id'])
                status_effects[status_id] = StatusEffect(
                    status_id=status_id,
                    name=row['name'],
                    effect_type=row['effect_type'],
                    logic_key=row['logic_key'],
                    description=row.get('description'),
                    duration=int(row.get('duration', -1)),  # 持续回合数，-1表示直到战斗结束
                    is_volatile=row.get('is_volatile', '0') == '1',  # 是否为易失性状态（战斗后自动消失）
                    can_be_cured=row.get('can_be_cured', '1') == '1',  # 是否可被治愈
                    can_act=row.get('can_act', '1') == '1',  # 是否可以行动
                    effect_chance=float(row.get('effect_chance', 100)) / 100.0,  # 效果触发概率
                    stat_modifier=json.loads(row.get('stat_modifier', '{}')),  # 能力修正，JSON格式
                    damage_per_turn=int(row.get('damage_per_turn', 0)),  # 每回合伤害
                    heal_per_turn=int(row.get('heal_per_turn', 0)),  # 每回合恢复
                    cure_chance_per_turn=float(row.get('cure_chance_per_turn', 0)) / 100.0,  # 每回合自愈概率
                    animation_key=row.get('animation_key')  # 动画效果标识
                )
        logger.info(f"Loaded {len(status_effects)} status effects.")
    except FileNotFoundError:
        logger.error(f"Status effects CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading status effects: {e}")
    return status_effects

async def load_field_effects(file_path: str = os.path.join(DATA_DIR, 'field_effects.csv')) -> Dict[int, FieldEffect]:
    """加载场地效果数据（包括天气和地形）。"""
    field_effects: Dict[int, FieldEffect] = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                effect_id = int(row['effect_id'])
                affected_types = [int(t) for t in row['affected_types'].split(',') if t] if row.get('affected_types') else []
                stat_modifiers = json.loads(row.get('stat_modifiers', '{}'))
                
                field_effects[effect_id] = FieldEffect(
                    effect_id=effect_id,
                    name=row['name'],
                    effect_type=row['effect_type'],  # weather或terrain
                    description=row.get('description'),
                    duration=int(row.get('duration', 5)),  # 默认持续5回合
                    affected_types=affected_types,  # 受影响的宝可梦属性
                    damage_modifier=float(row.get('damage_modifier', 1.0)),  # 伤害修正
                    stat_modifiers=stat_modifiers,  # 能力修正，JSON格式
                    special_effect=row.get('special_effect'),  # 特殊效果，如冰冻概率提高
                    animation_key=row.get('animation_key'),  # 动画效果标识
                    is_natural=row.get('is_natural', '0') == '1',  # 是否为自然生成（非技能引起）
                    compatible_effects=[int(e) for e in row.get('compatible_effects', '').split(',') if e]  # 兼容的其他场地效果
                )
        logger.info(f"Loaded {len(field_effects)} field effects.")
    except FileNotFoundError:
        logger.error(f"Field effects CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading field effects: {e}")
    return field_effects

class MetadataRepository:
    """
    Repository for accessing game metadata loaded from data files.
    """
    def __init__(self):
        self._skills: Optional[Dict[int, Skill]] = None
        self._attributes: Optional[Dict[int, Attribute]] = None
        self._races: Optional[Dict[int, Race]] = None
        self._items: Optional[Dict[int, Item]] = None # Add items dictionary
        self._abilities: Optional[Dict[int, Ability]] = None # Add abilities dictionary
        self._status_effects: Optional[Dict[int, StatusEffect]] = None # Add status effects dictionary
        self._field_effects: Optional[Dict[int, FieldEffect]] = None # Add field effects dictionary
        self._pokemon_species_data: Optional[Dict[int, Dict[str, Any]]] = None
        self._pokemon_evolutions_data: Optional[List[Dict[str, Any]]] = None

    async def load_all(self):
        """Loads all metadata asynchronously."""
        logger.info("Loading all metadata...")
        self._skills = await load_skills()
        self._attributes = await load_attributes()
        self._races = await load_races()
        self._items = await load_items() # Load items
        self._abilities = await load_abilities() # Load abilities
        self._status_effects = await load_status_effects() # Load status effects
        self._field_effects = await load_field_effects() # Load field effects
        logger.info("All metadata loaded.")

    def get_skill(self, skill_id: int) -> Optional[Skill]:
        """Gets a skill by its ID."""
        return self._skills.get(skill_id) if self._skills else None

    def get_attribute(self, attribute_id: int) -> Optional[Attribute]:
        """Gets an attribute (type) by its ID."""
        return self._attributes.get(attribute_id) if self._attributes else None

    def get_race(self, race_id: int) -> Optional[Race]:
        """Gets a pokemon race by its ID."""
        return self._races.get(race_id) if self._races else None

    def get_item(self, item_id: int) -> Optional[Item]:
        """Gets an item by its ID."""
        return self._items.get(item_id) if self._items else None

    def get_ability(self, ability_id: int) -> Optional[Ability]:
        """Gets an ability by its ID."""
        return self._abilities.get(ability_id) if self._abilities else None

    def get_status_effect(self, status_id: int) -> Optional[StatusEffect]:
        """Gets a status effect by its ID."""
        return self._status_effects.get(status_id) if self._status_effects else None

    def get_status_effect_by_logic_key(self, logic_key: str) -> Optional[StatusEffect]:
        """Gets a status effect by its logic key."""
        if self._status_effects:
            for status_effect in self._status_effects.values():
                if status_effect.effect_logic_key == logic_key:
                    return status_effect
        return None

    def get_field_effect(self, effect_id: int) -> Optional[FieldEffect]:
        """Gets a field effect (weather/terrain) by its ID."""
        return self._field_effects.get(effect_id) if self._field_effects else None

    def check_status_immunity_by_ability_or_item(self, pokemon: Pokemon, status_logic_key: str) -> bool:
        """
        Checks if a Pokemon is immune to a status effect based on its ability or held item.
        """
        # Check ability immunity
        if pokemon.ability_id:
            ability = self.get_ability(pokemon.ability_id)
            if ability and status_logic_key in ability.status_immunities:
                logger.debug(f"Pokemon {pokemon.nickname} is immune to {status_logic_key} due to ability {ability.name}.")
                return True

        # Check held item immunity
        if pokemon.held_item_id:
            item = self.get_item(pokemon.held_item_id)
            if item and status_logic_key in item.status_immunities:
                 logger.debug(f"Pokemon {pokemon.nickname} is immune to {status_logic_key} due to held item {item.name}.")
                 return True

        return False

    async def get_pokemon_species_by_id(self, race_id: int) -> Optional[Dict[str, Any]]:
        """获取指定 race_id 的宝可梦种族数据"""
        if not self._pokemon_species_data:
            await self.load_pokemon_species()
        
        species_info = self._pokemon_species_data.get(race_id)
        if species_info:
            # 确保返回的是字典的副本，以防外部修改
            return dict(species_info)
        logger.warning(f"未找到 Race ID 为 {race_id} 的宝可梦种族数据。")
        return None

    async def get_evolution_data_for_pokemon(self, current_race_id: int) -> List[Dict[str, Any]]:
        """
        获取指定 current_race_id 的宝可梦所有可能的直接进化路径。
        """
        if not self._pokemon_evolutions_data:
            await self.load_pokemon_evolutions() # 确保进化数据已加载
        
        evolutions = []
        # self._pokemon_evolutions_data 应该是一个列表，每个元素是一个包含进化信息的字典
        # 例如: [{'evolution_id': 1, 'current_race_id': 1, 'evolved_race_id': 2, 'evolution_trigger': 'level_up', 'trigger_value': '16'}, ...]
        for evo_data in self._pokemon_evolutions_data:
            if evo_data.get("current_race_id") == current_race_id:
                evolutions.append(dict(evo_data)) # 返回副本
        
        if not evolutions:
            logger.debug(f"未找到 Race ID {current_race_id} 的进化数据。")
        return evolutions

    async def load_pokemon_evolutions(self):
        """从 CSV 加载宝可梦进化数据"""
        if self._pokemon_evolutions_data is None:
            self._pokemon_evolutions_data = []
            try:
                # 假设 CSV 文件名为 pokemon_evolutions.csv
                # 列: evolution_id,current_race_id,evolved_race_id,evolution_trigger,trigger_value,[other_conditions...]
                evolutions_df = await self._load_csv_data('pokemon_evolutions.csv')
                if evolutions_df is not None:
                    for _, row in evolutions_df.iterrows():
                        evo_dict = row.to_dict()
                        # 类型转换
                        for key in ['evolution_id', 'current_race_id', 'evolved_race_id']:
                            if key in evo_dict and pd.notna(evo_dict[key]):
                                try:
                                    evo_dict[key] = int(evo_dict[key])
                                except ValueError:
                                    logger.warning(f"在 pokemon_evolutions.csv 中，行 {_ + 2} 的 {key} 值 '{evo_dict[key]}' 不是有效整数。")
                                    # 根据需要决定是否跳过此行或使用默认值
                        
                        # trigger_value 可能不是数字 (例如道具名称)，所以保持为字符串，由 EvolutionHandler 解析
                        self._pokemon_evolutions_data.append(evo_dict)
                    logger.info(f"成功加载 {len(self._pokemon_evolutions_data)} 条宝可梦进化数据。")
                else:
                    logger.error("未能加载宝可梦进化数据 (pokemon_evolutions.csv 可能不存在或为空)。")
            except Exception as e:
                logger.error(f"加载宝可梦进化数据时出错: {e}", exc_info=True)
                self._pokemon_evolutions_data = [] # 出错时重置，避免使用部分加载的数据

    async def get_ability_by_id(self, ability_id: int) -> Optional[Ability]:
        """通过ID获取特性对象"""
        if not self._abilities:
            await self.load_abilities()
        
        ability_info = self._abilities.get(ability_id)
        if ability_info:
            # 假设 ability_info 是一个包含 Ability 模型所需所有字段的字典
            return Ability(**ability_info)
        logger.warning(f"未找到 ID 为 {ability_id} 的特性数据。")
        return None

    # TODO: Add methods to get all skills, races, etc. if needed (S30 refinement)

    async def get_skills_learnable_at_level(self, race_id: int, level: int) -> List[Dict[str, Any]]:
        """
        获取宝可梦种族在特定等级可学习的技能。
        
        Args:
            race_id: 宝可梦种族ID
            level: 等级
            
        Returns:
            List[Dict[str, Any]]: 可学习技能的列表
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT s.* 
                    FROM pokemon_skills ps
                    JOIN skills s ON ps.skill_id = s.skill_id
                    WHERE ps.race_id = ? AND ps.learn_level = ?
                    """,
                    (race_id, level)
                )
                
                skills = await cursor.fetchall()
                return [dict(skill) for skill in skills]
        except Exception as e:
            logger.error(f"获取可学习技能失败: {e}", exc_info=True)
            return []

    async def get_skills_learnable_until_level(self, race_id: int, max_level: int) -> List[Dict[str, Any]]:
        """
        获取宝可梦种族在指定等级之前（含）可学习的所有技能。
        
        Args:
            race_id: 宝可梦种族ID
            max_level: 最大等级
            
        Returns:
            List[Dict[str, Any]]: 可学习技能的列表
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT s.*, ps.learn_level 
                    FROM pokemon_skills ps
                    JOIN skills s ON ps.skill_id = s.skill_id
                    WHERE ps.race_id = ? AND ps.learn_level <= ?
                    ORDER BY ps.learn_level DESC
                    """,
                    (race_id, max_level)
                )
                
                skills = await cursor.fetchall()
                return [dict(skill) for skill in skills]
        except Exception as e:
            logger.error(f"获取可学习技能失败: {e}", exc_info=True)
            return []

    async def get_pokemons_by_location(self, location_id: str) -> List[Dict[str, Any]]:
        """
        获取特定位置可遇到的宝可梦列表。
        
        Args:
            location_id: 位置ID
            
        Returns:
            List[Dict[str, Any]]: 可遇到的宝可梦列表，包含遇到概率
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT p.*, l.encounter_rate 
                    FROM location_pokemons l
                    JOIN pokemon_races p ON l.race_id = p.race_id
                    WHERE l.location_id = ?
                    """,
                    (location_id,)
                )
                
                pokemons = await cursor.fetchall()
                return [dict(pokemon) for pokemon in pokemons]
        except Exception as e:
            logger.error(f"获取位置宝可梦列表失败: {e}", exc_info=True)
            return []

    async def get_all_skills(self) -> Dict[int, Skill]:
        """获取所有技能数据。"""
        if not self._skills:
            await self.load_skills()
        return self._skills

    async def get_all_races(self) -> Dict[int, Race]:
        """获取所有宝可梦种族数据。"""
        if not self._races:
            await self.load_races()
        return self._races

    async def get_all_items(self) -> Dict[int, Item]:
        """获取所有道具数据。"""
        if not self._items:
            await self.load_items()
        return self._items

    async def get_all_abilities(self) -> Dict[int, Ability]:
        """获取所有特性数据。"""
        if not self._abilities:
            await self.load_abilities()
        return self._abilities

    async def get_all_status_effects(self) -> Dict[int, StatusEffect]:
        """获取所有状态效果数据。"""
        if not self._status_effects:
            await self.load_status_effects()
        return self._status_effects

    async def get_all_field_effects(self) -> Dict[int, FieldEffect]:
        """获取所有场地效果数据（包括天气和地形）。"""
        if not self._field_effects:
            await self.load_field_effects()
        return self._field_effects

    async def get_evolutions_for_race(self, race_id: int) -> List[Dict[str, Any]]:
        """
        获取特定宝可梦种族的所有可能进化路径。
        
        Args:
            race_id: 宝可梦种族ID
            
        Returns:
            List[Dict[str, Any]]: 进化数据列表
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT * FROM pokemon_evolutions
                    WHERE base_race_id = ?
                    """,
                    (race_id,)
                )
                
                evolutions = await cursor.fetchall()
                return [dict(evolution) for evolution in evolutions]
        except Exception as e:
            logger.error(f"获取宝可梦进化数据失败: {e}", exc_info=True)
            return []