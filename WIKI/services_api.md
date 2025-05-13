# Services 层接口定义

本文档描述了 `services/` 模块的关键接口和与其他层的交互。Services 层负责编排 core 逻辑和 data_access 层，完成一个完整的用户操作。

## `services/player_service.py`

**职责:** 处理玩家相关的业务逻辑，如注册、查看信息、管理背包等。

**关键方法:** (示例)

### `get_player_info(player_id: str) -> Player | None`

*   **描述:** 获取指定玩家的信息。
*   **输入:**
    *   `player_id: str`: 玩家的唯一标识符。
*   **输出:**
    *   `Player | None`: 玩家模型对象 (来自 models 层)，如果玩家不存在则返回 `None`。
*   **调用关系:**
    *   被 `commands/command_handler.py` 调用。
    *   调用 `data_access/repositories/player_repository.py` 获取数据。

### `register_player(player_id: str, initial_data: dict) -> Player`

*   **描述:** 注册一个新玩家。
*   **输入:**
    *   `player_id: str`: 新玩家的唯一标识符。
    *   `initial_data: dict`: 玩家的初始数据（例如，起始地点，初始道具等）。
*   **输出:**
    *   `Player`: 新创建的玩家模型对象。
*   **调用关系:**
    *   被 `commands/command_handler.py` 调用。
    *   调用 `data_access/repositories/player_repository.py` 保存数据。

## `services/pokemon_service.py`

**职责:** 处理宝可梦相关的业务逻辑，如捕捉、升级、进化等。

**关键方法:** (示例)

### `catch_pokemon(player_id: str, location_id: str) -> CatchResult`

*   **描述:** 执行捕捉宝可梦的业务流程。
*   **输入:**
    *   `player_id: str`: 尝试捕捉的玩家 ID。
    *   `location_id: str`: 尝试捕捉的地点 ID。
*   **输出:**
    *   `CatchResult`: 捕捉结果对象（包含是否成功、遇到的宝可梦信息等）。
*   **调用关系:**
    *   被 `commands/command_handler.py` 调用。
    *   调用 `services/encounter_service.py` 尝试遭遇。
    *   调用 `data_access/repositories/metadata_repository.py` 获取宝可梦种类数据。
    *   调用 `core/battle/pokemon_factory.py` 创建宝可梦实例。
    *   调用 `data_access/repositories/pokemon_repository.py` 保存宝可梦实例。

## `services/battle_service.py`

**职责:** 组织宝可梦对战的业务流程。

**关键方法:** (示例)

### `start_pvp_battle(player1_id: str, player2_id: str) -> BattleSummary`

*   **描述:** 开始一场玩家对战。
*   **输入:**
    *   `player1_id: str`: 玩家 1 ID。
    *   `player2_id: str`: 玩家 2 ID。
*   **输出:**
    *   `BattleSummary`: 战斗总结信息。
*   **调用关系:**
    *   被 `commands/command_handler.py` 调用。
    *   调用 `data_access/repositories/player_repository.py` 获取玩家数据。
    *   调用 `data_access/repositories/pokemon_repository.py` 获取玩家的宝可梦数据。
    *   调用 `core/game_logic.py` 或 `core/battle/battle_logic.py` 执行核心战斗逻辑。
    *   调用 `data_access/repositories/battle_repository.py` 记录战斗结果。

## `services/data_init_service.py`

**职责:** 从初始数据文件加载数据并填充到数据库。

**关键方法:**

### `initialize_metadata() -> None`

*   **描述:** 读取 `data/` 目录下的 CSV/JSON 文件，并将元数据（宝可梦种类、技能、道具等）导入到数据库中。
*   **输入:** 无。
*   **输出:** 无。
*   **调用关系:**
    *   通常在插件启动时由 `main.py` 或一个初始化函数调用。
    *   调用 `data_access/repositories/metadata_repository.py` 保存数据。
    *   调用 `utils/txt_parser.py` (如果使用 TXT 文件)。 