from typing import Optional, Dict, Any, List
import aiosqlite
import json # Need json for log serialization
from backend.models.battle import Battle
from backend.utils.logger import get_logger
# Assuming db_manager is available for database path
from backend.data_access.db_manager import DATABASE_PATH

logger = get_logger(__name__)

class BattleRepository:
    """Repository for handling Battle data persistence."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def create_battle_table(self):
        """Creates the battles table if it doesn't exist."""
        sql = """
        CREATE TABLE IF NOT EXISTS battles (
            battle_id TEXT PRIMARY KEY,
            player_id TEXT NOT NULL,
            wild_pokemon_instance_id TEXT NOT NULL,
            player_pokemon_instance_id TEXT NOT NULL,
            current_turn INTEGER DEFAULT 1,
            log TEXT DEFAULT '[]', -- Store log as JSON string
            start_time TEXT NOT NULL,
            end_time TEXT,
            outcome TEXT,
            run_attempts INTEGER DEFAULT 0,
            weather TEXT, -- Add weather column
            terrain TEXT -- Add terrain column
        )
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(sql)
            await db.commit()
        logger.info("Ensured battles table exists.")

    async def save_battle(self, battle: Battle):
        """Saves or updates a battle in the database."""
        sql = """
        INSERT OR REPLACE INTO battles (
            battle_id, player_id, wild_pokemon_instance_id, player_pokemon_instance_id,
            current_turn, log, start_time, end_time, outcome, run_attempts, weather, terrain
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Convert log (list of strings) to JSON string for storage
        log_json = json.dumps(battle.log)
        params = (
            battle.battle_id, battle.player_id, battle.wild_pokemon_instance_id,
            battle.player_pokemon_instance_id, battle.current_turn, log_json,
            battle.start_time.isoformat(), battle.end_time.isoformat() if battle.end_time else None,
            battle.outcome, battle.run_attempts, battle.weather, battle.terrain # Include weather and terrain
        )
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(sql, params)
            await db.commit()
        logger.debug(f"Battle {battle.battle_id} saved.")

    async def get_battle_by_id(self, battle_id: str) -> Optional[Battle]:
        """Retrieves a battle by its ID."""
        sql = "SELECT * FROM battles WHERE battle_id = ?"
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row # Return rows as dict-like objects
            cursor = await db.execute(sql, (battle_id,))
            row = await cursor.fetchone()
            if row:
                row_dict = dict(row)
                # Convert log JSON string back to list
                row_dict['log'] = json.loads(row_dict.get('log', '[]'))
                return Battle.from_dict(row_dict)
            return None

    async def delete_battle(self, battle_id: str):
        """Deletes a battle from the database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM battles WHERE battle_id = ?", (battle_id,))
            await db.commit()
        logger.debug(f"Battle {battle_id} deleted.")

    # TODO: Add methods for querying battles (e.g., get all active battles) (S3 refinement) 