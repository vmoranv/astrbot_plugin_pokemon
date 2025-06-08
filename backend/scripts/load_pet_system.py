import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for pet system data
from backend.data_access.repositories.pet_system_repository import PetSystemRepository # Example repository import
from backend.models.pet_system import PetSystemData # Example model import

logger = get_logger(__name__)

async def load_pet_system_data() -> None:
    """
    Loads pet system data from a CSV file into the database.
    """
    logger.info("Loading pet system data...")
    file_path = os.path.join(settings.DATA_DIR, 'pet_system.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = PetSystemData(
                        system_id=int(row['system_id']),
                        system_name=row['system_name'],
                        system_description=row.get('system_description', ''),
                        system_effect=row.get('system_effect', '')
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await PetSystemRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} pet system entries.")
        else:
            logger.warning("No valid pet system entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Pet system CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading pet system data: {e}")
