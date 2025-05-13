# Commands 层接口定义

本文档描述了 `commands/` 模块的关键接口和与其他层的交互。

## `commands/command_handler.py`

**职责:** 根据事件中的命令名称，分发到相应的服务层方法。它充当了表现层和业务逻辑层之间的协调者。

**关键方法:**

### `handle_command(event: AstrMessageEvent) -> MessageEventResult | None`

*   **描述:** 处理接收到的 AstrBot 消息事件，解析命令并调用相应的服务层方法。
*   **输入:**
    *   `event: AstrMessageEvent`: AstrBot 消息事件对象，包含发送者、消息内容等信息。
*   **输出:**
    *   `MessageEventResult | None`: 如果命令成功处理并需要回复，返回一个 `MessageEventResult` 对象；否则返回 `None`。
*   **调用关系:**
    *   被 `main.py` 调用。
    *   调用 `services/` 层中的具体服务方法。

## `commands/available_commands.py`

**职责:** 定义插件支持的所有命令及其参数结构。

**关键数据结构:**

### `COMMAND_DEFINITIONS`

*   **描述:** 一个字典，键是命令名称（例如，"catch"），值是包含参数定义的字典。
*   **调用关系:**
    *   被 `commands/command_handler.py` 用于查找命令定义和参数校验。 