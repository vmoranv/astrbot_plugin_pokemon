# Core 层接口定义

本文档描述了 `core/` 模块的关键接口和与其他层的交互。Core 层包含不依赖于具体数据存储或外部框架的游戏核心规则和计算。

## `core/game_logic.py`

**职责:** 包含如战斗流程控制、伤害计算调用、状态效果处理、进化条件判断等主要游戏逻辑入口。

**关键方法:** (示例，具体方法根据游戏逻辑细分)

### `run_battle(player_pokemon: Pokemon, opponent_pokemon: Pokemon) -> BattleResult`

*   **描述:** 执行一场宝可梦对战的完整流程。
*   **输入:**
    *   `player_pokemon: Pokemon`: 玩家的宝可梦实例 (来自 models 层)。
    *   `opponent_pokemon: Pokemon`: 对手的宝可梦实例 (来自 models 层)。
*   **输出:**
    *   `BattleResult`: 包含战斗结果、日志、宝可梦最终状态等信息（一个自定义的数据结构或 models 层对象）。
*   **调用关系:**
    *   被 `services/battle_service.py` 调用。
    *   调用 `core/battle/formulas.py` 进行计算。
    *   调用 `core/battle/status_effect.py` 和 `core/battle/field_effect.py` 处理效果。

## `core/battle/pokemon_factory.py`

**职责:** 根据宝可梦种类数据 (Species) 和等级等信息，创建具体的宝可梦实例 (Pokemon)。

**关键方法:**

### `create_pokemon_instance(species_data: Species, level: int) -> Pokemon`

*   **描述:** 创建一个新的宝可梦实例对象。
*   **输入:**
    *   `species_data: Species`: 宝可梦种类数据 (来自 models 层)。
    *   `level: int`: 宝可梦的等级。
*   **输出:**
    *   `Pokemon`: 新创建的宝可梦实例对象 (来自 models 层)。
*   **调用关系:**
    *   被 `services/pokemon_service.py` (例如，在捕捉或生成野生宝可梦时) 调用。

## `core/battle/formulas.py`

**职责:** 存放所有游戏内的计算公式，如伤害、经验值、属性计算等。

**关键方法:** (示例)

### `calculate_damage(attack_power: int, defense_power: int, move_power: int, ...) -> int`

*   **描述:** 计算一次攻击造成的伤害。
*   **输入:**
    *   `attack_power: int`: 攻击方的攻击属性值。
    *   `defense_power: int`: 防守方的防御属性值。
    *   `move_power: int`: 技能的威力。
    *   ... 其他影响伤害的参数 (属性克制、天气、状态等)。
*   **输出:**
    *   `int`: 计算出的伤害数值。
*   **调用关系:**
    *   被 `core/game_logic.py` 或 `core/battle/battle_logic.py` 调用。

## 其他 Core 模块

*   `core/battle/encounter_logic.py`: 包含遭遇野生宝可梦的逻辑。
    *   **关键方法:** `try_encounter(location: Map) -> Species | None` (输入地图模型，输出遭遇到的宝可梦种类模型或 None)。
*   `core/battle/field_effect.py`: 处理场地效果。
*   `core/battle/status_effect.py`: 处理状态效果。
*   `core/pet/`: 包含宠物技能、养成、捕捉、装备、道具、进化、系统等更细分的逻辑模块，它们也会提供类似的方法供 services 层调用，并操作 models 层对象。 