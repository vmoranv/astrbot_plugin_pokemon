import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for achievements data
from backend.data_access.repositories.achievement_repository import AchievementRepository # Example repository import
from backend.models.achievement import Achievement # Example model import

logger = get_logger(__name__)

async def load_achievements_data() -> None:
    """
    Loads achievements data from a CSV file into the database.
    """
    logger.info("Loading achievements data...")
    file_path = os.path.join(settings.DATA_DIR, 'achievements.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = Achievement(
                        achievement_id=int(row['achievement_id']),
                        name=row['name'],
                        description=row.get('description', ''),
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await AchievementRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} achievement entries.")
        else:
            logger.warning("No valid achievement entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Achievements CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading achievement data: {e}")
