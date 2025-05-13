import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for events data
from backend.data_access.repositories.event_repository import EventRepository # Example repository import
from backend.models.event import Event # Example model import

logger = get_logger(__name__)

async def load_events_data() -> None:
    """
    Loads events data from a CSV file into the database.
    """
    logger.info("Loading events data...")
    file_path = os.path.join(settings.DATA_DIR, 'events.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = Event(
                        event_id=int(row['event_id']),
                        name=row['name'],
                        description=row.get('description', ''),
                        reward_item_id=int(row['reward_item_id']) if row.get('reward_item_id') else None,
                        dialog_id=int(row['dialog_id']) if row.get('dialog_id') else None,
                        pet_id=int(row['pet_id']) if row.get('pet_id') else None,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await EventRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} event entries.")
        else:
            logger.warning("No valid event entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Events CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading event data: {e}")
