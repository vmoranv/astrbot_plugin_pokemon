# Utils 层接口定义

本文档描述了 `utils/` 模块的关键接口。Utils 层包含通用工具类，提供不属于特定业务领域的辅助功能。

## `utils/txt_parser.py` (如果需要)

**职责:** 处理 TXT 文件输入/输出，例如与旧版 AstrBot 交互。

**关键方法:**

### `parse_input(file_path: str) -> dict`

*   **描述:** 读取指定 TXT 文件，将其内容解析为命令和参数字典。
*   **输入:**
    *   `file_path: str`: TXT 文件路径。
*   **输出:**
    *   `dict`: 解析出的命令和参数字典。
*   **调用关系:**
    *   可能被 `main.py` 或其他需要读取 TXT 输入的模块调用。

### `format_output(data_dict: dict, file_path: str) -> None`

*   **描述:** 将结果字典格式化并写入指定的 TXT 文件。
*   **输入:**
    *   `data_dict: dict`: 需要写入的数据字典。
    *   `file_path: str`: TXT 文件路径。
*   **输出:** 无。
*   **调用关系:**
    *   可能被 `main.py` 或其他需要写入 TXT 输出的模块调用。

## `utils/logger.py`

**职责:** 配置和提供日志记录器实例，方便调试和追踪。建议封装 `astrbot.api.logger`。

**关键方法:** (示例，通常是对标准 logging 库或 astrbot.api.logger 的封装)

### `info(message: str) -> None`

*   **描述:** 记录一条信息级别的日志。
*   **输入:**
    *   `message: str`: 日志消息。
*   **输出:** 无。
*   **调用关系:**
    *   可在插件的任何层中调用，用于记录运行时信息。

### `error(message: str, exc_info: bool = False) -> None`

*   **描述:** 记录一条错误级别的日志。
*   **输入:**
    *   `message: str`: 日志消息。
    *   `exc_info: bool`: 是否包含异常信息。
*   **输出:** 无。
*   **调用关系:**
    *   可在插件的任何层中调用，用于记录错误信息。

## `utils/exceptions.py`

**职责:** 定义游戏中可能发生的自定义异常。

**关键类:** (示例)

### `PokemonNotFoundException(Exception)`

*   **描述:** 当找不到指定的宝可梦时抛出的异常。

### `InsufficientItemException(Exception)`

*   **描述:** 当玩家道具不足时抛出的异常。

## 接口定义 / 关键交互

Utils 层提供静态方法或函数供其他层调用，例如 `utils.logger.info("...")`, `utils.txt_parser.parse_input(...)`。异常类在需要时被抛出并在上层捕获处理。 