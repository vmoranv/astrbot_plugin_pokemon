# 数据处理流程 (Pipeline) 规范

本文档定义了插件各架构层之间数据流动的规范和数据结构。理解这些规范有助于确保模块间的正确交互和职责边界。

## 数据流动的基本原则

1.  **请求自顶向下，结果/错误自底向上:**
    *   用户请求或外部事件从顶层（`main.py` -> `commands/`）进入，逐层向下传递到 `services/`，可能进一步触及 `core/` 和 `data_access/`。
    *   处理结果、返回数据或异常则从底层向上返回，经过 `services/`，最终由 `commands/` 层格式化后返回给 `main.py`，再由 AstrBot 发送给用户。
2.  **Models 作为主要数据载体:**
    *   在 `services/`、`core/` 和 `data_access/` 层之间传递的业务数据应主要使用 `models/` 模块中定义的数据模型对象。
    *   这确保了数据结构的一致性，并提供了清晰的数据契约。
3.  **层边界的数据转换:**
    *   **Commands -> Services:** `commands/` 层负责将原始的外部输入（如 `AstrMessageEvent`）解析为结构化的参数，调用 `services/` 层的方法。传递给 Services 层的是 Python 基本类型或 Models 对象。
    *   **Services -> Data Access:** `services/` 层调用 `data_access/repositories/` 的方法，传递 Models 对象或用于查询的标识符/参数。
    *   **Data Access -> Services:** `data_access/repositories/` 从数据库读取数据，将其转换为 `models/` 对象返回给 `services/` 层。
    *   **Services -> Core:** `services/` 层调用 `core/` 模块的纯逻辑函数，传递 Models 对象或基本类型作为输入。
    *   **Core -> Services:** `core/` 模块的函数返回计算结果或更新后的 Models 对象给 `services/` 层。
    *   **Services -> Commands:** `services/` 层将业务处理结果（可能是 Models 对象、基本类型或自定义结果对象）返回给 `commands/` 层。
    *   **Commands -> main.py:** `commands/` 层将服务层返回的结果格式化为适合 AstrBot 输出的格式（如字符串、`MessageEventResult` 对象）。
4.  **异常处理:**
    *   底层模块（`data_access/`，`core/`）应抛出 `utils/exceptions.py` 中定义的自定义异常或标准的 Python 异常。
    *   `services/` 层负责捕获底层异常，进行业务逻辑相关的处理，可能转换为服务层特定的异常或返回错误结果。
    *   `commands/` 层负责捕获服务层抛出的异常或返回的错误结果，并将其格式化为用户友好的错误消息。

## 各层在数据流中的角色

*   **Commands:**
    *   **输入:** 原始外部事件 (`AstrMessageEvent`)。
    *   **输出:** 调用 `services/` 层方法的参数 (基本类型, Models 对象)；格式化后的用户回复 (`MessageEventResult`, 字符串)。
    *   **职责:** 解析输入，参数校验，调用服务，格式化输出。
*   **Services:**
    *   **输入:** 来自 `commands/` 层的结构化参数 (基本类型, Models 对象)。
    *   **输出:** 调用 `core/` 和 `data_access/` 的参数 (Models 对象, 基本类型)；返回给 `commands/` 层的结果 (Models 对象, 基本类型, 自定义结果对象)；抛出业务异常。
    *   **职责:** 编排业务流程，调用 Core 和 Data Access，处理事务和异常。
*   **Core:**
    *   **输入:** 来自 `services/` 层的 Models 对象或基本类型。
    *   **输出:** 计算结果或更新后的 Models 对象；抛出逻辑异常。
    *   **职责:** 实现纯游戏规则和计算，操作 Models 对象。
*   **Models:**
    *   **职责:** 定义游戏数据结构，作为数据在 `services/`、`core/` 和 `data_access/` 层之间传递的**载体**。不包含复杂的业务逻辑。
*   **Data Access:**
    *   **输入:** 来自 `services/` 层的 Models 对象或查询参数 (基本类型)。
    *   **输出:** 从数据库读取并转换为 Models 对象的数据；执行数据库操作的结果（成功/失败）。
    *   **职责:** 封装数据库操作，实现 Models 对象与数据库数据之间的转换。
*   **Utils & Config:**
    *   这些模块提供跨层使用的辅助功能（日志、常量、异常）和配置信息。它们不参与核心的数据流转链条，而是被其他层按需调用。
