from typing import Optional, List, Dict, Any
import json
from backend.models.race import Race
from backend.models.item import Item
# Import other metadata models (Skill, Map, Dialog, etc.)
# from backend.models.skill import Skill
# from backend.models.map import Map
# from backend.models.dialog import Dialog

from backend.data_access.db_manager import fetch_one, fetch_all, execute_query
from backend.utils.exceptions import RaceNotFoundException, ItemNotFoundException
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class MetadataRepository:
    """Repository for static game metadata (Races, Items, Skills, Maps, Dialogs, etc.)."""

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