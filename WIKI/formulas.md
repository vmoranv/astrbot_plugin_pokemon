# 游戏公式与计算

本文档详细说明了游戏中使用的各种公式和计算方法。

## 战斗相关

### 伤害计算

伤害计算公式如下：

`伤害 = ((((2 * 攻击方等级) / 5 + 2) * 技能威力 * 攻击/防御) / 50 + 2) * 修正系数`

其中修正系数包括：
- 属性相克效果（0.5x, 1x, 2x）
- 暴击效果（1.5x）
- 随机数（0.85-1.0）
- STAB加成（Same Type Attack Bonus，当技能与宝可梦属性相同时，伤害x1.5）

### 命中率计算

技能命中率计算公式：
```
最终命中率 = 技能基础命中率 * 攻击方命中等级修正 * 防御方闪避等级修正
```

## 捕获相关

### 捕获率计算

捕获率计算公式如下：
```
捕获阈值 = (3 * 最大HP - 2 * 当前HP) * 基础捕获率 * 球种修正 * 状态修正 / (3 * 最大HP)
```

其中：
- 基础捕获率：每种宝可梦的固有属性，范围通常为3-255
- 球种修正：不同的精灵球提供不同的修正值（普通球1.0x，高级球1.5x，超级球2.0x等）
- 状态修正：不同状态提供不同的捕获加成（睡眠/冰冻2.5x，麻痹/中毒/烧伤1.5x）

捕获成功判定：
1. 计算捕获阈值（0-255）
2. 生成随机数（0-255）
3. 如果随机数小于捕获阈值，则捕获成功

摇晃次数与捕获阈值关系：
- 0次摇晃：捕获阈值 < 10
- 1次摇晃：10 ≤ 捕获阈值 < 30
- 2次摇晃：30 ≤ 捕获阈值 < 70
- 3次摇晃：捕获阈值 ≥ 70，但随机数大于捕获阈值（捕获失败）
- 捕获成功：随机数小于捕获阈值

## 进化相关

### 进化条件

宝可梦进化可能基于以下条件：
- 等级达到特定值
- 使用特定进化石或道具
- 特定时间或地点
- 特定友好度
- 交换后
- 学习特定技能

每种宝可梦的进化条件在元数据中定义。

## 道具效果

### 战斗中使用的道具

1. **回复类道具**
   - HP回复：直接恢复固定值或百分比的HP
   - PP回复：恢复技能的PP值
   - 状态恢复：治愈特定状态异常

2. **能力提升类道具**
   - 格式：`stat_name:change`，例如 `attack:+1,defense:+1`
   - 能力等级范围：-6 到 +6
   - 每级提升效果：+1级对应1.5倍，+2级对应2倍，以此类推
   - 每级降低效果：-1级对应0.67倍，-2级对应0.5倍，以此类推

3. **进化石**
   - 触发特定宝可梦的进化
   - 需要宝可梦满足其他条件（如最低等级）

4. **捕获类道具**
   - 不同精灵球提供不同的捕获率修正
   - 特殊球可能在特定条件下有额外效果

## 经验值计算公式

(待补充，根据具体游戏世代或设计需求添加)

## 属性计算公式

(待补充，根据宝可梦种类、等级、个体值、努力值、性格等计算最终属性)

## 其他公式

(根据游戏需要添加其他计算公式，例如：进化条件判断、状态效果持续回合计算等)

## 接口定义 / 关键交互

`core/formulas.py` 模块应提供一系列纯函数，接收计算所需的参数（通常是 models 层对象或基本数据类型），并返回计算结果。这些函数应是无副作用的。

*   **调用关系:** 主要被 `core/game_logic.py` 或其子模块（如 `core/battle/battle_logic.py`）调用。 

# Formulas 接口定义

本文档描述了 `core/battle/formulas.py` 文件的关键接口。`formulas.py` 负责存放游戏中所有核心的计算公式，例如战斗伤害计算、经验值计算、属性计算等。

## `core/battle/formulas.py`

**职责:** 集中管理游戏中各种数值计算的公式实现。这些公式是纯函数，只依赖于输入参数进行计算，不涉及状态修改或数据持久化。

**关键功能:**

`formulas.py` 提供一系列函数，每个函数实现一个特定的计算公式。这些函数通常接收游戏相关的数值或模型对象作为输入，并返回计算结果。

*   **战斗伤害计算:** 根据攻击方和防守方的属性、技能威力、属性克制、状态效果、场地效果等因素计算造成的伤害值。
*   **经验值计算:** 根据击败的宝可梦等级、玩家等级、战斗类型等计算获得的经验值。
*   **属性值计算:** 根据宝可梦种类基础属性、个体值、努力值、等级、性格等计算宝可梦的实际战斗属性值（HP, 攻击, 防御, 特攻, 特防, 速度）。
*   **捕捉成功率计算:** 根据目标宝可梦的种类、当前 HP、使用的精灵球类型、状态效果等计算捕捉成功的概率。
*   **其他计算:** 可能包括状态效果持续回合计算、场地效果持续回合计算、遇敌概率计算、暴击率计算、命中率计算等。

**接口定义 (示例性描述，具体函数根据游戏需求定义):**

*   `calculate_damage(...) -> int`: 计算伤害。
*   `calculate_exp_gain(...) -> int`: 计算经验值获取。
*   `calculate_stat_value(...) -> int`: 计算宝可梦属性值。
*   `calculate_catch_rate(...) -> float`: 计算捕捉成功率。

**调用关系:**

*   主要被 `core/battle/battle_logic.py`、`core/pet/pet_grow.py`、`core/pet/pet_catch.py` 等 Core 模块中的逻辑函数调用。
*   可能被 `services/` 层中的服务方法直接调用，如果该计算不属于某个 Core 逻辑模块的内部细节。 