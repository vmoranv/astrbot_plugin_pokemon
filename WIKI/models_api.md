# Models 层接口定义

本文档描述了 `models/` 模块的关键接口。Models 层定义了游戏中的核心数据结构或实体，它们是游戏状态和数据的抽象表示。

## `models/` 目录结构

`models/` 目录下包含多个文件，每个文件定义一个或一组相关的数据模型类：

*   `player.py`: 定义玩家数据模型。
*   `pokemon.py`: 定义宝可梦实例数据模型（玩家拥有的具体宝可梦）。
*   `race.py`: 定义宝可梦种类（图鉴）数据模型。
*   `map.py`: 定义地图数据模型。
*   `dialog.py`: 定义对话数据模型。
*   `item.py`: 定义道具数据模型。
*   其他文件: 根据游戏需求可能包含其他模型，例如 `skill.py`, `status_effect.py`, `field_effect.py`, `task.py`, `achievement.py`, `shop.py`, `npc.py` 等。

## Models 模块职责

Models 模块的主要职责包括：

1.  **定义数据结构:** 使用 Python 类来定义游戏中的各种实体及其属性。
2.  **数据封装:** 将相关数据封装在一个对象中，提供属性访问。
3.  **数据转换:** 可能包含从数据库行或外部数据源（如 CSV）转换为模型对象，以及将模型对象转换为适合存储或传输的格式的方法（例如，`from_db_row`, `to_dict`）。
4.  **基本数据操作:** 可能包含一些基本的数据操作方法，例如宝可梦等级提升、属性计算（调用 `formulas` 模块）、状态效果管理等，但应避免复杂的业务逻辑。

## 关键数据模型 (示例性描述，具体属性和方法根据模型定义)

### `Player`

*   **描述:** 代表一个玩家的数据。
*   **关键属性:** `player_id` (唯一标识符), `name`, `location_id` (当前地图), `money`, `inventory` (道具列表), `pokemon_party` (当前队伍), `pokemon_box` (仓库), `tasks` (任务进度), `achievements` (成就)。
*   **关键方法:** 可能包含添加/移除道具、添加/移除宝可梦到队伍/仓库等方法。

### `Pokemon`

*   **描述:** 代表玩家拥有的一个具体的宝可梦实例。
*   **关键属性:** `pokemon_id` (唯一实例 ID), `race_id` (宝可梦种类 ID), `owner_id` (玩家 ID), `nickname`, `level`, `current_hp`, `max_hp`, `attack`, `defense`, `special_attack`, `special_defense`, `speed`, `skills` (当前技能列表), `status_effects` (当前状态效果), `experience`, `nature_id`, `ability_id`, `individual_values` (个体值), `effort_values` (努力值)。
*   **关键方法:** 可能包含计算当前属性值（调用 `formulas`）、学习/遗忘技能、应用/移除状态效果、经验值增加、升级、进化检查等方法。

### `Race`

*   **描述:** 代表一种宝可梦的种类数据（图鉴信息）。
*   **关键属性:** `race_id` (种类 ID), `name`, `type1_id`, `type2_id`, `base_stats` (基础属性), `abilities` (可能的能力), `learnable_skills` (可学习技能列表), `evolution_chain` (进化链信息)。
*   **关键方法:** 通常是数据容器，方法较少。

## 接口定义 / 关键交互

*   **被调用:** 被 `core/` 模块和 `services/` 层调用，用于创建、读取和操作游戏数据。
*   **调用:** Models 中的方法可能会调用 `core/battle/formulas.py` 进行数值计算。
*   **依赖:** 可能依赖于 `utils/constants.py` (例如，属性类型、状态效果 ID)。 