import aiosqlite
from backend.config.settings import settings # Import settings to get database paths
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# SQL DDL statements to create tables for game_main.db
CREATE_PET_DICTIONARY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pet_dictionary (
    race_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    evo_level INTEGER,
    evolution_stage INTEGER,
    base_hp INTEGER NOT NULL,
    base_attack INTEGER NOT NULL,
    base_defence INTEGER NOT NULL,
    base_special_attack INTEGER NOT NULL,
    base_special_defence INTEGER NOT NULL,
    base_speed INTEGER NOT NULL,
    catch_rate INTEGER NOT NULL,
    growth_rate TEXT NOT NULL, -- e.g., 'fast', 'medium', 'slow'
    attribute_id1 INTEGER NOT NULL,
    attribute_id2 INTEGER, -- Optional second type
    height REAL,
    weight REAL,
    description TEXT,
    FOREIGN KEY (attribute_id1) REFERENCES attributes(attribute_id),
    FOREIGN KEY (attribute_id2) REFERENCES attributes(attribute_id)
);
"""

CREATE_PET_SYSTEM_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pet_system (
    system_id INTEGER PRIMARY KEY,
    system_name TEXT NOT NULL,
    system_description TEXT,
    system_effect TEXT -- JSON or specific format for effect data
);
"""

CREATE_ATTRIBUTES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS attributes (
    attribute_id INTEGER PRIMARY KEY,
    attribute_name TEXT NOT NULL UNIQUE
    -- Note: Type effectiveness is often handled in code or a separate lookup table
    -- Adding placeholder for effectiveness relationships if needed in DB
    -- attacking_id INTEGER, -- Example: Fire attacks Grass
    -- defending_id INTEGER, -- Example: Grass defends against Water
    -- super_effective_id INTEGER, -- Example: Fire is super effective against Grass
    -- none_effective_id INTEGER -- Example: Normal is none effective against Ghost
    -- FOREIGN KEY (attacking_id) REFERENCES attributes(attribute_id),
    -- FOREIGN KEY (defending_id) REFERENCES attributes(attribute_id),
    -- FOREIGN KEY (super_effective_id) REFERENCES attributes(attribute_id),
    -- FOREIGN KEY (none_effective_id) REFERENCES attributes(attribute_id)
);
"""

CREATE_PET_LEARNABLE_SKILLS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pet_learnable_skills (
    race_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    learn_method TEXT NOT NULL, -- e.g., 'level_up', 'tm', 'egg_move'
    learn_level INTEGER, -- Required for 'level_up' method
    PRIMARY KEY (race_id, skill_id, learn_method),
    FOREIGN KEY (race_id) REFERENCES pet_dictionary(race_id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);
"""

CREATE_SKILLS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS skills (
    skill_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type INTEGER NOT NULL, -- References attribute_id
    power INTEGER, -- NULL for status moves
    accuracy INTEGER, -- NULL for moves that never miss
    critical_rate INTEGER DEFAULT 0,
    pp INTEGER NOT NULL,
    category TEXT NOT NULL, -- 'physical', 'special', 'status'
    priority INTEGER DEFAULT 0,
    target_type TEXT NOT NULL, -- e.g., 'single_target', 'all_opponents', 'self'
    effect_logic_key TEXT, -- Key to look up effect logic in code
    description TEXT,
    FOREIGN KEY (type) REFERENCES attributes(attribute_id)
);
"""

CREATE_STATUS_EFFECTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS status_effects (
    status_effect_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    effect_logic_key TEXT NOT NULL, -- Key to look up effect logic in code
    length INTEGER -- Duration in turns, NULL for permanent until cured
);
"""

CREATE_FIELD_EFFECTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS field_effects (
    field_effect_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    effect_logic_key TEXT NOT NULL, -- Key to look up effect logic in code
    length INTEGER -- Duration in turns, NULL for permanent
);
"""

CREATE_ITEMS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    effect_type TEXT NOT NULL, -- e.g., 'consumable', 'equipment', 'key_item', 'pokeball'
    use_target TEXT, -- e.g., 'pokemon', 'player', 'battle', 'map'
    use_effect TEXT, -- JSON or specific format for effect data
    price INTEGER NOT NULL -- Price in shops
);
"""

CREATE_EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    reward_item_id INTEGER,
    dialog_id INTEGER,
    pet_id INTEGER, -- Could reference a specific pokemon instance or race
    FOREIGN KEY (reward_item_id) REFERENCES items(item_id),
    FOREIGN KEY (dialog_id) REFERENCES dialogs(dialog_id)
    -- FOREIGN KEY (pet_id) REFERENCES pokemon_instances(pet_id) -- If referencing instance
    -- FOREIGN KEY (pet_id) REFERENCES pet_dictionary(race_id) -- If referencing race
);
"""

CREATE_NPCS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS npcs (
    npc_id INTEGER PRIMARY KEY,
    pet_id INTEGER, -- Associated pokemon instance or race
    name TEXT NOT NULL,
    interaction_type TEXT NOT NULL, -- e.g., 'dialog', 'shop', 'battle'
    initial_dialog_id INTEGER,
    map_id INTEGER NOT NULL, -- Location of the NPC
    FOREIGN KEY (initial_dialog_id) REFERENCES dialogs(dialog_id),
    FOREIGN KEY (map_id) REFERENCES maps(map_id)
    -- FOREIGN KEY (pet_id) REFERENCES pokemon_instances(pet_id) -- If referencing instance
    -- FOREIGN KEY (pet_id) REFERENCES pet_dictionary(race_id) -- If referencing race
);
"""

CREATE_DIALOGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS dialogs (
    dialog_id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    next_dialog_id INTEGER, -- For linear dialog
    option1_text TEXT,
    option1_next_dialog_id INTEGER,
    option2_text TEXT,
    option2_next_dialog_id INTEGER,
    -- Add more options if needed
    FOREIGN KEY (next_dialog_id) REFERENCES dialogs(dialog_id),
    FOREIGN KEY (option1_next_dialog_id) REFERENCES dialogs(dialog_id),
    FOREIGN KEY (option2_next_dialog_id) REFERENCES dialogs(dialog_id)
);
"""

CREATE_TASKS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    reward_money INTEGER DEFAULT 0,
    reward_item_id INTEGER,
    reward_item_quantity INTEGER DEFAULT 1,
    prerequisite_task_id INTEGER, -- Task that must be completed first
    start_dialog_id INTEGER,
    completion_dialog_id INTEGER,
    FOREIGN KEY (reward_item_id) REFERENCES items(item_id),
    FOREIGN KEY (prerequisite_task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (start_dialog_id) REFERENCES dialogs(dialog_id),
    FOREIGN KEY (completion_dialog_id) REFERENCES dialogs(dialog_id)
);
"""

CREATE_ACHIEVEMENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS achievements (
    achievement_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);
"""

CREATE_MAPS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS maps (
    map_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    encounter_rate REAL DEFAULT 0.0, -- Probability of encountering a wild pokemon
    background_image_path TEXT,
    -- Simplified encounter pool for MVP, can be expanded with a separate table
    common_pet_id INTEGER, -- References race_id
    common_pet_rate REAL,
    rare_pet_id INTEGER, -- References race_id
    rare_pet_rate REAL,
    rare_pet_time TEXT, -- e.g., 'day', 'night', 'any'
    FOREIGN KEY (common_pet_id) REFERENCES pet_dictionary(race_id),
    FOREIGN KEY (rare_pet_id) REFERENCES pet_dictionary(race_id)
);
"""

CREATE_SHOPS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS shops (
    shop_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    npc_id INTEGER NOT NULL, -- NPC running the shop
    shop_type TEXT NOT NULL, -- e.g., 'general', 'pokemart'
    FOREIGN KEY (npc_id) REFERENCES npcs(npc_id)
);
"""

CREATE_SHOP_ITEMS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS shop_items (
    shop_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    price INTEGER, -- Override default item price if needed
    PRIMARY KEY (shop_id, item_id),
    FOREIGN KEY (shop_id) REFERENCES shops(shop_id),
    FOREIGN KEY (item_id) REFERENCES items(item_id)
);
"""

CREATE_ENCOUNTERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS encounters (
    map_id INTEGER NOT NULL,
    race_id INTEGER NOT NULL,
    rate REAL NOT NULL, -- Probability of encountering this specific race in this map
    time TEXT, -- e.g., 'day', 'night', 'any'
    PRIMARY KEY (map_id, race_id),
    FOREIGN KEY (map_id) REFERENCES maps(map_id),
    FOREIGN KEY (race_id) REFERENCES pet_dictionary(race_id)
);
"""

CREATE_EVOLUTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS evolutions (
    race_id INTEGER NOT NULL, -- The base pokemon race
    evolves_to_race_id INTEGER NOT NULL, -- The evolved pokemon race
    evolution_method TEXT NOT NULL, -- e.g., 'level', 'item', 'trade', 'friendship'
    evolution_level INTEGER, -- Required for 'level' method
    evolution_item_id INTEGER, -- Required for 'item' method
    PRIMARY KEY (race_id, evolves_to_race_id),
    FOREIGN KEY (race_id) REFERENCES pet_dictionary(race_id),
    FOREIGN KEY (evolves_to_race_id) REFERENCES pet_dictionary(race_id),
    FOREIGN KEY (evolution_item_id) REFERENCES items(item_id)
);
"""

# SQL DDL statements to create tables for game_record.db
CREATE_BATTLE_RECORDS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS battle_records (
    battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player1_id TEXT NOT NULL, -- References player_records(player_id)
    player2_id TEXT, -- NULL for wild encounters
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    winner_id TEXT, -- References player_records(player_id)
    preload_effect_id INTEGER, -- Example: Weather or terrain at start
    -- Consider adding columns for battle events/logs if needed
    FOREIGN KEY (player1_id) REFERENCES player_records(player_id),
    FOREIGN KEY (player2_id) REFERENCES player_records(player_id),
    FOREIGN KEY (winner_id) REFERENCES player_records(player_id),
    FOREIGN KEY (preload_effect_id) REFERENCES field_effects(field_effect_id)
);
"""

CREATE_PLAYER_RECORDS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_records (
    player_id TEXT PRIMARY KEY, -- AstrBot user ID
    location_id INTEGER NOT NULL, -- References maps(map_id)
    last_login_time DATETIME NOT NULL,
    money INTEGER DEFAULT 0,
    -- Inventory can be a separate table or JSON/BLOB here for simplicity in MVP
    inventory TEXT DEFAULT '{}', -- JSON string: {item_id: quantity}
    current_quest_id INTEGER, -- References tasks(task_id)
    FOREIGN KEY (location_id) REFERENCES maps(map_id),
    FOREIGN KEY (current_quest_id) REFERENCES tasks(task_id)
);
"""

CREATE_PLAYER_REPOSITORY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_repository (
    player_id TEXT NOT NULL, -- References player_records(player_id)
    pet_id INTEGER NOT NULL, -- References pokemon_instances(pet_id)
    PRIMARY KEY (player_id, pet_id),
    FOREIGN KEY (player_id) REFERENCES player_records(player_id),
    FOREIGN KEY (pet_id) REFERENCES pokemon_instances(pet_id)
);
"""

CREATE_PLAYER_PARTY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_party (
    player_id TEXT NOT NULL, -- References player_records(player_id)
    pet_id INTEGER NOT NULL, -- References pokemon_instances(pet_id)
    party_order INTEGER NOT NULL, -- Position in the party (1-6)
    PRIMARY KEY (player_id, pet_id),
    FOREIGN KEY (player_id) REFERENCES player_records(player_id),
    FOREIGN KEY (pet_id) REFERENCES pokemon_instances(pet_id)
);
"""

CREATE_POKEMON_INSTANCES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pokemon_instances (
    pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER NOT NULL, -- References pet_dictionary(race_id)
    owner_id TEXT, -- References player_records(player_id), NULL for wild pokemon
    nickname TEXT,
    level INTEGER DEFAULT 1,
    exp INTEGER DEFAULT 0,
    current_hp INTEGER, -- Can be calculated from max_hp
    max_hp INTEGER, -- Can be calculated
    attack INTEGER, -- Can be calculated
    defence INTEGER, -- Can be calculated
    special_attack INTEGER, -- Can be calculated
    special_defence INTEGER, -- Can be calculated
    speed INTEGER, -- Can be calculated
    ivs TEXT DEFAULT '{}', -- JSON string: {stat_name: value}
    evs TEXT DEFAULT '{}', -- JSON string: {stat_name: value}
    nature_id INTEGER, -- References natures(nature_id) - Need to add natures table?
    ability_id INTEGER, -- References abilities(ability_id) - Need to add abilities table?
    caught_date DATETIME,
    caught_location INTEGER, -- References maps(map_id)
    current_status_effects TEXT DEFAULT '[]', -- JSON string of status_effect_ids
    skill1_id INTEGER, -- References skills(skill_id)
    skill2_id INTEGER,
    skill3_id INTEGER,
    skill4_id INTEGER,
    skill1_pp INTEGER, -- Current PP
    skill2_pp INTEGER,
    skill3_pp INTEGER,
    skill4_pp INTEGER,
    is_in_party BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (race_id) REFERENCES pet_dictionary(race_id),
    FOREIGN KEY (owner_id) REFERENCES player_records(player_id),
    FOREIGN KEY (caught_location) REFERENCES maps(map_id),
    -- FOREIGN KEY (nature_id) REFERENCES natures(nature_id), -- Need natures table
    -- FOREIGN KEY (ability_id) REFERENCES abilities(ability_id), -- Need abilities table
    FOREIGN KEY (skill1_id) REFERENCES skills(skill_id),
    FOREIGN KEY (skill2_id) REFERENCES skills(skill_id),
    FOREIGN KEY (skill3_id) REFERENCES skills(skill_id),
    FOREIGN KEY (skill4_id) REFERENCES skills(skill_id)
);
"""

CREATE_PLAYER_QUEST_PROGRESS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_quest_progress (
    player_id TEXT NOT NULL, -- References player_records(player_id)
    task_id INTEGER NOT NULL, -- References tasks(task_id)
    status TEXT NOT NULL, -- e.g., 'not_started', 'in_progress', 'completed'
    PRIMARY KEY (player_id, task_id),
    FOREIGN KEY (player_id) REFERENCES player_records(player_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);
"""

CREATE_PLAYER_ACHIEVEMENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_achievements (
    player_id TEXT NOT NULL, -- References player_records(player_id)
    achievement_id INTEGER NOT NULL, -- References achievements(achievement_id)
    unlock_date DATETIME NOT NULL,
    PRIMARY KEY (player_id, achievement_id),
    FOREIGN KEY (player_id) REFERENCES player_records(player_id),
    FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id)
);
"""

CREATE_FRIENDS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS friends (
    player_id TEXT NOT NULL, -- References player_records(player_id)
    friend_id TEXT NOT NULL, -- References player_records(player_id)
    friendship_date DATETIME NOT NULL,
    friendship_level INTEGER DEFAULT 0,
    PRIMARY KEY (player_id, friend_id),
    FOREIGN KEY (player_id) REFERENCES player_records(player_id),
    FOREIGN KEY (friend_id) REFERENCES player_records(player_id)
);
"""

# List of all table creation SQLs for game_main.db in dependency order
GAME_MAIN_TABLES_SQL = [
    CREATE_ATTRIBUTES_TABLE_SQL, # Attributes needed for pet_dictionary and skills
    CREATE_PET_DICTIONARY_TABLE_SQL,
    CREATE_SKILLS_TABLE_SQL, # Skills needed for pet_learnable_skills and pokemon_instances
    CREATE_PET_LEARNABLE_SKILLS_TABLE_SQL,
    CREATE_STATUS_EFFECTS_TABLE_SQL,
    CREATE_FIELD_EFFECTS_TABLE_SQL,
    CREATE_ITEMS_TABLE_SQL, # Items needed for evolutions, tasks, events, shop_items
    CREATE_DIALOGS_TABLE_SQL, # Dialogs needed for npcs, tasks, events
    CREATE_MAPS_TABLE_SQL, # Maps needed for npcs, encounters, pokemon_instances, player_records
    CREATE_NPCS_TABLE_SQL, # NPCs needed for shops
    CREATE_SHOPS_TABLE_SQL,
    CREATE_SHOP_ITEMS_TABLE_SQL,
    CREATE_ENCOUNTERS_TABLE_SQL,
    CREATE_EVOLUTIONS_TABLE_SQL,
    CREATE_TASKS_TABLE_SQL, # Tasks needed for player_quest_progress, player_records
    CREATE_ACHIEVEMENTS_TABLE_SQL, # Achievements needed for player_achievements
    CREATE_PET_SYSTEM_TABLE_SQL, # No dependencies listed, can be placed anywhere
    # Add Natures and Abilities tables if needed based on pokemon_instances FKs
    # CREATE_NATURES_TABLE_SQL = """..."""
    # CREATE_ABILITIES_TABLE_SQL = """..."""
]

# List of all table creation SQLs for game_record.db in dependency order
GAME_RECORD_TABLES_SQL = [
    CREATE_PLAYER_RECORDS_TABLE_SQL, # Players needed for most other tables
    CREATE_POKEMON_INSTANCES_TABLE_SQL, # Pokemon instances needed for player_repository, player_party
    CREATE_PLAYER_REPOSITORY_TABLE_SQL,
    CREATE_PLAYER_PARTY_TABLE_SQL,
    CREATE_PLAYER_QUEST_PROGRESS_TABLE_SQL,
    CREATE_PLAYER_ACHIEVEMENTS_TABLE_SQL,
    CREATE_FRIENDS_TABLE_SQL,
    CREATE_BATTLE_RECORDS_TABLE_SQL, # Depends on player_records, field_effects
]


async def create_tables() -> None:
    """
    Creates all necessary database tables if they do not exist.
    Connects to both game_main.db and game_record.db.
    """
    logger.info("Checking/Creating database tables...")

    # Create tables in game_main.db
    try:
        async with aiosqlite.connect(settings.MAIN_DATABASE_PATH) as db_connection:
            db_connection.row_factory = aiosqlite.Row # Optional: access columns by name
            cursor = await db_connection.cursor()
            for create_sql in GAME_MAIN_TABLES_SQL:
                await cursor.execute(create_sql)
            await db_connection.commit()
        logger.info(f"Database tables checked/created in {settings.MAIN_DATABASE_PATH}.")
    except Exception as e:
        logger.error(f"Error creating tables in {settings.MAIN_DATABASE_PATH}: {e}")
        # Depending on severity, you might want to re-raise or exit

    # Create tables in game_record.db
    try:
        async with aiosqlite.connect(settings.RECORD_DATABASE_PATH) as db_connection:
            db_connection.row_factory = aiosqlite.Row # Optional: access columns by name
            cursor = await db_connection.cursor()
            for create_sql in GAME_RECORD_TABLES_SQL:
                await cursor.execute(create_sql)
            await db_connection.commit()
        logger.info(f"Database tables checked/created in {settings.RECORD_DATABASE_PATH}.")
    except Exception as e:
        logger.error(f"Error creating tables in {settings.RECORD_DATABASE_PATH}: {e}")
        # Depending on severity, you might want to re-raise or exit


# Example usage:
# async def initialize():
#     await create_tables()
#     # await load_initial_data() # Call data loading script here
