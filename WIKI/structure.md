# AstrBot 插件架构指南

本指南旨在为开发 AstrBot 插件提供架构建议和最佳实践。我们将从一个基础的插件模板开始，逐步介绍如何构建更复杂、可维护的插件。

## 分层架构

astrbot_pokemon_plugin/
├── main.py                     # 插件入口，AstrBot 交互
├── metadata.yaml               # 插件元数据文件
├── _conf_schema.json           # 初始配置文件
├── backend/
│   ├── commands/                   # 命令解析和分发
│   │   ├── __init__.py
│   │   └── command_handler.py      # 命令分发器
│   │   └── available_commands.py   # 定义可用命令及其参数结构
│   ├── core/                       # 核心游戏逻辑
│   │   ├── __init__.py
│   │   ├── game_logic.py           # 主要逻辑入口
│   │   ├── battle/
│   │   │   ├── __init__.py
│   │   │   ├── battle_logic.py     # 战斗逻辑
│   │   │   ├── encounter_logic.py  # 遭遇逻辑
│   │   │   ├── formulas.py         # 伤害计算
│   │   │   ├── field_effect.py     # 场地效果
│   │   │   └── status_effect.py    # 状态效果
│   │   ├── pet/
│   │   │   ├── __init__.py
│   │   │   ├── pet_skill.py        # 宠物技能
│   │   │   ├── pet_grow.py         # 宠物养成
│   │   │   ├── pet_catch.py        # 宠物捕捉
│   │   │   ├── pet_equipment.py    # 宠物装备
│   │   │   ├── pet_item.py         # 宠物道具
│   │   │   ├── pet_evolution.py    # 宠物进化
│   │   │   └── pet_system.py       # 宠物系统
│   │   └── services/               # 业务逻辑服务层
│   │       ├── __init__.py
│   │       ├── player_service.py   # 玩家服务
│   │       ├── pokemon_service.py  # 宝可梦服务
│   │       ├── item_service.py     # 物品服务
│   │       ├── map_service.py      # 地图服务
│   │       ├── dialog_service.py   # 对话服务
│   │       └── metadata_service.py # 元数据服务
│   ├── models/                     # 数据模型/实体定义
│   │   ├── __init__.py
│   │   ├── attribute.py            # 属性
│   │   ├── achievement.py          # 成就
│   │   ├── dialog.py               # 对话
│   │   ├── event.py                # 事件
│   │   ├── field_effect.py         # 场地效果
│   │   ├── map.py                  # 地图
│   │   ├── npc.py                  # NPC
│   │   ├── player.py               # 玩家
│   │   ├── pet_learnable_skill.py  # 宠物可学习技能
│   │   ├── pet_system_data.py      # 宠物系统数据
│   │   ├── pokemon.py              # 宝可梦实例
│   │   ├── shop.py                 # 商店
│   │   ├── status_effect.py        # 状态效果
│   │   ├── task.py                 # 任务
│   │   └── item.py                 # 道具
│   ├── data_access/                # 数据访问层
│   │   ├── __init__.py
│   │   ├── db_manager.py           # 数据库管理
│   │   ├── schema.py               # 数据库表单创建
│   │   ├── repositories/           # 仓库模式
│   │   │   ├── __init__.py
│   │   │   ├── player_repository.py # 玩家仓库
│   │   │   └── pokemon_repository.py # 宝可梦仓库
│   ├── utils/                      # 通用工具类
│   │   ├── __init__.py
│   │   ├── exceptions.py           # 自定义异常
│   │   └── constants.py            # 游戏常量和枚举定义
│   ├── config/                     # 配置
│   │   ├── __init__.py
│   │   └── settings.py             # 数据库路径、日志级别等
│   ├── data/                       # 初始游戏数据
│   │   ├── pet_dictionary.csv      # 宠物字典
│   │   ├── pet_system.csv          # 宠物系统
│   │   ├── attributes.csv          # 属性
│   │   ├── status_effects.csv      # 状态效果
│   │   ├── pet_learnable_skills.csv # 宠物可学习技能
│   │   ├── field_effects.csv       # 场地效果
│   │   ├── events.csv              # 事件
│   │   ├── npcs.csv                # NPC
│   │   ├── skills.csv              # 技能
│   │   ├── maps.csv                # 地图
│   │   ├── dialogs.csv             # 对话
│   │   ├── tasks.csv               # 任务
│   │   ├── achievements.csv        # 成就
│   │   ├── shops.csv               # 商店
│   │   └── items.csv               # 道具
│   ├── scripts/                    # 脚本目录
│   │   ├── __init__.py
│   │   ├── load_pet_dictionary.py  # 加载宠物字典
│   │   ├── load_pet_system.py      # 加载宠物系统
│   │   ├── load_attributes.py      # 加载属性
│   │   ├── load_status_effects.py  # 加载状态效果
│   │   ├── load_pet_learnable_skills.py # 加载宠物可学习技能
│   │   ├── load_field_effects.py    # 加载场地效果
│   │   ├── load_events.py          # 加载事件  
│   │   ├── load_npcs.py            # 加载NPC
│   │   ├── load_skills.py          # 加载技能
│   │   ├── load_maps.py            # 加载地图
│   │   ├── load_dialogs.py         # 加载对话
│   │   ├── load_tasks.py           # 加载任务
│   │   ├── load_achievements.py   # 加载成就
│   │   ├── load_shops.py           # 加载商店
│   │   ├── load_items.py           # 加载道具
│   │   └── load_initial_data.py    # 从 CSV 文件加载初始数据到数据库的脚本
│   └── db/                         # SQLite 数据库文件存放目录 (由 .gitignore 排除)
│       ├── game_main.db            #主数据库
│       └── game_record.db          #运行记录数据库

**核心设计原则：**

1.  **分层架构 (Layered Architecture):** 将应用分为表现层（与 AstrBot 交互）、业务逻辑层（游戏核心功能）、数据访问层（与 SQLite 交互）。
2.  **模块化 (Modularity):** 每个模块负责一部分明确的功能。
3.  **依赖倒置原则 (Dependency Inversion Principle):** 高层模块不应该依赖于低层模块，两者都应该依赖于抽象。抽象不应该依赖于细节，细节应该依赖于抽象。这可以通过定义清晰的接口（即使在 Python 中是隐式的）来实现。
4.  **单一职责原则 (Single Responsibility Principle):** 每个类或模块应该有且只有一个改变的理由。
5.  **配置与代码分离:** 游戏配置（如数据库路径、初始数据文件路径等）应与代码分离。
6.  **数据加载与校验:** 初始数据加载应通过专门的脚本进行，并包含必要的数据校验逻辑。

**各模块详细说明:**

1.  **main.py (插件入口与 AstrBot 交互)**
    -   **职责:**
        -   接收 AstrBot 框架触发的事件 (`AstrMessageEvent`)。
        -   调用 commands.command_handler 分发事件到相应的处理逻辑。
        -   接收处理结果并使用 `yield` 返回 `MessageEventResult`。
        -   基本的错误捕获和响应。
        -   插件初始化时，负责调用数据库创建和初始数据加载脚本。
    -   **耦合:** 低。只知道如何接收事件和调用命令处理器，以及进行初始化设置。
    -   **[接口定义详情请参阅 WIKI/main_api.md]**

2.  **commands/ (命令处理)**
    -   **command_handler.py:**
        -   **职责:** 根据事件中的命令名称，分发到相应的服务层方法。它充当了表现层和业务逻辑层之间的协调者。
        -   **高内聚:** 专注于命令的分发和参数的初步校验。
        -   **低耦合:** 不包含具体业务逻辑，只调用 services。
    -   **available_commands.py:**
        -   **职责:** 定义插件支持的所有命令，以及每个命令期望的参数（名称、类型、是否必需）。这有助于参数校验和生成帮助信息。
        -   例如: `{'catch': {'params': ['location_id', 'player_id']}, 'battle': {'params': ['player_id', 'opponent_id']}}`
    -   **[接口定义详情请参阅 WIKI/commands_api.md]**

3.  **core/ (核心游戏逻辑)**
    -   **职责:** 实现不依赖于具体数据存储或外部框架的游戏核心规则和计算。操作 models 中的对象，并被 services 层调用。
    -   **game_logic.py:** 游戏流程协调器，编排服务调用以完成复杂的游戏流程（如战斗、捕捉）。
    -   **pokemon_factory.py:** 根据宝可梦种类数据 (Species) 和等级等信息，创建具体的宝可梦实例 (Pokemon)，包括计算属性、生成初始技能等。
    -   **formulas.py:** 存放所有游戏内的计算公式，如伤害、经验值、属性计算等。
    -   **高内聚:** 专注于游戏本身的规则和流程编排。
    -   **极低耦合:** 理想情况下，这部分代码可以被用在不同的界面或存储后端。它操作的是 models 中的对象。
    -   **[接口定义详情请参阅 WIKI/core_api.md]**
    -   **[计算公式详情请参阅 WIKI/formulas.md]**

4.  **services/ (业务逻辑服务层)**
    -   **职责:** 编排 core 逻辑和 data_access 层，完成一个完整的用户操作或业务流程。
    -   例如，`PokemonService` 可能包含 `catch_pokemon(player_id, location_id)` 方法，该方法会调用 `core.encounter_logic` 判断是否遭遇，调用 `data_access.repositories` 保存宝可梦，并调用 `core.pokemon_factory` 创建宝可梦实例。
    -   **高内聚:** 每个服务专注于一个业务领域（如玩家服务、宝可梦服务、战斗服务）。
    -   **中等耦合:** 依赖于 core 和 data_access 层，但不依赖于 commands 或 main。
    -   **[接口定义详情请参阅 WIKI/services_api.md]**

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
    -   **[接口定义详情请参阅 WIKI/data_access_api.md]**

6.  **models/ (数据模型)**
    -   **职责:** 定义游戏中的核心实体，如 Player, Pokemon, Species, Move, Item。这些通常是简单的 Python 类 (Plain Old Python Objects - POPOs)，主要用于封装数据。
    -   可以包含一些简单的验证逻辑或辅助方法（例如，计算宝可梦当前属性）。
    -   **高内聚:** 每个模型代表一个明确的业务实体。
    -   **低耦合:** 模型之间可以有关联（例如，Player 有一个 Pokemon 列表），但它们不包含复杂的业务逻辑。
    -   **[接口定义详情请参阅 WIKI/models_api.md]**

7.  **utils/ (通用工具类)**
    -   **logger.py:** 配置和提供日志记录器实例，方便调试和追踪。建议封装 `astrbot.api.logger`。
    -   **exceptions.py:** 定义游戏中可能发生的自定义异常，如 `PokemonNotFoundException`, `InsufficientItemException`，方便上层捕获和处理。
    -   **[接口定义详情请参阅 WIKI/utils_api.md]**

8.  **config/ (配置)**
    -   **settings.py:**
        -   **职责:** 存储所有配置项，如数据库文件路径 (`DATABASE_PATH = 'db/game_main.db'`)，日志级别，初始数据文件路径等。
        -   避免硬编码。
    -   **[接口定义详情请参阅 WIKI/config_api.md]**

9.  **data/ (初始游戏数据)**
    -   **职责:** 存放宝可梦种类、技能、道具等的静态数据，通常为 CSV 或 JSON 格式。DataInitService 会读取这些文件来填充数据库。
    -   **耦合:** 低。只被 DataInitService 读取。

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

## 数据库表单设计

**[数据库表单设计详情请参阅 WIKI/database_schema.md]**

**[数据处理流程详情请参阅 WIKI/pipeline.md]**

## 可扩展性与可维护性

采用分层架构和上述实践可以带来以下好处：

-   **清晰职责:** 每个模块/类功能单一，易于理解和修改。
-   **低耦合:** 修改一个模块不易意外破坏其他模块。
-   **易于测试:** 核心逻辑和服务层不依赖于 AstrBot 框架或数据库实现细节，更容易进行单元测试。
-   **可扩展:** 添加新功能时，可以在现有层中增加新的服务、仓库或核心逻辑，对现有代码影响较小。例如，添加交易功能可以创建 `TradingService` 和 `TradeRepository`。
-   **配置分离:** 方便在不同环境中部署和运行插件。