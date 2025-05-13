import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for shops data
from backend.data_access.repositories.shop_repository import ShopRepository # Example repository import
from backend.models.shop import Shop # Example model import

logger = get_logger(__name__)

async def load_shops_data() -> None:
    """
    Loads shop data from a CSV file into the database.
    """
    logger.info("Loading shop data...")
    file_path = os.path.join(settings.DATA_DIR, 'shops.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = Shop(
                        shop_id=int(row['shop_id']),
                        name=row['name'],
                        npc_id=int(row['npc_id']) if row.get('npc_id') else None,
                        shop_type=row.get('shop_type', ''),
                        item_id=int(row['item_id']) if row.get('item_id') else None,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await ShopRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} shop entries.")
        else:
            logger.warning("No valid shop entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Shops CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading shop data: {e}")
