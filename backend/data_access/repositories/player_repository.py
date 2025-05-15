from typing import Optional, Dict, Any, List
import json
from backend.models.player import Player
from backend.data_access.db_manager import fetch_one, execute_query
from backend.utils.exceptions import PlayerNotFoundException
from backend.utils.logger import get_logger
import aiosqlite
from backend.config.settings import settings # Assuming settings contains DB path

logger = get_logger(__name__)

class PlayerRepository:
    """Repository for Player data."""

    def __init__(self):
        self.db_path = settings.database_path # Get DB path from settings

    async def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """
        Retrieves a player by their ID.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Ensure the table exists (for initial setup or testing)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    location_id TEXT,
                    party_pokemon_ids TEXT, -- Store as JSON string
                    box_pokemon_ids TEXT -- Store as JSON string
                    -- Add other columns as needed
                )
            """)
            await db.commit()

            cursor = await db.execute("SELECT player_id, name, location_id, party_pokemon_ids, box_pokemon_ids FROM players WHERE player_id = ?", (player_id,))
            row = await cursor.fetchone()
            if row:
                # Deserialize JSON strings back to lists
                party_ids = json.loads(row[3]) if row[3] else []
                box_ids = json.loads(row[4]) if row[4] else []
                return Player(player_id=row[0], name=row[1], location_id=row[2], party_pokemon_ids=party_ids, box_pokemon_ids=box_ids)
            return None

    async def save_player(self, player: Player) -> None:
        """
        Saves or updates a player's data.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Serialize lists to JSON strings before saving
            party_ids_json = json.dumps(player.party_pokemon_ids)
            box_ids_json = json.dumps(player.box_pokemon_ids)

            await db.execute(
                "UPDATE players SET name = ?, location_id = ?, party_pokemon_ids = ?, box_pokemon_ids = ? WHERE player_id = ?",
                (player.name, player.location_id, party_ids_json, box_ids_json, player.player_id)
            )
            await db.commit()
            logger.debug(f"Saved player data for {player.player_id}")

    async def create_player(self, player_id: str, name: str) -> Player:
        """
        Creates a new player with default values.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Ensure the table exists
            await db.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    location_id TEXT,
                    party_pokemon_ids TEXT, -- Store as JSON string
                    box_pokemon_ids TEXT -- Store as JSON string
                    -- Add other columns as needed
                )
            """)
            await db.commit()

            # Serialize empty lists to JSON strings for new player
            initial_party_ids_json = json.dumps([])
            initial_box_ids_json = json.dumps([])

            await db.execute(
                "INSERT INTO players (player_id, name, location_id, party_pokemon_ids, box_pokemon_ids) VALUES (?, ?, ?, ?, ?)",
                (player_id, name, "starting_location", initial_party_ids_json, initial_box_ids_json) # Default location
            )
            await db.commit()
            logger.info(f"Created new player: {name} ({player_id})")
            # Return the newly created Player object
            return Player(player_id=player_id, name=name, location_id="starting_location", party_pokemon_ids=[], box_pokemon_ids=[])

    async def create_table(self):
        """Creates the players table if it doesn't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    current_map_id INTEGER,
                    current_location_x INTEGER,
                    current_location_y INTEGER,
                    inventory TEXT, -- JSON string of inventory dict {item_id: quantity}
                    -- Add other player attributes here (e.g., money, battle_id if in battle)
                    battle_id TEXT, -- Add battle_id column
                    FOREIGN KEY (current_map_id) REFERENCES maps (map_id),
                    FOREIGN KEY (battle_id) REFERENCES battles (battle_id)
                )
            """)
            await db.commit()
        logger.info("Players table checked/created.")

    async def save_player(self, player: Player):
        """Saves or updates a player in the database."""
        async with aiosqlite.connect(self.db_path) as db:
            # Serialize inventory dict to JSON string
            inventory_json = json.dumps(player.inventory)

            await db.execute("""
                INSERT OR REPLACE INTO players (
                    player_id, name, current_map_id, current_location_x,
                    current_location_y, inventory, battle_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                player.player_id,
                player.name,
                player.current_map_id,
                player.current_location_x,
                player.current_location_y,
                inventory_json, # Include inventory JSON
                player.battle_id, # Include battle_id
            ))
            await db.commit()
        logger.debug(f"Player {player.player_id} saved.")

    async def get_player(self, player_id: str) -> Optional[Player]:
        """Retrieves a player by their ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM players WHERE player_id = ?", (player_id,))
            row = await cursor.fetchone()
            if row:
                player_data = dict(row)
                # Deserialize inventory JSON string to dict
                if player_data.get("inventory"):
                    player_data["inventory"] = json.loads(player_data["inventory"])
                else:
                    player_data["inventory"] = {} # Default to empty dict if NULL

                return Player.from_dict(player_data)
            return None

    async def get_player_by_name(self, name: str) -> Optional[Player]:
        """Retrieves a player by their name."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM players WHERE name = ?", (name,))
            row = await cursor.fetchone()
            if row:
                player_data = dict(row)
                # Deserialize inventory JSON string to dict
                if player_data.get("inventory"):
                    player_data["inventory"] = json.loads(player_data["inventory"])
                else:
                    player_data["inventory"] = {} # Default to empty dict if NULL
                return Player.from_dict(player_data)
            return None

    # TODO: Add methods for updating specific player attributes (e.g., location, inventory) (S3 refinement)
    # The save_player method can handle updates, but specific methods might be cleaner. 