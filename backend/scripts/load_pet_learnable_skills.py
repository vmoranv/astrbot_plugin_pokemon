import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for pet learnable skills data
from backend.data_access.repositories.pet_learnable_skills_repository import PetLearnableSkillsRepository # Example repository import
from backend.models.pet_learnable_skill import PetLearnableSkill # Example model import

logger = get_logger(__name__)

async def load_pet_learnable_skills_data() -> None:
    """
    Loads pet learnable skills data from a CSV file into the database.
    """
    logger.info("Loading pet learnable skills data...")
    file_path = os.path.join(settings.DATA_DIR, 'pet_learnable_skills.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = PetLearnableSkill(
                        race_id=int(row['race_id']),
                        skill_id=int(row['skill_id']),
                        learn_method=row['learn_method'],
                        learn_level=int(row['learn_level']) if row.get('learn_level') else None,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await PetLearnableSkillsRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} pet learnable skill entries.")
        else:
            logger.warning("No valid pet learnable skill entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Pet learnable skills CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading pet learnable skills data: {e}")
