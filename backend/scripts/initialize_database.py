import asyncio
import os
from backend.data_access.schema import create_tables
from backend.utils.logger import get_logger
from backend.config.settings import settings

# Import individual data loading scripts
from backend.scripts import (
    load_pet_dictionary,
    load_pet_system,
    load_attributes,
    load_status_effects,
    load_pet_learnable_skills,
    load_field_effects,
    load_events,
    load_npcs,
    load_skills,
    load_maps,
    load_dialogs,
    load_tasks,
    load_achievements,
    load_shops,
    load_items,
)

logger = get_logger(__name__)

async def load_initial_data() -> None:
    """
    Loads initial game metadata from data files into the database by calling specific loading scripts.
    Assumes data is stored in CSV files in the DATA_DIR.
    """
    logger.info("Starting initial game data loading process...")

    # Call individual loading scripts
    # Each script is responsible for reading its specific CSV file
    # and saving the data using the appropriate repository methods.
    await load_pet_dictionary.load_data()
    await load_pet_system.load_data()
    await load_attributes.load_data()
    await load_status_effects.load_data()
    await load_pet_learnable_skills.load_data()
    await load_field_effects.load_data()
    await load_events.load_data()
    await load_npcs.load_data()
    await load_skills.load_data()
    await load_maps.load_data()
    await load_dialogs.load_data()
    await load_tasks.load_data()
    await load_achievements.load_data()
    await load_shops.load_data()
    await load_items.load_data()

    logger.info("Initial game data loading process finished.")

async def initialize_database() -> None:
    """
    Initializes the database by creating tables and loading initial data.
    """
    logger.info("Initializing database...")
    await create_tables()
    await load_initial_data()
    logger.info("Database initialization complete.")

# Helper function to load JSON data (example) - Removed as we are using CSV
# async def load_json_data(filepath: str) -> list:
#     """Reads and parses JSON data from a file."""
#     try:
#         with open(filepath, 'r', encoding='utf-8') as f:
#             import json
#             return json.load(f)
#     except FileNotFoundError:
#         logger.error(f"Data file not found: {filepath}")
#         return []
#     except json.JSONDecodeError:
#         logger.error(f"Error decoding JSON from file: {filepath}")
#         return []
#     except Exception as e:
#         logger.error(f"An error occurred while reading {filepath}: {e}")
#         return []

# Example of how to run this script
# if __name__ == "__main__":
#     asyncio.run(initialize_database()) 