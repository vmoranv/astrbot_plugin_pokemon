import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

def _get_int_env(self, key: str, default: int) -> int:
    """安全地获取整数类型的环境变量"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

def _get_float_env(self, key: str, default: float) -> float:
    """安全地获取浮点数类型的环境变量"""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default

def validate_settings(self) -> bool:
    """验证配置参数的有效性"""
    try:
        # 验证目录路径
        if not os.path.exists(self.DATABASE_DIR):
            os.makedirs(self.DATABASE_DIR, exist_ok=True)
        if not os.path.exists(self.DATA_DIR):
            os.makedirs(self.DATA_DIR, exist_ok=True)
            
        # 验证数值范围
        if self.MAX_PARTY_SIZE <= 0 or self.MAX_PARTY_SIZE > 10:
            raise ValueError("MAX_PARTY_SIZE must be between 1 and 10")
        if self.MAX_POKEMON_LEVEL <= 0 or self.MAX_POKEMON_LEVEL > 200:
            raise ValueError("MAX_POKEMON_LEVEL must be between 1 and 200")
            
        return True
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False

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

        # Battle settings
        self.MAX_PARTY_SIZE: int = int(os.getenv("MAX_PARTY_SIZE", "6"))
        self.WILD_POKEMON_ENCOUNTER_RATE: float = float(os.getenv("WILD_POKEMON_ENCOUNTER_RATE", "0.1"))
        self.MAX_POKEMON_LEVEL: int = int(os.getenv("MAX_POKEMON_LEVEL", "100"))

        # Item settings
        self.MAX_INVENTORY_SIZE: int = int(os.getenv("MAX_INVENTORY_SIZE", "999"))
        self.DEFAULT_POKEBALL_ID: int = int(os.getenv("DEFAULT_POKEBALL_ID", "1"))

        # Battle mechanics
        self.EXPERIENCE_MULTIPLIER: float = float(os.getenv("EXPERIENCE_MULTIPLIER", "1.0"))
        self.CATCH_RATE_MULTIPLIER: float = float(os.getenv("CATCH_RATE_MULTIPLIER", "1.0"))

        # Ensure database directory exists
        os.makedirs(self.DATABASE_DIR, exist_ok=True)
        # Ensure data directory exists
        os.makedirs(self.DATA_DIR, exist_ok=True)

settings = Settings()
