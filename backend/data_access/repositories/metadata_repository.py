from typing import Optional, List, Dict, Any
import json
from backend.models.race import Race
from backend.models.item import Item
# Import other metadata models (Skill, Map, Dialog, etc.)
from backend.models.skill import Skill
# from backend.models.map import Map # Map and Dialog return dict for now
# from backend.models.dialog import Dialog
from backend.models.attribute import Attribute
from backend.models.status_effect import StatusEffect
from backend.models.field_effect import FieldEffect
from backend.models.event import Event
from backend.models.npc import NPC
from backend.models.task import Task
from backend.models.achievement import Achievement
from backend.models.shop import Shop

from backend.data_access.db_manager import fetch_one, fetch_all, execute_query
from backend.utils.exceptions import RaceNotFoundException, ItemNotFoundException
from backend.utils.logger import get_logger
import aiosqlite
from backend.config.settings import settings

logger = get_logger(__name__)

class MetadataRepository:
    """Repository for static game metadata (Races, Items, Skills, Maps, Dialogs, etc.)."""

    def __init__(self):
        self.db_path = settings.metadata_database_path # Assuming settings has a path for metadata DB

    async def get_race_by_id(self, race_id: int) -> Optional[Race]:
        """
        Retrieves a pokemon race (species) by its ID.
        """
        sql = "SELECT * FROM races WHERE race_id = ?"
        row = await fetch_one(sql, (race_id,))
        if row:
            row_dict = dict(row)
            row_dict['base_stats'] = json.loads(row_dict.get('base_stats', '{}'))
            row_dict['abilities'] = json.loads(row_dict.get('abilities', '[]'))
            row_dict['learnable_skills'] = json.loads(row_dict.get('learnable_skills', '[]'))
            return Race.from_dict(row_dict)
        return None

    async def get_item_by_id(self, item_id: int) -> Optional[Item]:
        """
        Retrieves an item by its ID.
        """
        sql = "SELECT * FROM items WHERE item_id = ?"
        row = await fetch_one(sql, (item_id,))
        if row:
            row_dict = dict(row)
            row_dict['effects'] = json.loads(row_dict.get('effects', '{}'))
            return Item.from_dict(row_dict)
        return None

    async def get_map_by_id(self, map_id: str) -> Optional[Dict[str, Any]]: # Return dict for simplicity in MVP
        """
        Retrieves map data by its ID.
        """
        sql = "SELECT * FROM maps WHERE map_id = ?"
        row = await fetch_one(sql, (map_id,))
        if row:
             row_dict = dict(row)
             row_dict['adjacent_maps'] = json.loads(row_dict.get('adjacent_maps', '[]'))
             row_dict['encounter_pool'] = json.loads(row_dict.get('encounter_pool', '{}'))
             row_dict['npcs'] = json.loads(row_dict.get('npcs', '[]'))
             row_dict['items'] = json.loads(row_dict.get('items', '[]'))
             return row_dict # Return dict for now, can convert to Map model later
        return None

    async def get_dialog_by_id(self, dialog_id: int) -> Optional[Dict[str, Any]]: # Return dict for simplicity in MVP
        """
        Retrieves dialog data by its ID.
        """
        sql = "SELECT * FROM dialogs WHERE dialog_id = ?"
        row = await fetch_one(sql, (dialog_id,))
        if row:
            row_dict = dict(row)
            row_dict['options'] = json.loads(row_dict.get('options', '[]'))
            row_dict['requires_task_status'] = json.loads(row_dict.get('requires_task_status', '{}'))
            return row_dict # Return dict for now, can convert to Dialog model later
        return None

    # Add methods to get other metadata (Skills, Status Effects, etc.)

    async def get_skill_by_id(self, skill_id: int) -> Optional[Skill]:
        """
        Retrieves a skill by its ID.
        """
        sql = "SELECT * FROM skills WHERE skill_id = ?"
        row = await fetch_one(sql, (skill_id,))
        if row:
            row_dict = dict(row)
            # Assuming 'effects' and 'target' might be JSON based on common game data
            row_dict['effects'] = json.loads(row_dict.get('effects', '{}'))
            row_dict['target'] = json.loads(row_dict.get('target', '{}'))
            return Skill.from_dict(row_dict)
        return None

    async def get_attribute_by_id(self, attribute_id: int) -> Optional[Attribute]:
        """
        Retrieves an attribute by its ID.
        """
        sql = "SELECT * FROM attributes WHERE attribute_id = ?"
        row = await fetch_one(sql, (attribute_id,))
        if row:
            row_dict = dict(row)
            return Attribute.from_dict(row_dict)
        return None

    async def get_status_effect_by_id(self, effect_id: int) -> Optional[StatusEffect]:
        """
        Retrieves a status effect by its ID.
        """
        sql = "SELECT * FROM status_effects WHERE effect_id = ?"
        row = await fetch_one(sql, (effect_id,))
        if row:
            row_dict = dict(row)
            # Assuming 'effects' might be JSON
            row_dict['effects'] = json.loads(row_dict.get('effects', '{}'))
            return StatusEffect.from_dict(row_dict)
        return None

    async def get_field_effect_by_id(self, effect_id: int) -> Optional[FieldEffect]:
        """
        Retrieves a field effect by its ID.
        """
        sql = "SELECT * FROM field_effects WHERE effect_id = ?"
        row = await fetch_one(sql, (effect_id,))
        if row:
            row_dict = dict(row)
            # Assuming 'effects' might be JSON
            row_dict['effects'] = json.loads(row_dict.get('effects', '{}'))
            return FieldEffect.from_dict(row_dict)
        return None

    async def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """
        Retrieves an event by its ID.
        """
        sql = "SELECT * FROM events WHERE event_id = ?"
        row = await fetch_one(sql, (event_id,))
        if row:
            row_dict = dict(row)
            # Assuming 'triggers' and 'actions' might be JSON
            row_dict['triggers'] = json.loads(row_dict.get('triggers', '[]'))
            row_dict['actions'] = json.loads(row_dict.get('actions', '[]'))
            return Event.from_dict(row_dict)
        return None

    async def get_npc_by_id(self, npc_id: int) -> Optional[NPC]:
        """
        Retrieves an NPC by its ID.
        """
        sql = "SELECT * FROM npcs WHERE npc_id = ?"
        row = await fetch_one(sql, (npc_id,))
        if row:
            row_dict = dict(row)
            # Assuming 'dialog_ids' and 'shop_id' (if NPC is a shopkeeper) might be JSON/nullable
            row_dict['dialog_ids'] = json.loads(row_dict.get('dialog_ids', '[]'))
            row_dict['shop_id'] = row_dict.get('shop_id') # Assuming shop_id is not JSON
            return NPC.from_dict(row_dict)
        return None

    async def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """
        Retrieves a task by its ID.
        """
        sql = "SELECT * FROM tasks WHERE task_id = ?"
        row = await fetch_one(sql, (task_id,))
        if row:
            row_dict = dict(row)
            # Assuming 'objectives' and 'rewards' might be JSON
            row_dict['objectives'] = json.loads(row_dict.get('objectives', '[]'))
            row_dict['rewards'] = json.loads(row_dict.get('rewards', '[]'))
            return Task.from_dict(row_dict)
        return None

    async def get_achievement_by_id(self, achievement_id: int) -> Optional[Achievement]:
        """
        Retrieves an achievement by its ID.
        """
        sql = "SELECT * FROM achievements WHERE achievement_id = ?"
        row = await fetch_one(sql, (achievement_id,))
        if row:
            row_dict = dict(row)
            # Assuming 'criteria' and 'rewards' might be JSON
            row_dict['criteria'] = json.loads(row_dict.get('criteria', '[]'))
            row_dict['rewards'] = json.loads(row_dict.get('rewards', '[]'))
            return Achievement.from_dict(row_dict)
        return None

    async def get_shop_by_id(self, shop_id: int) -> Optional[Shop]:
        """
        Retrieves a shop by its ID.
        """
        sql = "SELECT * FROM shops WHERE shop_id = ?"
        row = await fetch_one(sql, (shop_id,))
        if row:
            row_dict = dict(row)
            # Assuming 'items_for_sale' might be JSON
            row_dict['items_for_sale'] = json.loads(row_dict.get('items_for_sale', '[]'))
            return Shop.from_dict(row_dict)
        return None

    async def save_race(self, race: Race) -> None:
        """
        Saves or updates race data. Used during initial data loading.
        """
        race_data = race.to_dict()
        race_data['base_stats'] = json.dumps(race_data['base_stats'])
        race_data['abilities'] = json.dumps(race_data['abilities'])
        race_data['learnable_skills'] = json.dumps(race_data['learnable_skills'])

        sql = """
        INSERT OR REPLACE INTO races (race_id, name, type1_id, type2_id, base_stats, abilities, learnable_skills, evolution_chain_id, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            race.race_id, race.name, race.type1_id, race.type2_id,
            race_data['base_stats'], race_data['abilities'], race_data['learnable_skills'],
            race.evolution_chain_id, race.description
        )
        await execute_query(sql, params)
        logger.debug(f"Saved race: {race.race_id}")

    async def save_item(self, item: Item) -> None:
        """
        Saves or updates item data. Used during initial data loading.
        """
        item_data = item.to_dict()
        item_data['effects'] = json.dumps(item_data['effects'])

        sql = """
        INSERT OR REPLACE INTO items (item_id, name, description, item_type, value, effects)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            item.item_id, item.name, item.description, item.item_type,
            item.value, item_data['effects']
        )
        await execute_query(sql, params)
        logger.debug(f"Saved item: {item.item_id}")

    async def save_map(self, map_data: Dict[str, Any]) -> None: # Save dict for simplicity in MVP
        """
        Saves or updates map data. Used during initial data loading.
        """
        map_data['adjacent_maps'] = json.dumps(map_data.get('adjacent_maps', []))
        map_data['encounter_pool'] = json.dumps(map_data.get('encounter_pool', {}))
        map_data['npcs'] = json.dumps(map_data.get('npcs', []))
        map_data['items'] = json.dumps(map_data.get('items', []))

        sql = """
        INSERT OR REPLACE INTO maps (map_id, name, description, adjacent_maps, encounter_pool, npcs, items)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            map_data.get('map_id'), map_data.get('name'), map_data.get('description', ''),
            map_data['adjacent_maps'], map_data['encounter_pool'], map_data['npcs'], map_data['items']
        )
        await execute_query(sql, params)
        logger.debug(f"Saved map: {map_data.get('map_id')}")

    async def save_dialog(self, dialog_data: Dict[str, Any]) -> None: # Save dict for simplicity in MVP
        """
        Saves or updates dialog data. Used during initial data loading.
        """
        dialog_data['options'] = json.dumps(dialog_data.get('options', []))
        dialog_data['requires_task_status'] = json.dumps(dialog_data.get('requires_task_status', {}))

        sql = """
        INSERT OR REPLACE INTO dialogs (dialog_id, text, options, requires_item, requires_task_status)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            dialog_data.get('dialog_id'), dialog_data.get('text'), dialog_data['options'],
            dialog_data.get('requires_item'), dialog_data['requires_task_status']
        )
        await execute_query(sql, params)
        logger.debug(f"Saved dialog: {dialog_data.get('dialog_id')}")

    # Add save methods for other metadata types

    async def save_skill(self, skill: Skill) -> None:
        """
        Saves or updates skill data. Used during initial data loading.
        """
        skill_data = skill.to_dict()
        skill_data['effects'] = json.dumps(skill_data.get('effects', {}))
        skill_data['target'] = json.dumps(skill_data.get('target', {}))

        sql = """
        INSERT OR REPLACE INTO skills (skill_id, name, description, power, accuracy, pp, type_id, category, effects, target)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            skill.skill_id, skill.name, skill.description, skill.power, skill.accuracy,
            skill.pp, skill.type_id, skill.category, skill_data['effects'], skill_data['target']
        )
        await execute_query(sql, params)
        logger.debug(f"Saved skill: {skill.skill_id}")

    async def save_attribute(self, attribute: Attribute) -> None:
        """
        Saves or updates attribute data. Used during initial data loading.
        """
        attribute_data = attribute.to_dict()

        sql = """
        INSERT OR REPLACE INTO attributes (attribute_id, name, description)
        VALUES (?, ?, ?)
        """
        params = (
            attribute.attribute_id, attribute.name, attribute.description
        )
        await execute_query(sql, params)
        logger.debug(f"Saved attribute: {attribute.attribute_id}")

    async def save_status_effect(self, effect: StatusEffect) -> None:
        """
        Saves or updates status effect data. Used during initial data loading.
        """
        effect_data = effect.to_dict()
        effect_data['effects'] = json.dumps(effect_data.get('effects', {}))

        sql = """
        INSERT OR REPLACE INTO status_effects (effect_id, name, description, duration, effects)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            effect.effect_id, effect.name, effect.description, effect.duration, effect_data['effects']
        )
        await execute_query(sql, params)
        logger.debug(f"Saved status effect: {effect.effect_id}")

    async def save_field_effect(self, effect: FieldEffect) -> None:
        """
        Saves or updates field effect data. Used during initial data loading.
        """
        effect_data = effect.to_dict()
        effect_data['effects'] = json.dumps(effect_data.get('effects', {}))

        sql = """
        INSERT OR REPLACE INTO field_effects (effect_id, name, description, duration, effects)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            effect.effect_id, effect.name, effect.description, effect.duration, effect_data['effects']
        )
        await execute_query(sql, params)
        logger.debug(f"Saved field effect: {effect.effect_id}")

    async def save_event(self, event: Event) -> None:
        """
        Saves or updates event data. Used during initial data loading.
        """
        event_data = event.to_dict()
        event_data['triggers'] = json.dumps(event_data.get('triggers', []))
        event_data['actions'] = json.dumps(event_data.get('actions', []))

        sql = """
        INSERT OR REPLACE INTO events (event_id, name, description, triggers, actions)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            event.event_id, event.name, event.description, event_data['triggers'], event_data['actions']
        )
        await execute_query(sql, params)
        logger.debug(f"Saved event: {event.event_id}")

    async def save_npc(self, npc: NPC) -> None:
        """
        Saves or updates NPC data. Used during initial data loading.
        """
        npc_data = npc.to_dict()
        npc_data['dialog_ids'] = json.dumps(npc_data.get('dialog_ids', []))
        # shop_id is not JSON

        sql = """
        INSERT OR REPLACE INTO npcs (npc_id, name, description, map_id, position_x, position_y, dialog_ids, shop_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            npc.npc_id, npc.name, npc.description, npc.map_id, npc.position_x,
            npc.position_y, npc_data['dialog_ids'], npc.shop_id
        )
        await execute_query(sql, params)
        logger.debug(f"Saved NPC: {npc.npc_id}")

    async def save_task(self, task: Task) -> None:
        """
        Saves or updates task data. Used during initial data loading.
        """
        task_data = task.to_dict()
        task_data['objectives'] = json.dumps(task_data.get('objectives', []))
        task_data['rewards'] = json.dumps(task_data.get('rewards', []))

        sql = """
        INSERT OR REPLACE INTO tasks (task_id, name, description, objectives, rewards, next_task_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            task.task_id, task.name, task.description, task_data['objectives'],
            task_data['rewards'], task.next_task_id
        )
        await execute_query(sql, params)
        logger.debug(f"Saved task: {task.task_id}")

    async def save_achievement(self, achievement: Achievement) -> None:
        """
        Saves or updates achievement data. Used during initial data loading.
        """
        achievement_data = achievement.to_dict()
        achievement_data['criteria'] = json.dumps(achievement_data.get('criteria', []))
        achievement_data['rewards'] = json.dumps(achievement_data.get('rewards', []))

        sql = """
        INSERT OR REPLACE INTO achievements (achievement_id, name, description, criteria, rewards)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            achievement.achievement_id, achievement.name, achievement.description,
            achievement_data['criteria'], achievement_data['rewards']
        )
        await execute_query(sql, params)
        logger.debug(f"Saved achievement: {achievement.achievement_id}")

    async def save_shop(self, shop: Shop) -> None:
        """
        Saves or updates shop data. Used during initial data loading.
        """
        shop_data = shop.to_dict()
        shop_data['items_for_sale'] = json.dumps(shop_data.get('items_for_sale', []))

        sql = """
        INSERT OR REPLACE INTO shops (shop_id, name, description, items_for_sale)
        VALUES (?, ?, ?, ?)
        """
        params = (
            shop.shop_id, shop.name, shop.description, shop_data['items_for_sale']
        )
        await execute_query(sql, params)
        logger.debug(f"Saved shop: {shop.shop_id}")

    async def get_pokemon_race_data(self, race_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves metadata for a specific pokemon race.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM pokemon_races WHERE race_id = ?", (race_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_item_data(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves metadata for a specific item.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_location_data(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves metadata for a specific location.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM locations WHERE location_id = ?", (location_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_location_encounters(self, location_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves encounter details for a specific location.
        Returns a list of dictionaries, each containing pokemon_race_id, min_level, max_level, and weight.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT pokemon_race_id, min_level, max_level, weight FROM location_encounters WHERE location_id = ?",
                (location_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows] 