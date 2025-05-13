import asyncio
import os
from backend.data_access.schema import create_tables
# from backend.data_access.repositories.metadata_repository import MetadataRepository # No longer needed here
from backend.utils.logger import get_logger
from backend.config.settings import settings

# Import individual data loading scripts
from backend.scripts.load_pet_dictionary import load_pet_dictionary_data
from backend.scripts.load_pet_system import load_pet_system_data
from backend.scripts.load_attributes import load_attributes_data
from backend.scripts.load_pet_learnable_skills import load_pet_learnable_skills_data
from backend.scripts.load_skills import load_skills_data
from backend.scripts.load_status_effects import load_status_effects_data
from backend.scripts.load_field_effects import load_field_effects_data
from backend.scripts.load_items import load_items_data
from backend.scripts.load_events import load_events_data
from backend.scripts.load_npcs import load_npcs_data
from backend.scripts.load_dialogs import load_dialogs_data
from backend.scripts.load_tasks import load_tasks_data
from backend.scripts.load_achievements import load_achievements_data
from backend.scripts.load_maps import load_maps_data
from backend.scripts.load_shops import load_shops_data
# Add imports for other loading scripts as needed (e.g., evolutions, encounters, shop_items)

logger = get_logger(__name__)

async def load_initial_data() -> None:
    """
    Loads initial game metadata from CSV files into the database by calling individual loading scripts.
    """
    logger.info("Loading initial game data from CSV files...")

    # Call individual loading functions
    await load_pet_dictionary_data()
    await load_pet_system_data()
    await load_attributes_data()
    await load_skills_data() # Load skills before pet_learnable_skills
    await load_pet_learnable_skills_data()
    await load_status_effects_data()
    await load_field_effects_data()
    await load_items_data()
    await load_dialogs_data() # Load dialogs before events and npcs
    await load_events_data()
    await load_npcs_data()
    await load_tasks_data()
    await load_achievements_data()
    await load_maps_data()
    await load_shops_data()
    # Call other loading functions here following potential dependencies (e.g., encounters after maps and pet_dictionary)

    logger.info("Initial game data loading complete.")

async def initialize_database() -> None:
    """
    Initializes the database by creating tables and loading initial metadata.
    """
    logger.info("Initializing database...")
    await create_tables()
    await load_initial_data()
    logger.info("Database initialization complete.")

# Helper function to read CSV data (can be moved to a utils or data_access helper module)
# This function is just an example; the actual reading logic should be in individual load scripts
# async def read_csv_data(filename: str):
#     filepath = os.path.join(settings.DATA_DIR, filename)
#     data = []
#     try:
#         import csv
#         with open(filepath, 'r', encoding='utf-8') as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 data.append(row)
#         return data
#     except FileNotFoundError:
#         logger.error(f"Data file not found: {filepath}")
#         return []
#     except Exception as e:
#         logger.error(f"An error occurred while reading {filepath}: {e}")
#         return []


# Example usage:
# if __name__ == "__main__":
#     asyncio.run(initialize_database()) 