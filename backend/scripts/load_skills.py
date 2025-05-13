import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for skills data
from backend.data_access.repositories.skill_repository import SkillRepository # Example repository import
from backend.models.skill import Skill # Example model import

logger = get_logger(__name__)

async def load_skills_data() -> None:
    """
    Loads skills data from a CSV file into the database.
    """
    logger.info("Loading skills data...")
    file_path = os.path.join(settings.DATA_DIR, 'skills.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = Skill(
                        skill_id=int(row['skill_id']),
                        name=row['name'],
                        skill_type=row['type'],
                        power=int(row['power']) if row.get('power') and row.get('power').isdigit() else None,
                        accuracy=int(row['accuracy']) if row.get('accuracy') and row.get('accuracy').isdigit() else None,
                        critical_rate=int(row['critical_rate']) if row.get('critical_rate') and row.get('critical_rate').isdigit() else None,
                        pp=int(row['pp']) if row.get('pp') and row.get('pp').isdigit() else None,
                        category=row['category'],
                        priority=int(row['priority']) if row.get('priority') and row.get('priority').isdigit() else 0,
                        target_type=row['target_type'],
                        effect_logic_key=row.get('effect_logic_key', ''),
                        description=row.get('description', '')
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await SkillRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} skill entries.")
        else:
            logger.warning("No valid skill entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Skills CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading skills data: {e}")
