# backend/commands/available_commands.py

# Define the structure of available commands and their expected parameters.
# This helps in parsing and validating user input.

AVAILABLE_COMMANDS = {
    "start": {
        "description": "Starts a new game.",
        "params": [
            {"name": "player_name", "type": str, "required": True, "description": "Your desired in-game name."}
        ]
    },
    "catch": {
        "description": "Attempts to catch a wild pokemon in your current location.",
        "params": [] # Location is determined by player's current location
    },
    "move": {
        "description": "Moves to an adjacent location.",
        "params": [
            {"name": "location_id", "type": str, "required": True, "description": "The ID of the location to move to."}
        ]
    },
    "inventory": {
        "description": "Shows your inventory.",
        "params": []
    },
    "party": {
        "description": "Shows your pokemon party.",
        "params": []
    },
    "use": {
        "description": "Uses an item from your inventory.",
        "params": [
            {"name": "item_id", "type": int, "required": True, "description": "The ID of the item to use."},
            {"name": "target_id", "type": int, "required": False, "description": "The ID of the target (e.g., pokemon instance ID)."}
        ]
    },
    "dialog": {
        "description": "Interacts with a dialogue.",
        "params": [
             {"name": "dialog_id", "type": int, "required": True, "description": "The ID of the dialogue to start."},
             {"name": "option_index", "type": int, "required": False, "description": "The index of the dialogue option to choose."}
        ]
    }
    # Add other commands here
}

# Example of how to use this:
# if command_name in AVAILABLE_COMMANDS:
#     command_info = AVAILABLE_COMMANDS[command_name]
#     # Validate args against command_info['params']
#     # Call appropriate service method
