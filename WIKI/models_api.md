# Models 层接口定义

本文档描述了 `models/` 模块的关键接口。Models 层定义游戏中的核心实体，主要作为数据载体在各层之间传递。

## 职责

定义游戏中的核心实体，如 Player, Pokemon, Species, Move, Item 等。这些通常是简单的 Python 类 (Plain Old Python Objects - POPOs)，主要用于封装数据。可以包含一些简单的验证逻辑或辅助方法（例如，计算宝可梦当前属性）。

## 关键类 (示例)

### `Player`

*   **描述:** 代表一个玩家实体。
*   **属性:** (示例)
    *   `id: str`: 玩家唯一 ID。
    *   `name: str`: 玩家昵称。
    *   `location_id: str`: 玩家当前所在地点 ID。
    *   `inventory: list[Item]`: 玩家背包中的道具列表。
    *   `pokemons: list[Pokemon]`: 玩家拥有的宝可梦实例列表。
    *   ... 其他玩家相关属性。

### `Pokemon`

*   **描述:** 代表一个具体的宝可梦实例 (非图鉴数据)。
*   **属性:** (示例)
    *   `id: int`: 宝可梦实例唯一 ID。
    *   `species_id: int`: 对应的宝可梦种类 ID。
    *   `nickname: str | None`: 昵称。
    *   `level: int`: 等级。
    *   `current_hp: int`: 当前生命值。
    *   `moves: list[Move]`: 学会的技能列表。
    *   ... 其他宝可梦实例属性 (经验值、个体值、努力值、状态等)。

### `Species`

*   **描述:** 代表一种宝可梦的图鉴数据。
*   **属性:** (示例)
    *   `id: int`: 宝可梦种类 ID。
    *   `name: str`: 宝可梦名称。
    *   `type1: str`: 属性 1。
    *   `type2: str | None`: 属性 2。
    *   `base_stats: dict`: 基础能力值 (HP, Attack, Defense, ...)。
    *   ... 其他图鉴属性 (特性、蛋组、捕捉率等)。

### `Item`

*   **描述:** 代表一个道具。
*   **属性:** (示例)
    *   `id: int`: 道具 ID。
    *   `name: str`: 道具名称。
    *   `description: str`: 道具描述。
    *   `effect: str`: 道具效果类型。
    *   ... 其他道具属性。

### `Move`

*   **描述:** 代表一个技能。
*   **属性:** (示例)
    *   `id: int`: 技能 ID。
    *   `name: str`: 技能名称。
    *   `type: str`: 技能属性。
    *   `power: int`: 技能威力。
    *   `accuracy: int`: 技能命中率。
    *   `pp: int`: 技能 PP。
    *   ... 其他技能属性 (分类、效果等)。

## 接口定义 / 关键交互

Models 层主要作为数据载体，在各层之间传递。它们通常不包含复杂的对外接口方法，其属性通过标准的 Python 属性访问方式进行读写。 