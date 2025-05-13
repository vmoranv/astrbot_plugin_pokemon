# Commands 层接口定义

本文档描述了 `commands/` 模块的关键接口和与其他层的交互。Commands 层负责接收来自 `main.py` 的用户输入事件，解析命令和参数，并分发到相应的服务层方法进行处理。

## `commands/command_handler.py`

**职责:** 接收 AstrBot 事件，解析命令和参数，根据 `available_commands.py` 定义进行初步校验，并调用 `services` 层相应的服务方法。它充当了表现层 (`main.py`) 和业务逻辑层 (`services/`) 之间的协调者。

**关键方法:**

### `handle_command(event: AstrMessageEvent) -> MessageEventResult | None`

*   **描述:** 处理接收到的 AstrBot 消息事件。解析事件中的文本，识别命令和参数，调用相应的服务方法，并返回适合 AstrBot 回复的结果。
*   **输入:**
    *   `event: AstrMessageEvent`: AstrBot 消息事件对象，包含发送者、消息内容等信息。
*   **输出:**
    *   `MessageEventResult | None`: 适合 AstrBot 回复的结果对象，或者在不需要回复时返回 `None`。
*   **调用关系:**
    *   被 `main.py` 调用。
    *   调用 `available_commands.py` 获取命令定义和进行参数校验。
    *   调用 `services/` 层中的具体服务方法（例如 `services.player_service.get_player_info`, `services.pokemon_service.catch_pokemon` 等）。
    *   可能调用 `utils/exceptions.py` 中的自定义异常。

## `commands/available_commands.py`

**职责:** 定义插件支持的所有命令及其期望的参数结构。这有助于 `command_handler.py` 进行参数解析和初步校验，也可以用于生成命令帮助信息。

**关键数据结构:**

### `COMMAND_DEFINITIONS: Dict[str, Dict[str, Any]]`

*   **描述:** 一个字典，键是命令名称（字符串），值是另一个字典，描述该命令的属性，特别是期望的参数。
*   **调用关系:**
    *   被 `command_handler.py` 调用，用于查找命令定义和校验参数。

## 接口定义 / 关键交互

*   `main.py` 调用 `command_handler.handle_command()`。
*   `command_handler.py` 依赖 `available_commands.py` 来理解和校验命令。
*   `command_handler.py` 调用 `services/` 层中的具体服务方法。
*   `services/` 层的方法执行业务逻辑，并返回结果给 `command_handler.py`。
*   `command_handler.py` 将服务层返回的结果转换为 `MessageEventResult` 返回给 `main.py`。
*   参数校验失败或服务层抛出异常时，`command_handler.py` 负责捕获并生成相应的用户友好错误信息。 