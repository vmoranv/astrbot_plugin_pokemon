# Data Access 层接口定义

本文档描述了 `data_access/` 模块的关键接口和与其他层的交互。Data Access 层负责与数据库进行交互。

## `data_access/db_manager.py`

**职责:** 管理 SQLite 数据库连接，提供执行 SQL 查询的底层方法。

**关键方法:**

### `get_connection() -> sqlite3.Connection`

*   **描述:** 获取一个数据库连接。
*   **输入:** 无。
*   **输出:**
    *   `sqlite3.Connection`: 数据库连接对象。
*   **调用关系:**
    *   被 `data_access/repositories/` 中的方法调用。

### `close_connection(conn: sqlite3.Connection) -> None`

*   **描述:** 关闭一个数据库连接。
*   **输入:**
    *   `conn: sqlite3.Connection`: 需要关闭的连接对象。
*   **输出:** 无。
*   **调用关系:**
    *   被 `data_access/repositories/` 中的方法调用 (通常在使用完连接后)。

### `execute_query(sql: str, params: tuple = ()) -> sqlite3.Cursor`

*   **描述:** 执行一个 SQL 语句 (INSERT, UPDATE, DELETE)。
*   **输入:**
    *   `sql: str`: SQL 语句字符串。
    *   `params: tuple`: SQL 语句的参数。
*   **输出:**
    *   `sqlite3.Cursor`: 游标对象。
*   **调用关系:**
    *   被 `data_access/repositories/` 中的方法调用。

### `fetch_one(sql: str, params: tuple = ()) -> dict | None`

*   **描述:** 执行一个 SELECT 查询并返回单行结果。
*   **输入:**
    *   `sql: str`: SQL SELECT 语句字符串。
    *   `params: tuple`: SQL 语句的参数。
*   **输出:**
    *   `dict | None`: 查询结果的字典表示，如果没有找到则返回 `None`。
*   **调用关系:**
    *   被 `data_access/repositories/` 中的方法调用。

### `fetch_all(sql: str, params: tuple = ()) -> list[dict]`

*   **描述:** 执行一个 SELECT 查询并返回所有结果行。
*   **输入:**
    *   `sql: str`: SQL SELECT 语句字符串。
    *   `params: tuple`: SQL 语句的参数。
*   **输出:**
    *   `list[dict]`: 查询结果的字典列表，如果没有找到则返回空列表。
*   **调用关系:**
    *   被 `data_access/repositories/` 中的方法调用。

## `data_access/repositories/`

**职责:** 为每个核心实体提供一个仓库，封装所有与该实体相关的 SQL 查询和数据转换逻辑。

**关键方法:** (示例，具体方法根据实体和需求定义)

### `PlayerRepository`

*   `get_player_by_id(player_id: str) -> Player | None`
    *   输入: 玩家 ID (str)。
    *   输出: Player 模型对象或 None。
    *   调用 `db_manager.fetch_one`。
*   `save_player(player: Player) -> None`
    *   输入: Player 模型对象。
    *   输出: 无。
    *   调用 `db_manager.execute_query`。

### `PokemonRepository`

*   `get_pokemon_instance_by_id(pokemon_id: int) -> Pokemon | None`
    *   输入: 宝可梦实例 ID (int)。
    *   输出: Pokemon 模型对象或 None。
    *   调用 `db_manager.fetch_one`。
*   `get_player_pokemons(player_id: str) -> list[Pokemon]`
    *   输入: 玩家 ID (str)。
    *   输出: Pokemon 模型对象列表。
    *   调用 `db_manager.fetch_all`。
*   `save_pokemon_instance(pokemon: Pokemon) -> None`
    *   输入: Pokemon 模型对象。
    *   输出: 无。
    *   调用 `db_manager.execute_query`。

### `MetadataRepository`

*   `get_species_by_id(species_id: int) -> Species | None`
    *   输入: 宝可梦种类 ID (int)。
    *   输出: Species 模型对象或 None。
    *   调用 `db_manager.fetch_one`。
*   `save_species(species: Species) -> None`
    *   输入: Species 模型对象。
    *   输出: 无。
    *   调用 `db_manager.execute_query`。
*   `get_move_by_id(move_id: int) -> Move | None`
    *   输入: 技能 ID (int)。
    *   输出: Move 模型对象或 None。
    *   调用 `db_manager.fetch_one`。
*   `save_move(move: Move) -> None`
    *   输入: Move 模型对象。
    *   输出: 无。
    *   调用 `db_manager.execute_query`。

## `data_access/schema.py`

**职责:** 包含创建数据库表的 SQL DDL 语句和初始化函数。

**关键方法:**

### `create_tables(db_connection: sqlite3.Connection) -> None`

*   **描述:** 在给定的数据库连接上执行 SQL 语句以创建所有必要的表。
*   **输入:**
    *   `db_connection: sqlite3.Connection`: 数据库连接对象。
*   **输出:** 无。
*   **调用关系:**
    *   通常在插件首次加载或初始化时由 `main.py` 或一个初始化函数调用。 