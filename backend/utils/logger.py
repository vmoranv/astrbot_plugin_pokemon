import logging
# from astrbot.api import logger as astrbot_logger # Placeholder for AstrBot logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a given name.
    Encapsulates AstrBot's logger or uses standard logging.
    """
    # In a real AstrBot plugin, you might use astrbot_logger.get_logger(name)
    # For now, using standard logging setup
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Basic configuration if no handlers are set (e.g., in standalone testing)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO) # Default level

    return logger

# Example usage:
# logger = get_logger(__name__)
# logger.info("Logger initialized") 