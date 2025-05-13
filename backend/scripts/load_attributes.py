import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for attributes data
from backend.data_access.repositories.attribute_repository import AttributeRepository # Example repository import
from backend.models.attribute import Attribute # Example model import

logger = get_logger(__name__)

async def load_attributes_data() -> None:
    """
    Loads attributes data from a CSV file into the database.
    """
    logger.info("Loading attributes data...")
    file_path = os.path.join(settings.DATA_DIR, 'attributes.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = Attribute(
                        attribute_id=int(row['attribute_id']),
                        attribute_name=row['attribute_name'],
                        attacking_id=int(row['attacking_id']) if row.get('attacking_id') else None,
                        defending_id=int(row['defending_id']) if row.get('defending_id') else None,
                        super_effective_id=int(row['super_effective_id']) if row.get('super_effective_id') else None,
                        none_effective_id=int(row['none_effective_id']) if row.get('none_effective_id') else None,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await AttributeRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} attribute entries.")
        else:
            logger.warning("No valid attribute entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Attributes CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading attribute data: {e}")
