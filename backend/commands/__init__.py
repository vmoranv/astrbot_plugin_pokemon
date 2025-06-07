# Import key command components
from .command_handler import CommandHandler
from .available_commands import AVAILABLE_COMMANDS
from .player_commands import handle_command, PlayerCommands

# Define what gets exported when someone does "from backend.commands import *"
__all__ = [
    'CommandHandler',
    'AVAILABLE_COMMANDS', 
    'handle_command',
    'PlayerCommands'
]
