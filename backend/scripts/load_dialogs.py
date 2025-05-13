import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for dialogs data
from backend.data_access.repositories.dialog_repository import DialogRepository # Example repository import
from backend.models.dialog import Dialog # Example model import

logger = get_logger(__name__)

async def load_dialogs_data() -> None:
    """
    Loads dialogs data from a CSV file into the database.
    """
    logger.info("Loading dialogs data...")
    file_path = os.path.join(settings.DATA_DIR, 'dialogs.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = Dialog(
                        dialog_id=int(row['dialog_id']),
                        text=row['text'],
                        next_dialog_id=int(row['next_dialog_id']) if row.get('next_dialog_id') else None,
                        option1_text=row.get('option1_text', ''),
                        option1_next_dialog_id=int(row['option1_next_dialog_id']) if row.get('option1_next_dialog_id') else None,
                        option2_text=row.get('option2_text', ''),
                        option2_next_dialog_id=int(row['option2_next_dialog_id']) if row.get('option2_next_dialog_id') else None,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await DialogRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} dialog entries.")
        else:
            logger.warning("No valid dialog entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Dialogs CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading dialogs data: {e}")

