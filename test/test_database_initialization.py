import pytest
import os
import aiosqlite
from unittest.mock import AsyncMock, patch, MagicMock
from backend.utils.logger import get_logger
import re
import asyncio

logger = get_logger(__name__)

# Import the function to be tested
from backend.scripts.initialize_database import initialize_database

# Import the actual repository you will be mocking
# from backend.data_access.repositories.pokemon_repository import PokemonRepository # 导入正确的仓库 - 不再直接导入类，而是模拟类本身

# Helper function to extract table names from SQL
def extract_table_names(sql_content):
    """Extracts table names from SQL CREATE TABLE statements."""
    # If sql_content is a list, join the elements into a single string
    if isinstance(sql_content, list):
        sql_content = "\n".join(sql_content)

    # This regex looks for CREATE TABLE followed by optional IF NOT EXISTS and captures the table name (word characters)
    matches = re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", sql_content)
    return set(matches)

# Load schema SQL to get expected table names
# Assuming schema.py has constants for table creation SQL
from backend.data_access.schema import GAME_MAIN_TABLES_SQL, GAME_RECORD_TABLES_SQL

EXPECTED_MAIN_TABLES = extract_table_names(GAME_MAIN_TABLES_SQL)
EXPECTED_RECORD_TABLES = extract_table_names(GAME_RECORD_TABLES_SQL)


@pytest.mark.asyncio
async def test_initialize_database_creates_files_and_tables(tmp_path, mocker):
    """
    Tests that initialize_database creates the database files and all expected tables,
    and orchestrates calls to data loading functions (which will have their repository
    interactions mocked).
    """
    # Create temporary directories for databases and data
    temp_db_dir = tmp_path / "db"
    temp_db_dir.mkdir()
    temp_data_dir = tmp_path / "data"
    temp_data_dir.mkdir() # Create a dummy data directory

    temp_main_db_path = temp_db_dir / "game_main.db"
    temp_record_db_path = temp_db_dir / "game_record.db"

    # Mock the entire settings object
    mock_settings = MagicMock()

    # Patch the settings object *within the schema module* to ensure create_tables uses the mock settings
    # We apply the patch first, then configure the mock that is now in place in the schema module.
    settings_patch = mocker.patch('backend.data_access.schema.settings', new=mock_settings)

    # Now configure the mock object that has replaced the original settings in schema.py
    settings_patch.configure_mock(
        MAIN_DATABASE_PATH=str(temp_main_db_path), # Use MAIN_DATABASE_PATH as defined in settings.py
        RECORD_DATABASE_PATH=str(temp_record_db_path), # Use RECORD_DATABASE_PATH as defined in settings.py
        DATA_DIR=str(temp_data_dir)
    )

    # --- Start: Mock Repository methods instead of loading functions ---
    # We need to mock the methods that the loading scripts will call to interact with the DB.
    # Assuming a pattern like backend.data_access.repositories.[table_name]_repository.[TableName]Repository.insert_many
    # We need to mock the CLASS so that when it's instantiated, we get a mock instance.

    # Mock the PokemonRepository class itself
    mock_pokemon_repo_class = MagicMock()
    # Configure the mock class to return a mock instance when called (instantiated)
    mock_pokemon_repo_instance = AsyncMock() # Use AsyncMock for the instance if its methods are async
    mock_pokemon_repo_class.return_value = mock_pokemon_repo_instance

    # Now, patch the specific method on the mock instance that will be returned
    # Assuming load_pet_dictionary_data creates an instance and calls insert_races on it
    # Patch the PokemonRepository class *within the load_pet_dictionary module*
    mocker.patch('backend.scripts.load_pet_dictionary.PokemonRepository', new=mock_pokemon_repo_class)

    # Ensure the database files do NOT exist before initialization
    assert not os.path.exists(temp_main_db_path)
    assert not os.path.exists(temp_record_db_path)

    # Call the function to initialize the database
    await initialize_database()

    # Assert that the database files were created
    assert os.path.exists(temp_main_db_path)
    assert os.path.exists(temp_record_db_path)

    # Now, connect to the created temporary databases and verify the tables exist
    # This part is crucial to ensure create_tables actually ran and worked.
    async with aiosqlite.connect(str(temp_main_db_path)) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in await cursor.fetchall()}
        logger.info(f"Tables found in game_main.db: {tables}")
        # Check if all expected tables are present
        for expected_table in EXPECTED_MAIN_TABLES:
             assert expected_table in tables, f"Table {expected_table} not found in game_main.db"

    async with aiosqlite.connect(str(temp_record_db_path)) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in await cursor.fetchall()}
        logger.info(f"Tables found in game_record.db: {tables}")
        # Check if all expected tables are present
        for expected_table in EXPECTED_RECORD_TABLES:
             assert expected_table in tables, f"Table {expected_table} not found in game_record.db"


    # Verify that the mocked repository methods were called
    mock_pokemon_repo_instance.insert_races.assert_called_once()
    # Add assertions for other mocked repository methods here 