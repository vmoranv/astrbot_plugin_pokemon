# Services 层接口定义

本文档描述了 `services/` 模块的关键接口和与其他层的交互。Services 层是业务逻辑服务层，负责编排 `core` 逻辑和 `data_access` 层，以完成一个完整的用户操作或业务流程。每个服务通常专注于一个特定的业务领域。

## `services/` 目录结构

`services/` 目录下包含多个服务文件，每个文件对应一个业务领域：

*   `player_service.py`: 处理玩家相关的业务逻辑（创建玩家、获取玩家信息、更新玩家状态等）。
*   `pokemon_service.py`: 处理宝可梦相关的业务逻辑（捕捉宝可梦、管理宝可梦队伍和仓库、宝可梦信息查询等）。
*   `item_service.py`: 处理道具相关的业务逻辑（使用道具、管理玩家背包、商店购买等）。
*   `map_service.py`: 处理地图相关的业务逻辑（玩家移动、地图信息查询、遇敌逻辑等）。
*   `dialog_service.py`: 处理对话相关的业务逻辑（触发对话、处理对话选项等）。
*   `metadata_service.py`: 处理静态元数据的读取和提供（从数据库加载宝可梦种类、技能、道具等信息）。

## 服务职责

每个服务文件的主要职责包括：

1.  **接收请求:** 接收来自 `commands/` 层或其他服务的请求，这些请求代表一个用户操作或业务流程的开始。
2.  **编排逻辑:** 调用 `core/` 模块中的纯游戏逻辑函数和 `data_access/repositories/` 中的数据持久化方法，按照业务规则完成整个流程。
3.  **处理事务:** 如果一个业务流程涉及多个数据操作，服务层负责管理数据库事务，确保数据的一致性。
4.  **返回结果:** 将业务处理的结果返回给调用者（通常是 `commands/` 层）。
5.  **异常处理:** 捕获 `data_access` 或 `core` 层可能抛出的异常，并转换为服务层或更上层可以理解和处理的异常类型（通常是 `utils/exceptions.py` 中定义的自定义异常）。

## 接口定义 / 关键交互

*   **被调用:** 主要被 `commands/command_handler.py` 调用，也可能被其他服务调用（例如，`battle_service` 可能调用 `pokemon_service` 来获取宝可梦信息）。
*   **调用:** 调用 `core/` 模块中的纯游戏逻辑函数（例如 `core.battle.battle_logic`）和 `data_access/repositories/` 中的数据持久化方法（例如 `data_access.repositories.player_repository.save_player`）。
*   **依赖:** 依赖于 `core/` 模块、`data_access/` 模块和 `models/` 模块。 