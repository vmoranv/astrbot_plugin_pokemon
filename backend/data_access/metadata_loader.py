import csv
from typing import Dict, Any, List, Optional
from backend.models.skill import Skill, SecondaryEffect
from backend.models.attribute import Attribute
from backend.models.race import Race, LearnableSkill
from backend.models.item import Item
from backend.models.ability import Ability
from backend.models.status_effect import StatusEffect # Import StatusEffect model
from backend.utils.logger import get_logger
import os

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
                    status_immunities=status_immunities, # Load status immunities
                    # TODO: Add other item properties like effects, consumable, etc. (S123 refinement)
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
                    status_immunities=status_immunities, # Load status immunities
                    # TODO: Add other ability properties like effects, trigger conditions, etc. (S122 refinement)
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
                    # TODO: Add other status effect properties like duration, effects, etc. (S125 refinement)
                )
        logger.info(f"Loaded {len(status_effects)} status effects.")
    except FileNotFoundError:
        logger.error(f"Status effects CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading status effects: {e}")
    return status_effects

# TODO: Add loading for field effects (weather, terrain) (S126 refinement)
# async def load_field_effects(...):
#      pass

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
        self._field_effects: Optional[Dict[str, Any]] = None # Add field effects dictionary

    async def load_all(self):
        """Loads all metadata asynchronously."""
        logger.info("Loading all metadata...")
        self._skills = await load_skills()
        self._attributes = await load_attributes()
        self._races = await load_races()
        self._items = await load_items() # Load items
        self._abilities = await load_abilities() # Load abilities
        self._status_effects = await load_status_effects() # Load status effects
        # TODO: Load field effects (S126 refinement)
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

    def get_field_effect(self, effect_logic_key: str) -> Optional[Dict[str, Any]]:
        """Gets a field effect (terrain/weather) by its logic key."""
        return self._field_effects.get(effect_logic_key) if self._field_effects else None

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


    # TODO: Add methods to get all skills, races, etc. if needed (S30 refinement) 