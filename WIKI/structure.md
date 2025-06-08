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
│   │   │   ├── events.py           # 战斗事件
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
│   │   ├── pet_system.py      # 宠物系统数据
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
        -   初始化插件和配置。
        -   注册 AstrBot 命令处理器。
        -   处理来自 AstrBot 的事件和消息。
        -   调用 `commands` 层处理用户命令。
        -   管理插件生命周期。
2.  **commands/ (命令解析和分发)**
    -   **职责:**
        -   解析用户输入的命令和参数。
        -   根据命令类型调用 `services` 层相应的业务逻辑。
        -   处理命令执行结果，生成用户友好的响应消息。
        -   `command_handler.py`: 负责命令的注册、解析和分发。
        -   `available_commands.py`: 定义所有可用命令的结构、参数和帮助信息。
3.  **core/ (核心游戏逻辑)**
    -   **职责:**
        -   包含纯粹的游戏规则和计算逻辑，不直接依赖数据库或外部框架。
        -   主要操作 `models` 层定义的数据结构。
        -   `game_logic.py`: 游戏主循环、状态管理等核心流程。
        -   `battle/`: 战斗系统的核心逻辑。
            -   `battle_logic.py`: 战斗回合处理、行动执行、事件发布。
            -   `encounter_logic.py`: 野生宝可梦遭遇、生成逻辑。
            -   `events.py`: 定义战斗中发生的各种事件类型。
            -   `formulas.py`: 各种游戏公式实现（伤害、命中、闪避、捕捉率等）。
            -   `field_effect.py`: 场地效果（天气、地形等）的逻辑处理。
            -   `status_effect.py`: 主要状态（中毒、麻痹等）和易变状态（混乱、畏缩等）的逻辑处理，包括状态的施加、移除、回合效果和免疫检查。
        -   `pet/`: 宝可梦个体相关的核心逻辑。
            -   `pet_skill.py`: 技能学习、遗忘、使用效果等。
            -   `pet_grow.py`: 经验获取、升级、能力值计算。
            -   `pet_catch.py`: 宝可梦捕捉过程逻辑。
            -   `pet_equipment.py`: 装备穿戴和效果。
            -   `pet_item.py`: 道具使用效果（非战斗）。
            -   `pet_evolution.py`: 宝可梦进化逻辑。
            -   `pet_system.py`: 宝可梦系统核心规则和交互。
        -   `pokemon_factory.py`: 根据种族数据创建具体的宝可梦实例。
4.  **services/ (业务逻辑服务层)**
    -   **职责:**
        -   协调 `core` 和 `data_access` 层，实现具体的业务流程。
        -   处理跨模块的复杂逻辑。
        -   提供给 `commands` 层调用的接口。
        -   `player_service.py`: 玩家注册、登录、数据存取等。
        -   `pokemon_service.py`: 宝可梦的获取、保存、队伍管理等。
        -   `item_service.py`: 物品的获取、使用、交易等。
        -   `map_service.py`: 地图切换、位置更新、地图事件触发等。
        -   `dialog_service.py`: 对话流程管理。
        -   `metadata_service.py`: 提供对元数据的便捷访问接口。
5.  **models/ (数据模型/实体定义)**
    -   **职责:**
        -   定义游戏中各种实体的数据结构。
        -   作为 `core` 和 `data_access` 层之间的数据载体。
        -   使用 Python 数据类 (`dataclasses`) 定义。
6.  **data_access/ (数据访问层)**
    -   **职责:**
        -   负责与 SQLite 数据库进行交互。
        -   实现数据的增、删、改、查操作。
        -   将数据库行映射到 `models` 层的数据结构，反之亦然。
        -   使用 `aiosqlite` 实现异步数据库操作。
        -   `db_manager.py`: 管理数据库连接池。
        -   `schema.py`: 定义数据库表结构并负责创建。
        -   `repositories/`: 实现仓库模式，为每个主要实体提供数据访问接口。
7.  **utils/ (通用工具类)**
    -   **职责:**
        -   提供项目中通用的辅助功能。
        -   `exceptions.py`: 定义自定义异常类。
        -   `constants.py`: 定义游戏中的常量和枚举值。
8.  **config/ (配置)**
    -   **职责:**
        -   加载和管理应用程序的配置设置。
        -   `settings.py`: 定义配置项（如数据库路径、日志级别、游戏参数等）。
9.  **data/ (初始游戏数据)**
    -   **职责:**
        -   存放游戏的初始配置数据，通常以 CSV 文件格式。
        -   这些数据在应用启动时加载到数据库中。
10. **scripts/ (脚本目录)**
    -   **职责:**
        -   存放用于数据加载、数据库迁移等一次性或维护性脚本。
        -   `load_initial_data.py`: 主加载脚本，调用其他加载脚本。
11. **db/ (SQLite 数据库文件存放目录)**
    -   **职责:**
        -   存放实际的 SQLite 数据库文件。
        -   应配置 `.gitignore` 忽略此目录下的文件。

**核心设计原则：**

1.  **分层架构 (Layered Architecture):** 将应用分为表现层（与 AstrBot 交互）、业务逻辑层（游戏核心功能）、数据访问层（与 SQLite 交互）。
2.  **模块化 (Modularity):** 每个模块负责一部分明确的功能。
3.  **依赖倒置原则 (Dependency Inversion Principle):** 高层模块不应该依赖于低层模块，两者都应该依赖于抽象。抽象不应该依赖于细节，细节应该依赖于抽象。这可以通过定义清晰的接口（即使在 Python 中是隐式的）来实现。
4.  **单一职责原则 (Single Responsibility Principle):** 每个类或模块应该有且只有一个改变的理由。
5.  **配置与代码分离:** 游戏配置（如数据库路径、初始数据文件路径等）应与代码分离。
6.  **数据加载与校验:** 初始数据加载应通过专门的脚本进行，并包含必要的数据校验逻辑。

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