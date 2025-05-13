# Scripts 目录

`backend/scripts/` 目录存放用于项目维护和初始化的一次性或周期性脚本。这些脚本通常不属于核心游戏逻辑，但在项目部署、更新或数据管理中扮演重要角色。

## 脚本列表

*   **`initialize_database.py`**:
    *   **职责**: 用于初始化游戏数据库。它会检查并创建 `game_main.db` 和 `game_record.db` 中的所有必要表，并加载游戏的初始元数据（如宝可梦种族、技能、道具、地图等）到 `game_main.db` 中。
    *   **使用方法**: 这个脚本可以在插件首次部署时运行，或者在数据库结构更新后运行（`CREATE TABLE IF NOT EXISTS` 语句会确保现有数据不会丢失）。通常可以通过命令行直接运行此脚本，或者在插件的启动流程中调用其 `initialize_database` 函数。
    *   **依赖**: 依赖于 `backend.data_access.schema` 定义的表结构和 `backend.data_access.repositories.metadata_repository` 中的数据保存方法。加载初始数据时，它会读取 `data/` 目录下的数据文件。

## 如何添加新的脚本

1.  在 `backend/scripts/` 目录下创建新的 Python 文件（例如 `migrate_data.py`）。
2.  编写脚本逻辑，确保遵循异步编程规范，并使用 `backend.utils.logger` 进行日志记录。
3.  如果脚本需要访问数据库或配置，请导入相应的模块 (`backend.data_access.db_manager`, `backend.config.settings` 等)。
4.  在 `WIKI/scripts.md` 中添加新脚本的描述、职责和使用方法。 