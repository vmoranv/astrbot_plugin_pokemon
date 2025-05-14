import aiosqlite
from typing import Optional, Any, List, Dict
from backend.config.settings import settings
from backend.utils.logger import get_logger
import contextlib # 导入 contextlib 模块

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
            # Depending on severity, you might want to re-raise or handle differently
            pass # For now, just log and continue

@contextlib.asynccontextmanager # 使用 asynccontextmanager 装饰器
async def get_db() -> aiosqlite.Connection:
    """
    Provide an asynchronous database connection as a context manager.
    Ensures the connection is properly handled within an async with block.
    """
    db = None
    try:
        db = await get_db_connection()
        yield db
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        # Depending on your error handling strategy, you might want to rollback
        # if db and not db.closed:
        #     await db.rollback()
        raise # Re-raise the exception after logging
    finally:
        # In this simple module-level connection approach, we don't close here
        # as the connection is intended to be reused.
        # For a connection pool or per-request connection, closing/releasing
        # the connection would happen here.
        pass # Keep the connection open for reuse in this simple model

async def execute_query(sql: str, params: tuple = ()) -> None:
    """
    Execute a non-SELECT query (INSERT, UPDATE, DELETE).
    """
    conn = await get_db_connection()
    try:
        await conn.execute(sql, params)
        await conn.commit() # Commit the transaction
        logger.debug(f"Executed query: {sql} with params {params}")
    except Exception as e:
        await conn.rollback() # Rollback on error
        logger.error(f"Error executing query: {sql} with params {params} - {e}")
        raise # Re-raise the exception

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

@contextlib.asynccontextmanager
async def get_cursor() -> aiosqlite.Cursor:
    """
    提供一个异步上下文管理器来获取数据库游标。

    使用方法:
        async with get_cursor() as cursor:
            await cursor.execute(...)
            await cursor.fetchall() # 或 fetchone(), executemany() 等
        # 游标在退出 with 块时自动关闭。
        # 连接的提交/回滚由上下文管理器处理。
        # 连接本身不在此处关闭，应由调用者管理。
    """
    conn = None
    cursor = None
    try:
        conn = await get_db_connection()
        cursor = await conn.cursor()
        yield cursor
        await conn.commit() # 默认提交事务
    except Exception as e:
        if conn:
            await conn.rollback() # 发生异常时回滚事务
        logger.error(f"Database operation failed: {e}", exc_info=True)
        raise # 重新抛出异常
    finally:
        if cursor:
            await cursor.close()
        if conn:
            await conn.close() # 保留此行以避免测试卡住

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