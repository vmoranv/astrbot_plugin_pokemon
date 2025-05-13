import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# Import necessary repositories and models for tasks data
from backend.data_access.repositories.task_repository import TaskRepository # Example repository import
from backend.models.task import Task # Example model import

logger = get_logger(__name__)

async def load_tasks_data() -> None:
    """
    Loads task data from a CSV file into the database.
    """
    logger.info("Loading task data...")
    file_path = os.path.join(settings.DATA_DIR, 'tasks.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    data_item = Task(
                        task_id=int(row['task_id']),
                        name=row['name'],
                        description=row.get('description', ''),
                        reward_money=int(row['reward_money']) if row.get('reward_money') else 0,
                        reward_item_id=int(row['reward_item_id']) if row.get('reward_item_id') else None,
                        reward_item_quantity=int(row['reward_item_quantity']) if row.get('reward_item_quantity') else 0,
                        prerequisite_task_id=int(row['prerequisite_task_id']) if row.get('prerequisite_task_id') else None,
                        start_dialog_id=int(row['start_dialog_id']) if row.get('start_dialog_id') else None,
                        completion_dialog_id=int(row['completion_dialog_id']) if row.get('completion_dialog_id') else None,
                    )
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting data
            await TaskRepository.insert_many(data_to_insert) # Example repository method call
            logger.info(f"Successfully loaded {len(data_to_insert)} task entries.")
        else:
            logger.warning("No valid task entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Tasks CSV file not found at {file_path}")
    except Exception as e:
        logger.error(f"Error loading task data: {e}")
