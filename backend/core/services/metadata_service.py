from typing import Optional, Dict, Any
from backend.models.race import Race
from backend.models.item import Item
# Import other metadata models
# from backend.models.skill import Skill
# from backend.models.map import Map
# from backend.models.dialog import Dialog

from backend.data_access.repositories.metadata_repository import MetadataRepository
from backend.utils.exceptions import RaceNotFoundException, ItemNotFoundException
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class MetadataService:
    """Service for accessing static game metadata."""

    def __init__(self):
        self.metadata_repo = MetadataRepository()

    async def get_race(self, race_id: int) -> Race:
        """
        Retrieves pokemon race (species) data. Raises RaceNotFoundException if not found.
        """
        race = await self.metadata_repo.get_race_by_id(race_id)
        if race is None:
            raise RaceNotFoundException(f"Pokemon race with ID {race_id} not found.")
        return race

    async def get_item(self, item_id: int) -> Item:
        """
        Retrieves item data. Raises ItemNotFoundException if not found.
        """
        item = await self.metadata_repo.get_item_by_id(item_id)
        if item is None:
            raise ItemNotFoundException(f"Item with ID {item_id} not found.")
        return item

    async def get_map(self, map_id: str) -> Optional[Dict[str, Any]]: # Return dict for simplicity in MVP
        """
        Retrieves map data.
        """
        return await self.metadata_repo.get_map_by_id(map_id)

    async def get_dialog(self, dialog_id: int) -> Optional[Dict[str, Any]]: # Return dict for simplicity in MVP
        """
        Retrieves dialog data.
        """
        return await self.metadata_repo.get_dialog_by_id(dialog_id)

    # Add methods to get other metadata (Skills, Status Effects, etc.)

    # Methods for initial data loading (might be called by main.py or a script)
    async def load_initial_data(self):
        """
        Loads initial game data from data files into the database.
        """
        logger.info("Starting initial data loading...")
        # Example: Load races from CSV
        # races_data = await read_races_from_csv(settings.PET_DICTIONARY_CSV) # Assuming a helper function
        # for race_data in races_data:
        #     race = Race.from_dict(race_data) # Assuming from_dict handles CSV row format
        #     await self.metadata_repo.save_race(race)

        # Example: Load items from CSV
        # items_data = await read_items_from_csv(settings.ITEMS_CSV) # Assuming a helper function
        # for item_data in items_data:
        #     item = Item.from_dict(item_data) # Assuming from_dict handles CSV row format
        #     await self.metadata_repo.save_item(item)

        # Load other data (maps, dialogs, skills, etc.)

        logger.info("Initial data loading complete.")

# Helper function example (needs implementation)
# async def read_races_from_csv(filepath: str) -> List[Dict[str, Any]]:
#     """Reads race data from a CSV file."""
#     # Implement CSV reading logic
#     pass

# async def read_items_from_csv(filepath: str) -> List[Dict[str, Any]]:
#     """Reads item data from a CSV file."""
#     # Implement CSV reading logic
#     pass
