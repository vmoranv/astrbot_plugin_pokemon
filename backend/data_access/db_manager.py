import aiosqlite
from typing import Optional, Any, List, Dict
from backend.config.settings import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Use a simple connection pool or manage connections per request/transaction
# For MVP, a simple approach might suffice, but a pool is better for concurrency.
# Let's use a simple module-level connection for now, but note this is not ideal for concurrent access.
# A better approach would be to pass connection/cursor or use a context manager.

# Using a simple connection for MVP, will need refinement for concurrent use
_db_connection: Optional[aiosqlite.Connection] = None

async def get_db_connection() -> aiosqlite.Connection:
    """
    Get an asynchronous database connection.
    Creates a new connection if one does not exist.
    """
    global _db_connection
    if _db_connection is None:
        try:
            # Use row_factory to get dictionary-like results
            _db_connection = await aiosqlite.connect(settings.MAIN_DATABASE_PATH)
            _db_connection.row_factory = aiosqlite.Row # Results can be accessed like dicts
            logger.info(f"Database connection established to {settings.MAIN_DATABASE_PATH}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    return _db_connection

async def close_db_connection() -> None:
    """
    Close the database connection if it exists.
    """
    global _db_connection
    if _db_connection is not None:
        try:
            await _db_connection.close()
            _db_connection = None
            logger.info("Database connection closed.")
        except Exception as e:
            logger.error(f"Failed to close database connection: {e}")
            # Depending on severity, you might re-raise or just log

async def execute_query(sql: str, params: tuple = ()) -> aiosqlite.Cursor:
    """
    Execute an SQL query (INSERT, UPDATE, DELETE).
    Commits the transaction.
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(sql, params)
        await conn.commit()
        logger.debug(f"Executed query: {sql} with params {params}")
        return cursor
    except Exception as e:
        logger.error(f"Error executing query: {sql} with params {params} - {e}")
        await conn.rollback() # Rollback on error
        raise

async def fetch_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """
    Execute a SELECT query and return a single row as a dictionary.
    """
    conn = await get_db_connection()
    try:
        conn.row_factory = aiosqlite.Row # Ensure row_factory is set
        cursor = await conn.execute(sql, params)
        row = await cursor.fetchone()
        logger.debug(f"Fetched one: {sql} with params {params}")
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching one: {sql} with params {params} - {e}")
        raise

async def fetch_all(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Execute a SELECT query and return all rows as a list of dictionaries.
    """
    conn = await get_db_connection()
    try:
        conn.row_factory = aiosqlite.Row # Ensure row_factory is set
        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()
        logger.debug(f"Fetched all: {sql} with params {params}")
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching all: {sql} with params {params} - {e}")
        raise

# Note: For a robust application, consider using a context manager for connections
# or passing the connection/cursor explicitly to repository methods.
# Example context manager approach:
# async def get_cursor():
#     conn = await get_db_connection()
#     return await conn.cursor()
#
# async with get_cursor() as cursor:
#     await cursor.execute(...)
#     await conn.commit() 