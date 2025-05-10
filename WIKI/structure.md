# AstrBot 插件架构指南

本指南旨在为开发 AstrBot 插件提供架构建议和最佳实践。我们将从一个基础的插件模板开始，逐步介绍如何构建更复杂、可维护的插件。

## 核心组件与概念 (基于基础模板)

基于 AstrBot 提供的 API，基础插件模板会使用以下核心组件：

1.  **`Star` 类**: 所有 AstrBot 插件都需要继承自 `astrbot.api.star.Star` 类。这是插件与框架交互的基础。
    -   `__init__(self, context: Context)`: 插件实例化时调用，接收一个 `Context` 对象，用于访问框架提供的功能。
    -   `initialize(self)` (可选异步方法): 插件加载后调用，用于执行异步初始化任务。
    -   `terminate(self)` (可选异步方法): 插件卸载或停用时调用，用于执行清理任务。

2.  **`Context` 对象**: 在 `Star` 类的 `__init__` 方法中提供，包含插件运行所需的上下文信息和工具，例如访问日志记录器。

3.  **`@register` 装饰器**: 用于在 `main.py` 中注册你的插件类。它需要插件的唯一名称、作者、描述和版本信息。
    ```python
    # main.py
    from astrbot.api.star import Context, Star, register

    @register("your_plugin_name", "YourName", "你的插件描述", "1.0.0")
    class YourPlugin(Star):
        # ...
        pass
    ```

4.  **`AstrMessageEvent` 对象**: 当用户发送消息触发插件时，命令处理函数会接收到一个 `AstrMessageEvent` 对象。它包含了消息的详细信息，如发送者、消息内容等。

5.  **`@filter.command` 装饰器**: 用于在插件类中注册一个命令处理函数。当用户发送与指定命令匹配的消息时，该函数会被调用。
    ```python
    # main.py
    from astrbot.api.event import filter, AstrMessageEvent

    class YourPlugin(Star):
        # ...
        @filter.command("your_command_name")
        async def handle_your_command(self, event: AstrMessageEvent):
            """你的命令描述"""
            # 处理命令逻辑
            # ...
            yield event.plain_result("回复用户") # 发送回复
    ```

6.  **`MessageEventResult`**: 命令处理函数通过 `yield` 返回 `MessageEventResult` 对象（如 `event.plain_result()`）来向用户发送回复。

7.  **日志记录**: 使用 `astrbot.api.logger` 进行日志记录，方便调试和追踪插件运行状态。

## 构建复杂插件：分层架构建议

对于功能更复杂、代码量更大的插件，建议采用分层架构来提高代码的可维护性、可扩展性和可测试性。以下是一个基于分层架构的目录结构建议，以一个类宝可梦插件为例：

astrbot_pokemon_plugin/
├── main.py                     # 插件入口，AstrBot 交互，TXT 文件 I/O
├── metadata.yaml               # 插件元数据文件
├── _conf_schema.json           # 初始配置文件
├── commands/                   # 命令解析和分发
│   ├── __init__.py
│   └── command_handler.py      # 命令分发器
│   └── available_commands.py   # 定义可用命令及其参数结构
├── core/                       # 核心游戏逻辑
│   ├── __init__.py
│   ├── game_logic.py           # 主要逻辑入口
│   ├── battle/
│   │   ├── __init__.py
│   │   ├── battle_logic.py     # 战斗逻辑
│   │   ├── encounter_logic.py  # 遭遇逻辑
│   │   ├── formulas.py         # 伤害计算
│   │   ├── field_effect.py     # 场地效果
│   │   ├── status_effect.py    # 状态效果
│   ├── pet/
│   │   ├── __init__.py
│   │   ├── pet_skill.py        # 宠物技能
│   │   ├── pet_grow.py         # 宠物养成
│   │   ├── pet_catch.py        # 宠物捕捉
│   │   ├── pet_equipment.py    # 宠物装备
│   │   ├── pet_item.py         # 宠物道具
│   │   ├── pet_evolution.py    # 宠物进化
│   │   ├── pet_system.py       # 宠物系统
├── services/                   # 业务逻辑服务层 (编排核心逻辑和数据访问)
│   ├── __init__.py
│   ├── player_service.py       # 玩家服务
│   ├── battle_service.py       # 战斗服务
│   ├── pet_service.py          # 宠物服务
│   └── data_init_service.py    # 初始化/加载游戏元数据服务
├── data_access/                # 数据访问层
│   ├── __init__.py
│   ├── db_manager.py           # SQLite 连接和基本 CRUD 操作封装
│   ├── repositories/           # 仓库模式，针对每个实体进行数据操作
│   │   ├── __init__.py
│   │   ├── player_repository.py  # 玩家仓库
│   │   ├── pokemon_repository.py # 宝可梦仓库
│   │   └── metadata_repository.py # 元数据仓库
│   └── schema.py               # 数据库表结构定义和创建脚本
├── models/                     # 数据模型/实体定义
│   ├── __init__.py
│   ├── player.py               # 玩家
│   ├── pokemon.py              # 宝可梦实例
│   ├── race.py                 # 宝可梦种类/图鉴数据
│   ├── map.py                  # 地图
│   ├── dialog.py               # 对话
│   └── item.py                 # 道具
├── utils/                      # 通用工具类
│   ├── __init__.py
│   └── exceptions.py           # 自定义异常
├── config/                     # 配置
│   ├── __init__.py
│   └── settings.py             # 数据库路径、日志级别等
├── data/                       # 初始游戏数据 (例如 CSV, JSON)
│   ├── race.csv                # 宝可梦种类/图鉴数据
│   ├── skill.csv               # 宝可梦技能数据
│   ├── map.csv                 # 地图数据
│   ├── attribute.csv           # 克制表
│   ├── dialog.csv              # 对话数据
│   └── item.csv                # 道具数据
└── db/                         # SQLite 数据库文件存放目录 (由 .gitignore 排除)
    ├── game_main.db             #主数据库
    └── game_record.db           #运行记录数据库

**核心设计原则：**

1.  **分层架构 (Layered Architecture):** 将应用分为表现层（与 AstrBot 交互）、业务逻辑层（游戏核心功能）、数据访问层（与 SQLite 交互）。
2.  **模块化 (Modularity):** 每个模块负责一部分明确的功能。
3.  **依赖倒置原则 (Dependency Inversion Principle):** 高层模块不应该依赖于低层模块，两者都应该依赖于抽象。抽象不应该依赖于细节，细节应该依赖于抽象。这可以通过定义清晰的接口（即使在 Python 中是隐式的）来实现。
4.  **单一职责原则 (Single Responsibility Principle):** 每个类或模块应该有且只有一个改变的理由。
5.  **配置与代码分离:** 游戏配置（如数据库路径、初始数据文件路径等）应与代码分离。

**各模块详细说明:**

1.  **main.py (插件入口与 AstrBot 交互)**
    -   **职责:**
        -   接收 AstrBot 框架触发的事件 (`AstrMessageEvent`)。
        -   调用 commands.command_handler 分发事件到相应的处理逻辑。
        -   接收处理结果并使用 `yield` 返回 `MessageEventResult`。
        -   基本的错误捕获和响应。
    -   **耦合:** 低。只知道如何接收事件和调用命令处理器。

2.  **commands/ (命令处理)**
    -   **command_handler.py:**
        -   **职责:** 根据事件中的命令名称，分发到相应的服务层方法。它充当了表现层和业务逻辑层之间的协调者。
        -   **高内聚:** 专注于命令的分发和参数的初步校验。
        -   **低耦合:** 不包含具体业务逻辑，只调用 services。
    -   **available_commands.py:**
        -   **职责:** 定义插件支持的所有命令，以及每个命令期望的参数（名称、类型、是否必需）。这有助于参数校验和生成帮助信息。
        -   例如: `{'catch': {'params': ['location_id', 'player_id']}, 'battle': {'params': ['player_id', 'opponent_id']}}`

3.  **core/ (核心游戏逻辑)**
    -   **职责:** 实现不依赖于具体数据存储或外部框架的游戏核心规则和计算。
    -   **game_logic.py:** 包含如战斗流程控制、伤害计算调用、状态效果处理、进化条件判断等。
    -   **pokemon_factory.py:** 根据宝可梦种类数据 (Species) 和等级等信息，创建具体的宝可梦实例 (Pokemon)，包括计算属性、生成初始技能等。
    -   **formulas.py:** 存放所有游戏内的计算公式，如伤害、经验值、属性计算等。
    -   **高内聚:** 专注于游戏本身的规则。
    -   **极低耦合:** 理想情况下，这部分代码可以被用在不同的界面或存储后端。它操作的是 models 中的对象。

4.  **services/ (业务逻辑服务层)**
    -   **职责:** 编排 core 逻辑和 data_access 层，完成一个完整的用户操作。处理事务性操作（如果需要的话，SQLite 中简单事务）。
    -   **player_service.py:** 处理玩家注册、登录、查看背包、使用道具等。
    -   **pokemon_service.py:** 处理捕捉宝可梦、宝可梦升级、学习技能、进化等。
    -   **battle_service.py:** 组织战斗流程，调用 core.game_logic 进行战斗计算，更新宝可梦状态。
    -   **encounter_service.py:** 根据地点、玩家状态等生成遭遇的野生宝可梦。
    -   **data_init_service.py:** 从 data/ 目录下的 CSV/JSON 文件中读取宝可梦种类、技能、道具等元数据，并使用 data_access.metadata_repository 将它们存入数据库。通常在插件首次加载或特定命令下执行。
    -   **高内聚:** 每个服务类关注一个特定的业务领域。
    -   **低耦合:** 服务之间可能存在调用关系，但应尽量减少。它们依赖 data_access.repositories 获取和存储数据，并使用 core 模块执行纯逻辑计算。

5.  **data_access/ (数据访问层)**
    -   **db_manager.py:**
        -   **职责:** 管理 SQLite 数据库连接（获取连接、关闭连接）。提供执行 SQL 查询（execute_query, fetch_one, fetch_all）的底层方法。处理数据库连接的异常。
        -   **高内聚:** 专注于数据库的连接和基本操作。
    -   **repositories/:** (仓库模式)
        -   **职责:** 为每个核心实体 (Player, Pokemon 实例, Species 元数据等) 提供一个仓库。封装所有与该实体相关的 SQL 查询和数据转换逻辑（从数据库行到 models 对象，反之亦然）。
        -   例如, PokemonRepository 会有 `save_pokemon_instance(pokemon_model)`, `get_pokemon_instance_by_id(id)`, `get_player_pokemons(player_id)` 等方法。
        -   **高内聚:** 每个仓库只处理一种实体的数据持久化。
        -   **低耦合:** 服务层通过仓库接口与数据库交互，不知道具体的 SQL 实现。这使得更换数据库或修改表结构对服务层的影响降到最低。
    -   **schema.py:**
        -   **职责:** 包含创建所有数据库表的 SQL DDL 语句。提供一个函数，如 `create_tables(db_connection)`，用于在插件首次运行时初始化数据库结构。

6.  **models/ (数据模型)**
    -   **职责:** 定义游戏中的核心实体，如 Player, Pokemon, Species, Move, Item。这些通常是简单的 Python 类 (Plain Old Python Objects - POPOs)，主要用于封装数据。
    -   可以包含一些简单的验证逻辑或辅助方法（例如，计算宝可梦当前属性）。
    -   **高内聚:** 每个模型代表一个明确的业务实体。
    -   **低耦合:** 模型之间可以有关联（例如，Player 有一个 Pokemon 列表），但它们不包含复杂的业务逻辑。

7.  **utils/ (通用工具类)**
    -   **txt_parser.py:** (如果你的插件需要处理 TXT 文件输入/输出，例如与旧版 AstrBot 交互)
        -   **职责:**
            -   `parse_input(file_path)`: 读取指定 TXT 文件，将其内容解析为命令和参数字典。
            -   `format_output(data_dict, file_path)`: 将结果字典格式化并写入指定的 TXT 文件。
    -   **logger.py:** 配置和提供日志记录器实例，方便调试和追踪。建议封装 `astrbot.api.logger`。
    -   **exceptions.py:** 定义游戏中可能发生的自定义异常，如 `PokemonNotFoundException`, `InsufficientItemException`，方便上层捕获和处理。

8.  **config/ (配置)**
    -   **settings.py:**
        -   **职责:** 存储所有配置项，如数据库文件路径 (`DATABASE_PATH = 'db/pokemon_game.db'`)，日志级别，初始数据文件路径等。
        -   避免硬编码。

9.  **data/ (初始游戏数据)**
    -   **职责:** 存放宝可梦种类、技能、道具等的静态数据，通常为 CSV 或 JSON 格式。DataInitService 会读取这些文件来填充数据库。

## 工作流程示例 (捕捉宝可梦 - 基于分层架构):**

1.  **AstrBot:** 用户在聊天中输入 `/pokemon catch route_1`。AstrBot 插件框架调用你的插件，触发相应的命令处理函数。
2.  **main.py:**
    -   接收 `AstrMessageEvent` 对象。
    -   调用 `commands.command_handler.handle_command(event)`。
3.  **commands.command_handler.py:**
    -   根据 `event` 中的命令 (即 `catch_pokemon`)，查找对应的处理逻辑。
    -   调用 `services.pokemon_service.catch_pokemon(player_id=event.get_sender_id(), location='route_1')`。
4.  **services.pokemon_service.py (catch_pokemon 方法):**
    -   调用 `services.encounter_service.try_encounter(location)` 看看是否能遇到宝可梦。
    -   如果遇到，比如遇到一个 species_id = 25 (皮卡丘)。
    -   调用 `data_access.repositories.metadata_repository.get_species_by_id(25)` 获取皮卡丘的种类信息。
    -   调用 `core.pokemon_factory.create_pokemon_instance(species_data, level=5)` 创建一个新的皮卡丘实例。
    -   调用 `data_access.repositories.pokemon_repository.save_pokemon_instance(new_pikachu, player_id)` 将新宝可梦存入数据库并与玩家关联。
    -   返回成功信息和宝可梦数据。
5.  **commands.command_handler.py:**
    -   接收来自 service 的结果。
    -   将结果封装成适合回复用户的格式。
6.  **main.py:**
    -   接收来自 command_handler 的结果。
    -   使用 `yield event.plain_result(...)` 或其他 `MessageEventResult` 类型发送回复。
7.  **AstrBot:** 将消息回复给用户。

## 通用实践

-   **配置管理**: 将数据库路径、API 密钥、日志级别等配置项放在 `config/settings.py` 中，避免硬编码。
-   **日志记录**: 使用 `astrbot.api.logger` 或在其基础上封装自己的日志模块 (`utils/logger.py`)，记录关键操作和错误信息，方便调试。
-   **错误处理**: 定义自定义异常 (`utils/exceptions.py`)，并在各层中捕获和处理异常，向上层传递有意义的错误信息。在 `main.py` 或 command handler 中进行最终的错误捕获，并向用户返回友好的错误提示。
-   **使用 `.scratch` 目录**: 根据指示，可以使用项目根目录下的 `.scratch` 目录存放临时文件或工作数据，例如：
    ```python
    import os

    SCRATCH_DIR = '.scratch'
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    temp_file_path = os.path.join(SCRATCH_DIR, 'temp_data.json')
    ```
-   **依赖管理**: 使用 `requirements.txt` 文件列出插件所需的所有 Python 库，方便安装。
-   **测试**: 为核心逻辑 (core) 和服务层 (services) 编写单元测试，确保代码的正确性。

## 数据库表单设计

### `db/game_main.db`设计 ：

-   `pet_dictionary`        # 宠物字典表 (存储宝可梦种类/图鉴数据)
-   `pet_system`            # 宠物系统相关配置或全局数据表
-   `items`                 # 道具数据表
-   `maps`                  # 地图数据表
-   `status_effects`        # 状态效果数据表
-   `field_effects`         # 场地效果数据表
-   `encounters`            # 遭遇配置或记录表
-   `evolutions`            # 进化条件和结果数据表
-   `skills`                # 技能数据表
-   `dialogs`               # 对话数据表
-   `attributes`            # 属性克制表

### `db/game_record.db`设计 ：

-   `battle_records`        # 战斗记录表
-   `player_records`        # 玩家记录表
-   `player_storage`        # 玩家仓库/背包表

## 可扩展性与可维护性

采用分层架构和上述实践可以带来以下好处：

-   **清晰职责:** 每个模块/类功能单一，易于理解和修改。
-   **低耦合:** 修改一个模块不易意外破坏其他模块。
-   **易于测试:** 核心逻辑和服务层不依赖于 AstrBot 框架或数据库实现细节，更容易进行单元测试。
-   **可扩展:** 添加新功能时，可以在现有层中增加新的服务、仓库或核心逻辑，对现有代码影响较小。例如，添加交易功能可以创建 `TradingService` 和 `TradeRepository`。
-   **配置分离:** 方便在不同环境中部署和运行插件。