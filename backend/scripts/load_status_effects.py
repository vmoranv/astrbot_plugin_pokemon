import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for status effects data
from backend.data_access.repositories.status_effect_repository import StatusEffectRepository # Example repository import
from backend.models.status_effect import StatusEffect # Example model import

logger = get_logger(__name__)

async def load_status_effects_data() -> None:
    """
    Loads status effects data from a CSV file into the database.
    """
    logger.info("Loading status effects data...")
    file_path = os.path.join(settings.DATA_DIR, 'status_effects.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # 安全地处理 length 字段
                    length_value = row.get('length')
                    if length_value:
                        try:
                            length_int = int(length_value)
                        except ValueError:
                            # 如果无法转换为整数，记录警告并设置为 None
                            logger.warning(f"Could not convert length '{length_value}' to int for status effect {row.get('status_effect_id')}. Setting length to None.")
                            length_int = None
                    else:
                        length_int = None

                    data_item = StatusEffect(
                        status_effect_id=int(row['status_effect_id']),
                        name=row['name'],
                        description=row.get('description', ''),
                        effect_logic_key=row.get('effect_logic_key', ''),
                        length=length_int,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await StatusEffectRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} status effect entries.")
        else:
            logger.warning("No valid status effect entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Status effects CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading status effects data: {e}")
