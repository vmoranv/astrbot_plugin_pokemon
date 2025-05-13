# Import key components for easier access
from .db_manager import get_db_connection, close_db_connection, execute_query, fetch_one, fetch_all
from .schema import create_tables
# Import repositories as they are created
# from .repositories.player_repository import PlayerRepository
# from .repositories.pokemon_repository import PokemonRepository
# from .repositories.metadata_repository import MetadataRepository 

# This file makes the 'backend.data_access' directory a Python package. 