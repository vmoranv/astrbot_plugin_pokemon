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
│   │   ├── pokemon_factory.py      # 宝可梦工厂
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
│   │   ├── pet_dictionary.py       # 宠物字典
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
│   │   │   ├── pet_dictionary_repository.py # 宠物字典仓库
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
    -   **职责:** 包含纯游戏逻辑和计算，不依赖于数据持久化或外部框架。操作 `models` 中的数据对象。
    -   **高内聚:** 专注于游戏核心规则和计算。
    -   **低耦合:** 不直接与 `data_access` 或外部系统交互。
    -   **game_logic.py:**
        -   **职责:** 协调和组织跨多个服务或核心逻辑模块的游戏流程。例如，一个复杂任务的完成可能需要调用玩家服务、物品服务和对话服务，`game_logic.py` 负责按顺序调用这些服务并处理它们之间的逻辑。
        -   **关键交互:** 被 `services/` 层调用，调用 `services/` 层中的方法。
    -   **battle/:**
        -   **职责:** 实现所有战斗相关的纯逻辑计算和规则实现。
        -   **关键文件:**
            *   `battle_logic.py`: 核心战斗回合逻辑和流程。
            *   `encounter_logic.py`: 决定在特定地点是否遭遇宝可梦以及遭遇何种宝可梦的逻辑。
            *   `formulas.py`: 存放各种战斗相关的计算公式（伤害、命中、暴击等）。
            *   `field_effect.py`: 场地效果的具体逻辑实现。
            *   `status_effect.py`: 状态效果的具体逻辑实现。
        -   **关键交互:** 被 `services/pokemon_service.py` (用于捕捉/遭遇) 和可能的 `services/battle_service.py` (如果存在) 调用。操作 `models/` 中的宝可梦、技能、状态等对象。
    -   **pet/:**
        -   **职责:** 实现所有与宝可梦个体相关的逻辑，例如技能学习、经验值计算、升级、进化条件判断、捕捉成功率计算、道具对宝可梦的影响等。
        -   **关键文件:**
            *   `pet_skill.py`: 宝可梦技能的学习、遗忘、使用逻辑。
            *   `pet_grow.py`: 经验值计算、升级、属性成长逻辑。
            *   `pet_catch.py`: 宝可梦捕捉成功率计算逻辑。
            *   `pet_equipment.py`: 宠物装备
            *   `pet_item.py`: 道具对宝可梦的影响逻辑。
            *   `pet_evolution.py`: 宝可梦进化条件判断和进化逻辑。
            *   `pet_system.py`: 宝可梦系统的通用逻辑。
        -   **关键交互:** 被 `services/pokemon_service.py` 和 `services/item_service.py` 调用。操作 `models/` 中的宝可梦、道具等对象。
    -   **pokemon_factory.py:**
        -   **职责:** 根据宝可梦种类元数据和其他参数（如等级、性格等）创建具体的宝可梦实例 (`models.Pokemon` 对象)。
        -   **关键交互:** 被 `services/pokemon_service.py` (在捕捉或生成宝可梦时) 调用。依赖 `metadata_service` 获取宝可梦种类数据。
    -   **[接口定义详情请参阅 WIKI/core_api.md]**

4.  **services/ (业务逻辑服务层)**
    -   **职责:** 包含具体的业务流程逻辑，编排 `core` 和 `data_access` 层的调用。
    -   **高内聚:** 每个服务专注于一个特定的业务领域（玩家、宝可梦、物品等）。
    -   **低耦合:** 不直接与 `commands` 或 `main` 交互，通过接口与 `core` 和 `data_access` 交互。
    -   **player_service.py:** 处理玩家相关的业务逻辑（创建玩家、获取玩家信息等）。
    -   **pokemon_service.py:** 处理宝可梦相关的业务逻辑（捕捉、战斗、管理宝可梦等）。
    -   **item_service.py:** 处理物品相关的业务逻辑（使用物品、管理背包等）。
    -   **map_service.py:** 处理地图相关的业务逻辑（移动、遇敌等）。
    -   **dialog_service.py:** 处理对话相关的业务逻辑。
    -   **metadata_service.py:** 负责加载和提供游戏元数据（宝可梦种类、技能、道具属性等）。它可能从数据库或静态文件中加载数据，并提供给其他服务和 Core 层使用。
    -   **[接口定义详情请参阅 WIKI/services_api.md]**

5.  **models/ (数据模型/实体定义)**
    -   **职责:** 定义游戏中的各种数据结构（宝可梦、玩家、物品、技能等）。这些是纯数据对象，不包含业务逻辑。
    -   **高内聚:** 每个模型定义一个特定的实体的数据结构。
    -   **低耦合:** 不依赖于其他层，只被其他层使用。
    -   **[接口定义详情请参阅 WIKI/models_api.md]**

6.  **data_access/ (数据访问层)**
    -   **职责:** 负责与数据库进行交互，执行数据的增删改查操作，并将数据库行映射到 `models` 对象，反之亦然。
    -   **高内聚:** 专注于数据库操作。
    -   **低耦合:** 不包含业务逻辑，只被 `services` 层调用。
    -   **db_manager.py:** 负责数据库连接的管理。
    -   **schema.py:** 定义数据库表结构和创建脚本。
    -   **repositories/:** 实现仓库模式，为每个主要实体提供数据访问接口。
        -   **player_repository.py:** 玩家数据访问。
        -   **pet_dictionary_repository.py:** 宝可梦图鉴数据访问。
        -   **pokemon_repository.py:** 宝可梦实例数据访问。
    -   **[接口定义详情请参阅 WIKI/data_access_api.md]**

7.  **utils/ (通用工具类)**
    -   **职责:** 存放各种通用的工具函数和类，不属于特定业务领域。
    -   **高内聚:** 每个工具类或函数专注于一个特定的通用任务。
    -   **低耦合:** 不依赖于其他业务层。
    -   **exceptions.py:** 自定义异常类。
    -   **constants.py:** 游戏常量和枚举定义。
    -   **[接口定义详情请参阅 WIKI/utils_api.md]**

8.  **config/ (配置)**
    -   **职责:** 存放应用的配置信息。
    -   **settings.py:** 具体的配置项（数据库路径、日志级别等）。
    -   **[接口定义详情请参阅 WIKI/config_api.md]**

9.  **data/ (初始游戏数据)**
    -   **职责:** 存放用于初始化数据库的原始游戏数据文件（如 CSV）。
    -   **[数据文件格式详情请参阅 WIKI/data_format.md]**

10. **scripts/ (脚本目录)**
    -   **职责:** 存放用于执行一次性任务或维护任务的脚本，例如数据库初始化和数据加载。
    -   **load_initial_data.py:** 主数据加载脚本，协调调用其他加载脚本。

11. **db/ (数据库文件存放目录)**
    -   存放实际的 SQLite 数据库文件。此目录应被版本控制忽略 (`.gitignore`)。

**开发流程建议:**

1.  **定义 Models:** 首先定义游戏中的各种数据模型。
2.  **设计 Database Schema:** 根据 Models 设计数据库表结构，并编写 `schema.py`。
3.  **实现 Data Access:** 实现 Repositories，完成数据的基本 CRUD 操作。
4.  **实现 Core Logic:** 实现纯游戏逻辑和计算函数，操作 Models 对象。
5.  **实现 Services:** 编写业务逻辑服务，编排 Core 和 Data Access 的调用。
6.  **实现 Commands:** 定义可用命令，并编写命令处理器调用 Services。
7.  **实现 Main:** 编写插件入口，处理 AstrBot 事件，调用 Commands，并进行初始化。
8.  **编写 Scripts:** 编写数据加载等维护脚本。
9.  **编写 Tests:** 为各层编写单元测试和集成测试。
10. **完善 Documentation:** 实时更新 WIKI 文档。

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