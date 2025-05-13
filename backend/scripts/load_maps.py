import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for maps data
from backend.data_access.repositories.map_repository import MapRepository # Example repository import
from backend.models.map import Map # Example model import

logger = get_logger(__name__)

async def load_maps_data() -> None:
    """
    Loads map data from a CSV file into the database.
    """
    logger.info("Loading map data...")
    file_path = os.path.join(settings.DATA_DIR, 'maps.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = Map(
                        map_id=int(row['map_id']),
                        name=row['name'],
                        description=row.get('description', ''),
                        encounter_rate=float(row['encounter_rate']) if row.get('encounter_rate') else 0.0,
                        background_image_path=row.get('background_image_path', ''),
                        npc_id=int(row['npc_id']) if row.get('npc_id') else None,
                        common_pet_id=int(row['common_pet_id']) if row.get('common_pet_id') else None,
                        common_pet_rate=float(row['common_pet_rate']) if row.get('common_pet_rate') else 0.0,
                        rare_pet_id=int(row['rare_pet_id']) if row.get('rare_pet_id') else None,
                        rare_pet_rate=float(row['rare_pet_rate']) if row.get('rare_pet_rate') else 0.0,
                        rare_pet_time=int(row['rare_pet_time']) if row.get('rare_pet_time') else None,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await MapRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} map entries.")
        else:
            logger.warning("No valid map entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Maps CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading map data: {e}")
