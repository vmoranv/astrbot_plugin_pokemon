import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for field effects data
from backend.data_access.repositories.field_effect_repository import FieldEffectRepository # Example repository import
from backend.models.field_effect import FieldEffect # Example model import

logger = get_logger(__name__)

async def load_field_effects_data() -> None:
    """
    Loads field effects data from a CSV file into the database.
    """
    logger.info("Loading field effects data...")
    file_path = os.path.join(settings.DATA_DIR, 'field_effects.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = FieldEffect(
                        field_effect_id=int(row['field_effect_id']),
                        name=row['name'],
                        description=row.get('description', ''),
                        effect_logic_key=row.get('effect_logic_key', ''),
                        length=int(row['length']) if row.get('length') else None,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await FieldEffectRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} field effect entries.")
        else:
            logger.warning("No valid field effect entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Field effects CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading field effects data: {e}")
