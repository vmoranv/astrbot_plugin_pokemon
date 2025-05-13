import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

class Settings:
    """Application settings."""
    def __init__(self):
        # Database settings
        self.DATABASE_DIR: str = os.getenv("DATABASE_DIR", "backend/db")
        self.MAIN_DATABASE_PATH: str = os.path.join(self.DATABASE_DIR, os.getenv("MAIN_DATABASE_NAME", "game_main.db"))
        self.RECORD_DATABASE_PATH: str = os.path.join(self.DATABASE_DIR, os.getenv("RECORD_DATABASE_NAME", "game_record.db"))

        # Data file settings
        self.DATA_DIR: str = os.getenv("DATA_DIR", "backend/data")
        self.PET_DICTIONARY_CSV: str = os.path.join(self.DATA_DIR, os.getenv("PET_DICTIONARY_CSV", "pet_dictionary.csv"))
        # Add paths for other data files

        # Logging settings
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

        # Game settings (examples)
        self.STARTING_MONEY: int = int(os.getenv("STARTING_MONEY", "1000"))
        self.PLAYER_START_LOCATION: str = os.getenv("PLAYER_START_LOCATION", "town_01")

        # Ensure database directory exists
        os.makedirs(self.DATABASE_DIR, exist_ok=True)

settings = Settings()

# Example usage:
# from backend.config.settings import settings
# db_path = settings.MAIN_DATABASE_PATH
