from .settings import settings

# Validate settings on import
if not settings.validate_settings():
    raise RuntimeError("Invalid configuration detected")
