# Data Access 层接口定义

本文档描述了 `data_access/` 模块的关键接口和与其他层的交互。Data Access 层负责与数据库进行交互，提供数据持久化和查询功能。它将数据库操作细节封装起来，供 Services 层调用。

## `data_access/` 目录结构

`data_access/` 目录下包含以下主要文件和子目录：

*   `db_manager.py`: 管理数据库连接和执行底层 SQL 操作。
*   `schema.py`: 包含数据库表结构的定义（DDL）。
*   `repositories/`: 包含各个实体或业务领域的数据仓库，封装了针对特定表的 CRUD (创建、读取、更新、删除) 操作。

## Data Access 模块职责

Data Access 模块的主要职责包括：

1.  **封装数据库操作:** 将底层的 SQL 语句或 ORM 操作封装在方法中。
2.  **提供数据持久化:** 负责将 Models 层的数据对象保存到数据库。
3.  **提供数据查询:** 负责从数据库查询数据，并转换为 Models 层的数据对象返回。
4.  **管理数据库连接:** `db_manager.py` 负责连接的获取和释放。
5.  **定义数据库结构:** `schema.py` 负责定义数据库表。

## 关键组件描述

### `data_access/db_manager.py`

*   **职责:** 管理 SQLite 数据库连接，提供执行 SQL 查询的底层方法。它是一个低级别的数据库工具模块。
*   **关键方法:** 提供获取连接、关闭连接、执行 SQL (INSERT, UPDATE, DELETE)、执行查询并获取单行结果、执行查询并获取多行结果等方法。
*   **关键交互:** 被 `data_access/repositories/` 中的方法调用。

### `data_access/repositories/`

*   **职责:** 包含各个实体或业务领域的数据仓库（Repository）。每个 Repository 封装了针对一个或多个相关数据库表的 CRUD 操作，将底层数据库操作转换为针对 Models 层对象的持久化操作。
*   **关键文件:** 例如 `player_repository.py`, `pokemon_repository.py`, `metadata_repository.py` 等。
*   **关键方法:** 每个 Repository 会定义针对其管理的数据模型的 CRUD 方法，例如 `get_player_by_id`, `save_pokemon_instance`, `get_species_by_id` 等。这些方法内部会调用 `db_manager.py` 来执行实际的 SQL 操作。
*   **关键交互:** 被 `services/` 层调用。调用 `db_manager.py`。操作 `models/` 中的数据对象。

### `data_access/schema.py`

*   **职责:** 定义数据库表。

## 接口定义 / 关键交互

*   **被调用:** 主要被 `services/` 层中的服务方法调用。
*   **调用:** `repositories/` 调用 `db_manager.py`。`schema.py` 在初始化时被调用。
*   **依赖:** 依赖于 `models/` 模块（Repositories 方法的输入和输出通常是 Models 对象）。

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
