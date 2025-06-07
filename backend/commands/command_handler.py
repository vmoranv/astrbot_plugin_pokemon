from typing import Dict, Any, Optional, List
# Assuming AstrBot provides an event object structure
# from astrbot.event import AstrMessageEvent, MessageEventResult
from backend.commands.available_commands import AVAILABLE_COMMANDS
from backend.utils.exceptions import CommandParseException, InvalidArgumentException, GameException, PlayerNotFoundException
from backend.utils.logger import get_logger
# Import necessary services
from backend.core.services.player_service import PlayerService
from backend.core.services.pokemon_service import PokemonService
from backend.core.services.item_service import ItemService
from backend.core.services.map_service import MapService
from backend.core.services.dialog_service import DialogService
from backend.models.player import Player
from backend.utils.exceptions import CommandParseException, InvalidArgumentException, GameException, PlayerNotFoundException, RaceNotFoundException

logger = get_logger(__name__)

class CommandHandler:
    """Handles parsing and dispatching commands from AstrBot events."""

    def __init__(self):
        # Initialize services
        self.player_service = PlayerService()
        self.pokemon_service = PokemonService()
        self.item_service = ItemService()
        self.map_service = MapService()
        self.dialog_service = DialogService()
        # Initialize other services

    async def handle_command(self, event: Any) -> Any: # Use Any for event and result for MVP
        """
        Parses the command from the event and dispatches it to the appropriate service.
        Returns a result object suitable for AstrBot.
        """
        # Example: Extract command and args from event (replace with actual AstrBot event structure)
        # command_text = event.get_command_text() # Assuming method to get command string
        # parts = command_text.split()
        # if not parts:
        #     return self._create_error_result("No command provided.") # Assuming helper method
        # command_name = parts[0].lower()
        # args = parts[1:]
        # player_id = event.get_sender_id() # Assuming method to get sender ID
        # player_name = event.get_sender_name() # Assuming method to get sender name

        # Placeholder for MVP
        command_name = "start" # Example default command for testing
        args = ["TestPlayer"]
        player_id = "user123"
        player_name = "TestPlayer"
        logger.info(f"Received command: {command_name} with args {args} from player {player_id}")


        if command_name not in AVAILABLE_COMMANDS:
            return self._create_error_result(f"Unknown command: {command_name}")

        command_info = AVAILABLE_COMMANDS[command_name]

        try:
            # Validate and parse arguments
            parsed_args = self._parse_and_validate_args(args, command_info["params"])

            # Get or create player (most commands require a player)
            player = await self.player_service.get_or_create_player(player_id, player_name)

            # Dispatch command to the appropriate service method
            result_message = await self._dispatch_command(command_name, player, parsed_args)

            # Return success result (replace with actual AstrBot result object)
            # return event.plain_result(result_message) # Assuming plain_result method
            return f"Success: {result_message}" # Placeholder

        except (CommandParseException, InvalidArgumentException, GameException) as e:
            logger.warning(f"Command handling failed for {command_name} from {player_id}: {e}")
            return self._create_error_result(f"Error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while handling command {command_name} from {player_id}: {e}", exc_info=True)
            return self._create_error_result("An unexpected error occurred. Please try again later.")

    def _parse_and_validate_args(self, args: List[str], param_definitions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses and validates command arguments based on definitions.
        """
        parsed_args = {}
        if len(args) < len([p for p in param_definitions if p["required"]]):
             raise InvalidArgumentException("Not enough arguments provided.")
        if len(args) > len(param_definitions):
             raise InvalidArgumentException("Too many arguments provided.")

        for i, param_def in enumerate(param_definitions):
            param_name = param_def["name"]
            param_type = param_def["type"]
            param_required = param_def["required"]

            if i < len(args):
                arg_value_str = args[i]
                try:
                    # Attempt to convert argument to the expected type
                    if param_type == int:
                        parsed_args[param_name] = int(arg_value_str)
                    elif param_type == float:
                        parsed_args[param_name] = float(arg_value_str)
                    elif param_type == bool:
                         # Simple boolean parsing
                         if arg_value_str.lower() in ['true', 'yes', '1']:
                             parsed_args[param_name] = True
                         elif arg_value_str.lower() in ['false', 'no', '0']:
                             parsed_args[param_name] = False
                         else:
                             raise ValueError(f"Invalid boolean value: {arg_value_str}")
                    else: # Default to string
                        parsed_args[param_name] = arg_value_str
                except ValueError:
                    raise InvalidArgumentException(f"Argument '{arg_value_str}' for parameter '{param_name}' is not a valid {param_type.__name__}.")
            elif param_required:
                 # This case should ideally be caught by the length check above, but included for safety
                 raise InvalidArgumentException(f"Missing required argument: {param_name}")
            # If not required and not provided, it's simply not added to parsed_args

        return parsed_args

    async def _dispatch_command(self, command_name: str, player: Player, parsed_args: Dict[str, Any]) -> str:
        """
        Dispatches the parsed command to the correct service method.
        Returns a message string to be sent back to the user.
        """
        # Map command names to service methods
        if command_name == "start":
            # 'start' command is handled by get_or_create_player, which is already called.
            # This branch might be for initial setup messages or tutorials.
            # For MVP, just confirm player exists/created.
            return f"Welcome, {player.name}! Your adventure begins."
        elif command_name == "catch":
            # Call PokemonService to handle catch logic
            caught_pokemon = await self.pokemon_service.catch_wild_pokemon(player, player.location_id)
            if caught_pokemon:
                 # Need to get race name from metadata service
                 try:
                     race = await self.metadata_service.get_race(caught_pokemon.race_id)
                     return f"You caught a {race.name}!"
                 except RaceNotFoundException:
                     return f"You caught a pokemon (ID: {caught_pokemon.race_id})!" # Fallback
            else:
                 return "You didn't catch a pokemon this time."
        elif command_name == "move":
            # Call MapService to handle movement
            location_id = parsed_args.get("location_id")
            if not location_id:
                 raise InvalidArgumentException("Location ID is required for the move command.")
            return await self.map_service.move_player_to_map(player, location_id)
        elif command_name == "inventory":
            # Call ItemService or access player model to show inventory
            # For MVP, just show raw inventory dict
            return f"Your inventory: {player.inventory}"
        elif command_name == "party":
            # Call PokemonService or access player model to show party
            # For MVP, just show raw party list
            return f"Your party pokemon IDs: {player.pokemon_party}"
        elif command_name == "use":
            # Call ItemService to handle item usage
            item_id = parsed_args.get("item_id")
            target_id = parsed_args.get("target_id")
            if item_id is None:
                 raise InvalidArgumentException("Item ID is required for the use command.")
            return await self.item_service.use_item(player, item_id, target_id)
        elif command_name == "dialog":
             dialog_id = parsed_args.get("dialog_id")
             option_index = parsed_args.get("option_index")
             if dialog_id is None:
                  raise InvalidArgumentException("Dialog ID is required for the dialog command.")

             if option_index is None:
                  # Start a new dialog
                  return await self.dialog_service.start_dialog(player, dialog_id)
             else:
                  # Choose an option in an ongoing dialog (requires tracking current dialog state, which is not in MVP)
                  # For MVP, we'll just simulate choosing an option in the specified dialog
                  return await self.dialog_service.choose_dialog_option(player, dialog_id, option_index)

        # Add other command dispatches here

        else:
            # This case should be caught by the check in handle_command, but included for safety
            raise CommandParseException(f"No dispatch logic for command: {command_name}")

    def _create_error_result(self, message: str) -> Any: # Use Any for result for MVP
        """
        Helper to create an error result object.
        (Replace with actual AstrBot error result object creation)
        """
        logger.error(f"Returning error result: {message}")
        # Example: return MessageEventResult(text=message, type="error")
        return f"Error: {message}" # Placeholder

# Example usage in main.py:
# command_handler = CommandHandler()
# async def on_message_event(event: AstrMessageEvent):
#     result = await command_handler.handle_command(event)
#     yield result # Yield the result back to AstrBot framework
