import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for npcs data
from backend.data_access.repositories.npc_repository import NpcRepository # Example repository import
from backend.models.npc import Npc # Example model import

logger = get_logger(__name__)

async def load_npcs_data() -> None:
    """
    Loads NPC data from a CSV file into the database.
    """
    logger.info("Loading NPC data...")
    file_path = os.path.join(settings.DATA_DIR, 'npcs.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = Npc(
                        npc_id=int(row['npc_id']),
                        pet_id=int(row['pet_id']) if row.get('pet_id') else None,
                        name=row['name'],
                        interaction_type=row.get('interaction_type', ''),
                        initial_dialog_id=int(row['initial_dialog_id']) if row.get('initial_dialog_id') else None,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await NpcRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} NPC entries.")
        else:
            logger.warning("No valid NPC entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"NPCs CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading NPC data: {e}")
