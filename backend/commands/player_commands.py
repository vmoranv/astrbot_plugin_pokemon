from typing import List, Optional, Dict, Any, Tuple
from backend.core.services.player_service import PlayerService
from backend.core.services.pokemon_service import PokemonService
from backend.core.services.item_service import ItemService
from backend.core.services.map_service import MapService
from backend.core.services.battle_service import BattleService # Import BattleService
from backend.utils.logger import get_logger
from backend.utils.exceptions import (
    PlayerNotFoundException, InvalidPartyOrderException,
    PokemonNotInCollectionException, PartyFullException,
    ItemNotFoundException, InsufficientItemException,
    LocationNotFoundException, BattleNotFoundException,
    NoActivePokemonException, InvalidBattleActionException,
    SkillNotFoundException, PokemonFaintedException, # Import PokemonFaintedException
    InvalidTargetException, NotEnoughPokemonException, # Import InvalidTargetException, NotEnoughPokemonException
    InvalidPokemonStateError, # Import InvalidPokemonStateError
    BattleFinishedException # Import BattleFinishedException
)
from backend.models.player import Player
from backend.models.pokemon import Pokemon
from backend.models.item import Item
from backend.models.battle import Battle
from backend.models.skill import Skill

logger = get_logger(__name__)

# Instantiate services
# TODO: Consider dependency injection instead of direct instantiation (S92 refinement)
player_service = PlayerService()
pokemon_service = PokemonService()
item_service = ItemService()
map_service = MapService()
battle_service = BattleService() # Instantiate BattleService

class PlayerCommands:
    """
    Handles player commands during a battle.
    Interacts with the BattleService to process player actions.
    """
    def __init__(self, battle_service: BattleService):
        self._battle_service = battle_service

    async def handle_player_action(self, player_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles a player's action during their turn.

        Args:
            player_id: The ID of the player taking the action.
            action: A dictionary representing the player's chosen action.
                    Expected format: {"type": "skill", "skill_id": 123, "target_pokemon_instance_id": "abc"}
                    or {"type": "item", "item_id": 456, "target_pokemon_instance_id": "def"}
                    or {"type": "switch", "pokemon_instance_id": "ghi"}
                    or {"type": "run"}
                    or {"type": "catch"}

        Returns:
            A dictionary containing the battle outcome and messages.
            Expected format: {"battle_ended": bool, "outcome": Optional[str], "messages": List[str]}

        Raises:
            InvalidBattleActionException: If the action is invalid or not allowed.
            BattleFinishedException: If the battle is already finished.
            Exception: For other unexpected errors.
        """
        logger.info(f"Player {player_id} attempting action: {action}")

        try:
            # S5, S6: Fetch the current battle state for the player
            battle = await self._battle_service.get_player_battle(player_id)
            if not battle:
                 raise BattleNotFoundException(f"No active battle found for player {player_id}.")

            if battle.is_finished:
                raise BattleFinishedException("Battle is already finished.")

            # S7: Check if it's the player's turn
            # TODO: Implement turn tracking logic in Battle model/Service (S7 refinement)
            # The BattleService.get_player_battle method or a separate check should determine the current turn.
            if battle.current_turn_player_id != player_id:
                 raise InvalidBattleActionException("现在不是你的回合。")

            action_type = action.get("type")
            if not action_type:
                raise InvalidBattleActionException("Action type is missing.")

            # S8: Validate the action based on the current battle state
            player_active_pokemon = battle.player_active_pokemon_instance # Assuming this is the actual Pokemon object
            if not player_active_pokemon:
                 raise NoActivePokemonException("Player has no active Pokemon.")

            battle_outcome: Dict[str, Any] = {"battle_ended": False, "outcome": None, "messages": []}

            if action_type == "skill":
                skill_id = action.get("skill_id")
                target_pokemon_instance_id = action.get("target_pokemon_instance_id") # Optional target

                if skill_id is None:
                    raise InvalidBattleActionException("Skill action requires 'skill_id'.")

                # S9: Validate skill_id (e.g., does the active pokemon know this skill? Does it have PP?)
                skill = None
                for ps in player_active_pokemon.skills:
                     if ps.skill_id == skill_id:
                          skill = self._battle_service._metadata_repo.get_skill(skill_id) # Access metadata via service (TODO: Refactor metadata access)
                          if skill and ps.current_pp > 0:
                               break
                          elif skill and ps.current_pp <= 0:
                               raise InvalidBattleActionException(f"技能 {skill.name} 没有PP了！")
                          else:
                               # Should not happen if skill_id is valid and in pokemon's skills
                               raise InvalidBattleActionException(f"无法找到技能 {skill_id} 的数据。")

                if not skill:
                     raise InvalidBattleActionException(f"你的宝可梦不知道技能 {skill_id}。")

                # TODO: Validate target_pokemon_instance_id based on skill's target type (S93 refinement)
                # For now, assume target is the opponent if not specified
                target_pokemon = None
                if target_pokemon_instance_id:
                     target_pokemon = await self._battle_service._get_pokemon_from_battle(battle, target_pokemon_instance_id) # TODO: Refactor this helper (S53 refinement)
                     if not target_pokemon:
                          raise InvalidTargetException(f"无效的目标宝可梦实例ID: {target_pokemon_instance_id}")
                else:
                     # Default target is wild pokemon in a wild battle
                     target_pokemon = battle.wild_active_pokemon_instance

                if not target_pokemon:
                     raise InvalidTargetException("技能需要一个目标。")


                # S10, S11: Call BattleService to process skill action
                events, battle_ended, outcome = await self._battle_service.process_skill_action(
                    battle.battle_id, player_id, skill_id, target_pokemon.instance_id
                )

            elif action_type == "item":
                item_id = action.get("item_id")
                target_pokemon_instance_id = action.get("target_pokemon_instance_id") # Optional target

                if item_id is None:
                    raise InvalidBattleActionException("Item action requires 'item_id'.")

                # S12: Validate item_id (e.g., does the player have this item? Is it usable in battle?)
                player = await self._battle_service._player_repo.get_player(player_id)
                if not player or player.inventory.get(str(item_id), 0) <= 0:
                     raise InsufficientItemException(f"你没有道具 {item_id}。")

                item = self._battle_service._metadata_repo.get_item_by_id(item_id) # Access metadata via service (TODO: Refactor)
                if not item:
                     raise ItemNotFoundException(f"道具 {item_id} 不存在。")

                # Determine the actual target pokemon object
                target_pokemon = None
                if target_pokemon_instance_id:
                     target_pokemon = await self._battle_service._get_pokemon_from_battle(battle, target_pokemon_instance_id) # TODO: Refactor this helper (S53 refinement)
                     if not target_pokemon:
                          raise InvalidTargetException(f"无效的目标宝可梦实例ID: {target_pokemon_instance_id}")
                else:
                     # Default target for some items might be the player's active pokemon
                     # TODO: Implement item targeting logic based on item type (S94 refinement)
                     target_pokemon = player_active_pokemon # Assume self for now

                if not target_pokemon:
                     raise InvalidTargetException("道具需要一个目标。")

                # TODO: Check if item can be used on the target (e.g., cannot use Potion on fainted pokemon) (S95 refinement)
                # if item.item_type in ['healing', 'berry'] and target_pokemon.is_fainted():
                #      raise InvalidTargetException(f"无法对濒死的宝可梦使用 {item.name}！")


                # S13, S14: Call BattleService to process item action
                events, battle_ended, outcome = await self._battle_service.process_item_action(
                    battle.battle_id, player_id, item_id, target_pokemon.instance_id
                )

            elif action_type == "switch":
                pokemon_instance_id = action.get("pokemon_instance_id")
                if pokemon_instance_id is None:
                    raise InvalidBattleActionException("Switch action requires 'pokemon_instance_id'.")

                # S15: Validate pokemon_instance_id (e.g., is this pokemon in the player's party? Is it not fainted? Is it not the current active pokemon?)
                player_party = await self._battle_service._get_player_party(player_id) # Access party via service (TODO: Refactor)
                target_pokemon = None
                for p in player_party:
                     if p.instance_id == pokemon_instance_id:
                          target_pokemon = p
                          break

                if not target_pokemon:
                     raise InvalidBattleActionException(f"宝可梦实例ID {pokemon_instance_id} 不在你的队伍中。")
                if target_pokemon.is_fainted():
                     raise PokemonFaintedException(f"{target_pokemon.nickname} 已经失去了战斗能力，无法上场。")
                if target_pokemon.instance_id == player_active_pokemon.instance_id:
                     raise InvalidBattleActionException(f"{target_pokemon.nickname} 已经在场上了。")

                # S16, S17: Call BattleService to process switch action
                events, battle_ended, outcome = await self._battle_service.process_switch_action(
                    battle.battle_id, player_id, pokemon_instance_id
                )

            elif action_type == "run":
                # S18, S19: Call BattleService to process run action
                events, battle_ended, outcome = await self._battle_service.process_run_action(battle.battle_id, player_id)

            elif action_type == "catch":
                 # TODO: Implement catch action validation (e.g., is it a wild battle? Does player have pokeballs?) (S96 refinement)
                 # TODO: Call BattleService to process catch action (S97 refinement)
                 # battle_outcome = await self._battle_service.process_catch_action(battle.battle_id, player_id) # TODO: Implement process_catch_action in BattleService (S98 refinement)
                 logger.debug(f"Processing catch action")
                 # Placeholder return
                 return {"battle_ended": False, "outcome": None, "messages": [f"玩家 {player_id} 尝试捕捉宝可梦 (待实现)"]}


            else:
                raise InvalidBattleActionException(f"未知的行动类型：{action_type}")

            # S20: After processing the action via BattleService, the service returns the updated battle state and messages
            # The messages are collected from the BattleLogic events within the service.
            battle_outcome["messages"] = events
            battle_outcome["battle_ended"] = battle_ended
            battle_outcome["outcome"] = outcome

            return battle_outcome

        except (InvalidBattleActionException, BattleNotFoundException,
                BattleFinishedException, NoActivePokemonException,
                SkillNotFoundException, InsufficientItemException,
                ItemNotFoundException, InvalidTargetException,
                PokemonFaintedException) as e:
            logger.warning(f"Player action failed for {player_id}: {e}")
            # S21, S22: Return an appropriate response to the user indicating the invalid action or finished battle
            return {"battle_ended": False, "outcome": None, "messages": [f"行动失败：{e}"]}
        except Exception as e:
            logger.error(f"An unexpected error occurred while handling player action for {player_id}: {e}", exc_info=True)
            # S23: Return a generic error message to the user
            return {"battle_ended": False, "outcome": None, "messages": ["处理您的行动时发生未知错误。"]}

    # TODO: Add other helper methods for command parsing if needed (S24 refinement)
    # For example, parsing a chat message like "!skill 火焰喷射" into the action dictionary format.

async def handle_command(player_id: str, command: str, args: List[str]) -> str:
    """
    Handles incoming commands from the player.
    Routes commands to appropriate handler functions.
    """
    try:
        # Check if player is in battle and if the command is a battle command
        active_battle = await battle_service.get_player_active_battle(player_id)
        if active_battle:
            # If in battle, only allow battle commands
            if command in ['fight', 'bag', 'pokemon', 'switch', 'run', 'catch']:
                return await handle_battle_command(player_id, command, args, active_battle)
            else:
                return "你正在战斗中，只能使用战斗相关的命令（fight, bag, pokemon, switch, run, catch）。"

        # If not in battle, handle non-battle commands
        if command == 'start' and len(args) == 1:
            return await handle_start_command(player_id, args[0])
        elif command == 'location':
            return await handle_location_command(player_id)
        elif command == 'move' and len(args) == 1:
            return await handle_move_command(player_id, args[0])
        elif command == 'party':
            return await handle_party_command(player_id)
        elif command == 'useitem' and len(args) >= 1:
            # Assuming item name or ID is provided, and optional target
            item_identifier = args[0]
            target_arg = args[1] if len(args) > 1 else None
            return await handle_useitem_command(player_id, item_identifier, target_arg)
        elif command == 'addpokemon' and len(args) == 1:
             # Debug command to add a pokemon
             pokemon_id = int(args[0])
             return await handle_addpokemon_command(player_id, pokemon_id)
        elif command == 'movepokemon' and len(args) == 2:
             try:
                 from_slot = int(args[0])
                 to_slot = int(args[1])
                 return await handle_movepokemon_command(player_id, from_slot, to_slot)
             except ValueError:
                 return "无效的队伍槽位，请使用数字。"
        elif command == 'sortparty':
             return await handle_sortparty_command(player_id)
        elif command == 'catch' and len(args) == 1:
             # This catch command is for non-battle catching (e.g., specific events)
             # Battle catch is handled in handle_battle_command
             pokemon_instance_id = int(args[0])
             return await handle_catch_command(player_id, pokemon_instance_id)
        # TODO: Add more non-battle commands (e.g., inventory, profile, etc.) (S3 refinement)
        else:
            return "未知命令或参数错误。"

    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except (LocationNotFoundException, InvalidPartyOrderException,
            PokemonNotInCollectionException, PartyFullException,
            ItemNotFoundException, InsufficientItemException,
            BattleNotFoundException, NoActivePokemonException,
            InvalidBattleActionException, SkillNotFoundException,
            PokemonFaintedException, InvalidTargetException,
            NotEnoughPokemonException) as e:
        # Catch specific game-related exceptions and return user-friendly messages
        return str(e)
    except Exception as e:
        logger.error(f"Error handling command '{command}' for player {player_id}: {e}", exc_info=True)
        return "执行命令时发生未知错误，请稍后再试。"

async def handle_battle_command(player_id: str, command: str, args: List[str], active_battle: Battle) -> str:
    """
    Handles commands specifically during a battle.
    """
    messages: List[str] = []
    battle_ended = False
    outcome: Optional[str] = None
    action: Optional[Dict[str, Any]] = None

    try:
        if command == 'fight':
            if len(args) != 1:
                return "用法: fight <技能编号>"
            try:
                skill_index = int(args[0]) - 1 # Adjust for 0-based index
                player_pokemon = await pokemon_service.get_pokemon_instance(active_battle.player_active_pokemon_instance_id)
                if not player_pokemon:
                     raise PokemonNotFoundException("你的宝可梦实例未找到。")
                if skill_index < 0 or skill_index >= len(player_pokemon.skills):
                     return "无效的技能编号。"
                # Get the skill ID from the pokemon's learned skills
                skill_id = player_pokemon.skills[skill_index].id
                action = {'type': 'attack', 'skill_id': skill_id}
            except ValueError:
                return "技能编号必须是数字。"
            except PokemonNotFoundException as e:
                 return str(e)

        elif command == 'bag':
            # Display player's inventory, filtered for battle-usable items
            # TODO: Filter items usable in battle (e.g., Potions, status heals, Pokeballs) (S3 refinement)
            player = await player_service.player_repo.get_player(player_id)
            if not player:
                 raise PlayerNotFoundException("玩家未找到。")
            inventory_messages = ["你的背包里有:"]
            if not player.inventory:
                 inventory_messages.append("  背包是空的。")
            else:
                 # Get item details from metadata for display
                 for item_id_str, quantity in player.inventory.items():
                      try:
                           item_id = int(item_id_str)
                           item = battle_service.metadata_repo.get_item_by_id(item_id)
                           if item:
                                # TODO: Check if item is usable in battle (S3 refinement)
                                inventory_messages.append(f"  {item.name} x{quantity}")
                           else:
                                inventory_messages.append(f"  未知道具 (ID: {item_id}) x{quantity}")
                      except ValueError:
                           inventory_messages.append(f"  无效道具ID ({item_id_str}) x{quantity}")

            return "\n".join(inventory_messages)

        elif command == 'pokemon':
            # Display player's party status
            player_party = await pokemon_service.get_player_party(player_id)
            party_messages = ["你的队伍:"]
            if not player_party:
                 party_messages.append("  队伍是空的。")
            else:
                 for i, pokemon in enumerate(player_party):
                      status = "濒死" if pokemon.is_fainted() else f"{pokemon.current_hp}/{pokemon.max_hp} HP"
                      active_marker = " (当前)" if pokemon.instance_id == active_battle.player_active_pokemon_instance_id else ""
                      party_messages.append(f"  {i+1}. {pokemon.nickname} (Lv.{pokemon.level}) - {status}{active_marker}")
            return "\n".join(party_messages)

        elif command == 'switch':
            if len(args) != 1:
                return "用法: switch <队伍编号>"
            try:
                party_index = int(args[0]) - 1 # Adjust for 0-based index
                player_party = await pokemon_service.get_player_party(player_id)
                if party_index < 0 or party_index >= len(player_party):
                     return "无效的队伍编号。"
                target_pokemon = player_party[party_index]
                action = {'type': 'switch', 'target_pokemon_instance_id': target_pokemon.instance_id}
            except ValueError:
                return "队伍编号必须是数字。"
            except (PokemonNotFoundException, PokemonFaintedException, InvalidBattleActionException, NotEnoughPokemonException) as e:
                 return str(e)

        elif command == 'run':
            if len(args) != 0:
                return "用法: run"
            action = {'type': 'run'}

        elif command == 'catch':
             if len(args) != 1:
                  return "用法: catch <精灵球道具ID>" # Or <精灵球道具名称> - using ID for simplicity now
             try:
                  item_id = int(args[0])
                  # TODO: Validate if item_id is actually a pokeball (S3 refinement)
                  action = {'type': 'catch', 'item_id': item_id}
             except ValueError:
                  return "道具ID必须是数字。"

        else:
            # This case should be caught by the initial check in handle_command, but included for safety
            return "未知战斗指令。"

        # If an action was successfully constructed, process the battle turn
        if action:
            updated_battle, messages = await battle_service.process_battle_action(
                active_battle.battle_id,
                player_id,
                action
            )
            # After processing, check if player's active pokemon fainted and battle is not over
            if not updated_battle.is_active:
                 # Battle ended, messages already contain outcome
                 pass # Messages are already updated by process_battle_action
            elif updated_battle.player_active_pokemon_instance_id != active_battle.player_active_pokemon_instance_id:
                 # Player successfully switched pokemon, messages already contain switch messages
                 pass # Messages are already updated by process_battle_action
            elif (await pokemon_service.get_pokemon_instance(updated_battle.player_active_pokemon_instance_id)).is_fainted():
                 # Player's active pokemon fainted, and battle is not over (needs switch)
                 # The core logic/service already added the "你需要替换宝可梦" message
                 # Check if player has any unfainted pokemon left
                 player_party = await pokemon_service.get_player_party(player_id)
                 unfainted_pokemon_count = sum(1 for p in player_party if not p.is_fainted())
                 if unfainted_pokemon_count == 0:
                      # All pokemon fainted, player loses
                      # This case should ideally be handled by core logic/service setting outcome to 'lose'
                      # But as a fallback, add a message here
                      messages.append("你的所有宝可梦都失去了战斗能力！")
                      # The service layer should have set the outcome and ended the battle, but if not:
                      if updated_battle.is_active:
                           await battle_service.end_battle(updated_battle.battle_id, outcome='lose')
                           messages.append("你输掉了战斗！")


            return "\n".join(messages)
        else:
            # Should not happen if command is valid but action is None
            return "未能生成战斗行动。"

    except (PlayerNotFoundException, BattleNotFoundException, InvalidBattleActionException,
            PokemonNotFoundException, NoActivePokemonException, SkillNotFoundException,
            ItemNotFoundException, InvalidTargetException, NotEnoughPokemonException,
            PokemonFaintedException, InvalidPokemonStateError, InsufficientItemException) as e:
        # Catch specific exceptions and return error message
        return str(e)
    except Exception as e:
        logger.error(f"Error handling battle command '{command}' for player {player_id}: {e}", exc_info=True)
        return "处理战斗指令时发生未知错误，请稍后再试。"


# --- Non-Battle Command Handlers (Existing or modified) ---

async def handle_start_command(player_id: str, player_name: str) -> str:
    """
    Handles the 'start' command to register a new player.
    """
    try:
        player = await player_service.get_player(player_id)
        if player:
            return f"你已经是宝可梦训练家了，{player.name}！无需重复开始。"
        else:
            new_player = await player_service.create_player(player_id, player_name)
            return f"欢迎来到宝可梦世界，{new_player.name}！你已成为一名新的宝可梦训练家！"
    except Exception as e:
        logger.error(f"Error handling start command for player {player_id}: {e}", exc_info=True)
        return "开始游戏时发生错误，请稍后再试。"

async def handle_location_command(player_id: str) -> str:
    """
    Handles the 'location' command to check the player's current location and trigger encounter check.
    """
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        location_id = player.location_id
        # Get location name from metadata using MapService
        location_name = await map_service.get_location_name(location_id)

        messages = [f"你当前位于：{location_name}"]

        # Check for wild pokemon encounter
        encounter_occurs = await pokemon_service.check_for_wild_encounter(location_id)

        if encounter_occurs:
            # Get wild pokemon details if encounter occurs
            wild_pokemon_details = await pokemon_service.get_wild_encounter_details(location_id)

            if wild_pokemon_details:
                wild_race_id, wild_level = wild_pokemon_details
                logger.info(f"Player {player_id} encountered wild pokemon race_id: {wild_race_id} at level: {wild_level} in location: {location_id}")

                # Create a temporary pokemon instance in the database for the encounter
                # This instance will be used for battle/catch attempts.
                wild_pokemon_instance = await pokemon_service.create_pokemon_instance(wild_race_id, wild_level, player_id=None) # Wild pokemon not owned by player initially

                # S2 refinement: Start a battle automatically upon encounter
                try:
                    battle, battle_messages = await battle_service.start_wild_pokemon_battle(player_id, wild_pokemon_instance.instance_id)
                    # Store the active battle ID in the player object (in-memory for the command duration)
                    # Note: For persistent battle state across commands, this would need to be in the Player model and saved.
                    # However, for simplicity and to avoid complex state management across commands,
                    # we assume battle commands are processed sequentially for a player.
                    # A more robust solution might involve a dedicated battle state manager or storing battle ID in Player model.
                    # For now, we'll rely on the battle_service to track active battles by player ID.
                    messages.extend(battle_messages)
                    messages.append("输入战斗指令进行操作 (例如: /fight, /bag, /pokemon, /run)。")

                except NoActivePokemonException:
                    messages.append("你遇到了野生的宝可梦，但你的队伍中没有可以战斗的宝可梦！")
                    # TODO: Handle scenario where player has no active pokemon upon encounter (S2 refinement)
                    # Maybe the wild pokemon runs away? Or player is forced to switch?
                except Exception as e:
                    logger.error(f"Error starting battle for player {player_id}: {e}", exc_info=True)
                    messages.append("开始战斗时发生错误。")

            else:
                messages.append("在当前位置未能找到野生的宝可梦信息。") # Should not happen if encounter_occurs is true

        # If no encounter, or encounter failed to start battle, check for active battle
        # This handles cases where a player might issue /location during an ongoing battle
        active_battle = await battle_service.get_player_active_battle(player_id)
        if active_battle:
             messages.append(f"你当前正在进行一场战斗 (ID: {active_battle.battle_id})。")
             # TODO: Provide more context about the ongoing battle (e.g., opponent, active pokemon) (S2 refinement)


        return "\n".join(messages)

    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except LocationNotFoundException:
        return "你当前位于一个未知地点。" # Should not happen if player location_id is valid
    except Exception as e:
        logger.error(f"Error handling location command for player {player_id}: {e}", exc_info=True)
        return "查询位置时发生错误，请稍后再试。"

async def handle_move_command(player_id: str, location_id: str) -> str:
    """
    Handles the 'move' command to move the player to a new location.
    """
    try:
        # Check if player is in a battle
        active_battle = await battle_service.get_player_active_battle(player_id)
        if active_battle:
             return "你正在战斗中，无法移动！" # Cannot move during battle

        message = await map_service.move_player_to_location(player_id, location_id)
        return message
    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except LocationNotFoundException:
        return f"找不到地点：{location_id}。"
    except Exception as e:
        logger.error(f"Error handling move command for player {player_id} to {location_id}: {e}", exc_info=True)
        return "移动时发生错误，请稍后再试。"

async def handle_inventory_command(player_id: str) -> str:
    """
    Handles the 'inventory' command to list player's items.
    """
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        inventory = await item_service.get_player_inventory(player_id)

        if not inventory:
            return "你的背包是空的。"

        messages = ["你的背包里有："]
        for item, quantity in inventory.items():
            # Attempt to get item name from metadata
            item_name = item.name if item and item.name else f"未知道具 (ID: {item.item_id})"
            messages.append(f"- {item_name} x{quantity}")

        return "\n".join(messages)

    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except Exception as e:
        logger.error(f"Error handling inventory command for player {player_id}: {e}", exc_info=True)
        return "查询背包时发生错误，请稍后再试。"

async def handle_party_command(player_id: str) -> str:
    """
    Handles the 'party' command to list player's party pokemon.
    """
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        party_pokemons = await pokemon_service.get_player_party_pokemon(player_id)

        if not party_pokemons:
            return "你的队伍中没有宝可梦。"

        messages = ["你的队伍宝可梦："]
        for i, pokemon in enumerate(party_pokemons):
            # Attempt to get race name from metadata
            race_name = pokemon.race.name if pokemon.race and pokemon.race.name else f"未知宝可梦 (Race ID: {pokemon.race_id})"
            messages.append(f"{i+1}. {pokemon.nickname} ({race_name} Lv.{pokemon.level}) - HP: {pokemon.current_hp}/{pokemon.max_hp}")
            # TODO: Add status effects and other relevant info (S2 refinement)

        return "\n".join(messages)

    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except Exception as e:
        logger.error(f"Error handling party command for player {player_id}: {e}", exc_info=True)
        return "查询队伍时发生错误，请稍后再试。"

async def handle_box_command(player_id: str) -> str:
    """
    Handles the 'box' command to list player's box pokemon.
    """
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        box_pokemons = await pokemon_service.get_player_box_pokemon(player_id)

        if not box_pokemons:
            return "你的宝可梦盒是空的。"

        messages = ["你的宝可梦盒里有："]
        for pokemon in box_pokemons:
             # Attempt to get race name from metadata
            race_name = pokemon.race.name if pokemon.race and pokemon.race.name else f"未知宝可梦 (Race ID: {pokemon.race_id})"
            messages.append(f"- {pokemon.nickname} ({race_name} Lv.{pokemon.level}) - HP: {pokemon.current_hp}/{pokemon.max_hp}")
            # TODO: Add status effects and other relevant info (S2 refinement)

        return "\n".join(messages)

    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except Exception as e:
        logger.error(f"Error handling box command for player {player_id}: {e}", exc_info=True)
        return "查询宝可梦盒子时发生错误，请稍后再试。"

async def handle_useitem_command(player_id: str, item_identifier: str, target_arg: Optional[str] = None) -> str:
    """
    Handles the 'useitem' command to use an item from the inventory.
    """
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        # Check if player is in a battle
        active_battle = await battle_service.get_player_active_battle(player_id)
        if active_battle:
             # If in battle, item usage might be different or restricted
             # TODO: Implement item usage logic specific to battle (S2 refinement)
             return "你正在战斗中，使用道具的逻辑尚未完全实现。" # Placeholder

        # If not in battle, use item outside of battle
        message = await item_service.use_item(player_id, item_identifier, target_arg)
        return message

    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except ItemNotFoundException:
        return f"ID为 {item_identifier} 的道具不存在。"
    except InsufficientItemException:
        return "你没有足够的该道具。"
    except PokemonNotFoundException:
        return f"未能找到ID为 {target_arg} 的宝可梦。"
    except Exception as e:
        logger.error(f"Error handling useitem command for player {player_id} with item {item_identifier}: {e}", exc_info=True)
        return "使用道具时发生错误，请稍后再试。"

async def handle_movepokemon_command(player_id: str, pokemon_instance_id: int, target_location: str) -> str:
    """
    Handles the 'movepokemon' command to move a pokemon between party and box.
    target_location should be 'party' or 'box'.
    """
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        # Check if player is in a battle
        active_battle = await battle_service.get_player_active_battle(player_id)
        if active_battle:
             # Cannot move pokemon between party/box during battle
             return "你正在战斗中，无法移动宝可梦！"

        if target_location.lower() == 'party':
            message = await pokemon_service.move_pokemon_to_party(player_id, pokemon_instance_id)
        elif target_location.lower() == 'box':
            message = await pokemon_service.move_pokemon_to_box(player_id, pokemon_instance_id)
        else:
            return "无效的目标位置。请指定 'party' 或 'box'。"

        return message

    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except PokemonNotInCollectionException:
        return f"ID为 {pokemon_instance_id} 的宝可梦不在你的收藏中。"
    except PartyFullException:
        return "你的队伍已满，无法将宝可梦移入队伍。"
    except Exception as e:
        logger.error(f"Error handling movepokemon command for player {player_id} pokemon {pokemon_instance_id} to {target_location}: {e}", exc_info=True)
        return "移动宝可梦时发生错误，请稍后再试。"

async def handle_sortparty_command(player_id: str, ordered_pokemon_ids: List[int]) -> str:
    """
    Handles the 'sortparty' command to reorder the player's party.
    """
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        # Check if player is in a battle
        active_battle = await battle_service.get_player_active_battle(player_id)
        if active_battle:
             # Cannot sort party during battle
             return "你正在战斗中，无法排序队伍！"

        message = await pokemon_service.sort_party(player_id, ordered_pokemon_ids)
        return message

    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except InvalidPartyOrderException as e:
        return f"队伍排序失败：{e}"
    except Exception as e:
        logger.error(f"Error handling sortparty command for player {player_id}: {e}", exc_info=True)
        return "排序队伍时发生错误，请稍后再试。"

async def handle_catch_command(player_id: str, pokemon_instance_id: int) -> str:
    """
    Handles the 'catch' command to attempt to catch the encountered wild pokemon.
    """
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        # Check if player is in a battle
        active_battle = await battle_service.get_player_active_battle(player_id)
        if not active_battle:
             return "当前没有可以捕获的野生宝可梦（你不在战斗中）。"

        # In battle, the wild pokemon instance ID is stored in the battle object
        wild_pokemon_instance_id = active_battle.wild_pokemon_instance_id

        # Attempt to catch the pokemon
        success, message = await pokemon_service.attempt_catch_pokemon(player, wild_pokemon_instance_id, pokemon_instance_id)

        # If battle ended (due to catch or other reason), end the battle session
        # Note: attempt_catch_pokemon might set battle.is_active = False if successful
        updated_battle = await battle_service.get_player_active_battle(player_id) # Re-fetch battle state
        if not updated_battle or not updated_battle.is_active:
             # Battle ended, perform cleanup if needed (e.g., remove wild pokemon instance if not caught)
             # TODO: Implement battle cleanup logic in BattleService (S2 refinement)
             pass # Cleanup handled by BattleService

        return message

    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except ItemNotFoundException:
        return f"ID为 {pokemon_instance_id} 的宝可梦球不存在。"
    except InsufficientItemException:
        # pokemon_service.attempt_catch_pokemon should return a specific message for this
        return "你没有足够的该宝可梦球。" # Fallback message
    except Exception as e:
        logger.error(f"Error handling catch command for player {player_id}: {e}", exc_info=True)
        return "尝试捕获时发生错误，请稍后再试。"


# --- New Battle Command Handler ---

async def handle_battle_command(player_id: str, command: str, args: List[str], active_battle: Battle) -> str:
    """
    Handles commands specifically during a battle.
    Delegates to the main handle_battle_command function which now takes active_battle.
    This is a routing function for clarity.
    """
    # The main handle_command function already routes battle commands here.
    # The logic is now within the main handle_battle_command function above.
    # This placeholder function is just for conceptual clarity in the command structure.
    pass # This function is effectively replaced by the logic in the main handle_command and the new handle_battle_command above.


# TODO: Add commands for interacting with NPCs, shops, etc. (S3 refinement) 