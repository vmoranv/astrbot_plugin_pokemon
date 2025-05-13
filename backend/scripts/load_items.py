import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for items data
from backend.data_access.repositories.item_repository import ItemRepository # Example repository import
from backend.models.item import Item # Example model import

logger = get_logger(__name__)

async def load_items_data() -> None:
    """
    Loads items data from a CSV file into the database.
    """
    logger.info("Loading items data...")
    file_path = os.path.join(settings.DATA_DIR, 'items.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = Item(
                        item_id=int(row['item_id']),
                        name=row['name'],
                        description=row.get('description', ''),
                        effect_type=row.get('effect_type', ''),
                        use_target=row.get('use_target', ''),
                        use_effect=row.get('use_effect', ''),
                        price=int(row['price']) if row.get('price') else 0,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await ItemRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} item entries.")
        else:
            logger.warning("No valid item entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Items CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading item data: {e}")
