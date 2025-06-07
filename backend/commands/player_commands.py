from typing import List, Optional, Dict, Any, Tuple
from backend.core.services.player_service import PlayerService
from backend.core.services.pokemon_service import PokemonService
from backend.core.services.item_service import ItemService
from backend.core.services.map_service import MapService
from backend.core.services.battle_service import BattleService
from backend.core.services.dialog_service import DialogService
from backend.utils.logger import get_logger
from backend.utils.exceptions import (
    PlayerNotFoundException, InvalidPartyOrderException,
    PokemonNotInCollectionException, PartyFullException,
    ItemNotFoundException, InsufficientItemException,
    LocationNotFoundException, BattleNotFoundException,
    NoActivePokemonException, InvalidBattleActionException,
    SkillNotFoundException, PokemonFaintedException,
    InvalidTargetException, NotEnoughPokemonException,
    InvalidPokemonStateError,
    BattleFinishedException,
    InsufficientFundsException,
    DialogNotFoundException,
    PokemonNotFoundException
)
from backend.models.player import Player
from backend.models.pokemon import Pokemon
from backend.models.item import Item
from backend.models.battle import Battle
from backend.models.skill import Skill

logger = get_logger(__name__)

# 修改为使用依赖注入工厂模式
class ServiceProvider:
    """服务提供者，管理所有服务实例的单例访问。"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.player_service = PlayerService()
        self.pokemon_service = PokemonService()
        self.item_service = ItemService()
        self.map_service = MapService()
        self.battle_service = BattleService()
        self.dialog_service = DialogService()  # 添加对话服务

# 获取服务实例
service_provider = ServiceProvider.get_instance()
player_service = service_provider.player_service
pokemon_service = service_provider.pokemon_service
item_service = service_provider.item_service
map_service = service_provider.map_service
battle_service = service_provider.battle_service
dialog_service = service_provider.dialog_service

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
            # 回合跟踪逻辑已实现 - 通过 battle.current_turn_player_id 检查当前回合
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
                          # 通过 battle_service 提供的公共方法获取技能数据
                          skill = await self._battle_service.get_skill_data(skill_id)
                          if skill and ps.current_pp > 0:
                               break
                          elif skill and ps.current_pp <= 0:
                               raise InvalidBattleActionException(f"技能 {skill.name} 没有PP了！")
                          else:
                               # Should not happen if skill_id is valid and in pokemon's skills
                               raise InvalidBattleActionException(f"无法找到技能 {skill_id} 的数据。")

                if not skill:
                     raise InvalidBattleActionException(f"你的宝可梦不知道技能 {skill_id}。")

                # 验证目标宝可梦实例ID是否符合技能的目标类型
                if not skill:
                     raise InvalidBattleActionException(f"你的宝可梦不知道技能 {skill_id}。")

                # 根据技能的目标类型验证目标
                target_pokemon = None
                
                # 获取技能的目标类型
                target_type = skill.target_type  # 例如: "self", "opponent", "all", "ally"
                
                if target_type == "self":
                    # 自身为目标的技能
                    target_pokemon = player_active_pokemon
                    if target_pokemon_instance_id and target_pokemon_instance_id != player_active_pokemon.instance_id:
                        raise InvalidTargetException(f"技能 {skill.name} 只能以自身为目标。")
                    
                elif target_type == "opponent":
                    # 敌方为目标的技能
                    if target_pokemon_instance_id:
                        target_pokemon = await self._battle_service.get_pokemon_from_battle(battle, target_pokemon_instance_id)
                        # 验证目标是否为敌方宝可梦
                        if not target_pokemon or (battle.is_wild_battle and target_pokemon.instance_id != battle.wild_pokemon_instance_id):
                            raise InvalidTargetException(f"技能 {skill.name} 必须以敌方宝可梦为目标。")
                    else:
                        # 默认目标是野生宝可梦
                        target_pokemon = battle.wild_active_pokemon_instance
                        
                elif target_type == "ally":
                    # 友方为目标的技能（可以是自己或队友）
                    if not target_pokemon_instance_id:
                        # 默认以自身为目标
                        target_pokemon = player_active_pokemon
                    else:
                        target_pokemon = await self._battle_service.get_pokemon_from_battle(battle, target_pokemon_instance_id)
                        # 验证目标是否为友方宝可梦
                        if not target_pokemon or target_pokemon.owner_id != player_id:
                            raise InvalidTargetException(f"技能 {skill.name} 只能以友方宝可梦为目标。")
                
                elif target_type == "all":
                    # 全体目标的技能不需要指定目标
                    # 这里需要特殊处理，可能需要在战斗逻辑中应用效果到所有宝可梦
                    target_pokemon = battle.wild_active_pokemon_instance  # 默认以野生宝可梦为显示目标
                
                else:
                    # 未知的目标类型，使用默认逻辑
                    if target_pokemon_instance_id:
                        target_pokemon = await self._battle_service.get_pokemon_from_battle(battle, target_pokemon_instance_id)
                        if not target_pokemon:
                            raise InvalidTargetException(f"无效的目标宝可梦实例ID: {target_pokemon_instance_id}")
                    else:
                        # 默认目标是野生宝可梦
                        target_pokemon = battle.wild_active_pokemon_instance

                if not target_pokemon:
                    raise InvalidTargetException("技能需要一个有效的目标。")


                # S10, S11: Call BattleService to process skill action
                events, battle_ended, outcome = await self._battle_service.process_skill_action(
                    battle.battle_id, player_id, skill_id, target_pokemon.instance_id
                )

            elif action_type == "item":
                item_id = action.get("item_id")
                target_instance_id = action.get("target_instance_id")
                
                if item_id is None:
                    raise InvalidBattleActionException("使用物品需要指定物品ID。")
                
                # 验证玩家拥有该物品
                player = await battle_service.get_player(player_id)
                if not player or player.inventory.get(str(item_id), 0) <= 0:
                    raise InsufficientItemException(f"你没有道具ID为 {item_id} 的道具。")
                
                # 获取物品信息并验证是否可在战斗中使用
                item = await item_service.get_item(item_id)
                if not item:
                    raise ItemNotFoundException(f"道具ID {item_id} 不存在。")
                
                # 验证物品是否可在战斗中使用
                if item.use_target not in ["self_pet", "opponent_pet", "any_pet"]:
                    raise InvalidBattleActionException(f"道具 {item.name} 不能在战斗中使用。")
                
                # 处理道具使用
                action_events, battle_ended, outcome = await battle_service.process_item_action(
                    battle.battle_id, player_id, item_id, target_instance_id
                )
                
                events.extend(action_events)

            elif action_type == "switch":
                pokemon_instance_id = action.get("pokemon_instance_id")
                if pokemon_instance_id is None:
                    raise InvalidBattleActionException("Switch action requires 'pokemon_instance_id'.")

                # S15: Validate pokemon_instance_id (e.g., is this pokemon in the player's party? Is it not fainted? Is it not the current active pokemon?)
                player_party = await self._battle_service._get_player_party(player_id)
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
                item_id = action.get("item_id")
                if item_id is None:
                    raise InvalidBattleActionException("捕获行动需要指定精灵球道具ID。")
                
                # 验证道具ID是否为精灵球
                item = await item_service.get_item(item_id)
                if not item:
                    raise ItemNotFoundException(f"找不到ID为 {item_id} 的道具。")
                if item.effect_type != "capture":
                    raise InvalidBattleActionException(f"道具 {item.name} 不是精灵球，无法用于捕获宝可梦。")
                
                # 处理捕获行动
                events, battle_ended, outcome = await self._battle_service.process_catch_action(
                    battle.battle_id, player_id, item_id
                )

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

    async def parse_action_from_command(self, player_id: str, command: str, args: List[str], battle: Battle) -> Dict[str, Any]:
        """
        将聊天命令解析为行动字典格式。
        
        Args:
            player_id: 玩家ID
            command: 命令名称（如fight, use, switch等）
            args: 命令参数列表
            battle: 当前战斗对象
            
        Returns:
            符合handle_player_action要求的行动字典
            
        Raises:
            InvalidBattleActionException: 当命令格式无效或参数不足时
            SkillNotFoundException: 当找不到指定的技能时
            ItemNotFoundException: 当找不到指定的道具时
        """
        action = {"type": ""}
        
        if command == "fight" or command == "skill":
            # 解析战斗技能命令
            if not args:
                raise InvalidBattleActionException("请指定要使用的技能ID或名称。")
            
            # 尝试查找技能（按ID或名称）
            try:
                skill_id = int(args[0])
                # 通过ID查找技能
                skill = await self._battle_service.get_skill_data(skill_id)
                if not skill:
                    raise SkillNotFoundException(f"找不到ID为 {skill_id} 的技能。")
            except ValueError:
                # 输入不是数字，尝试按名称查找
                skill_name = args[0]
                # 获取玩家当前的宝可梦
                player_pokemon = battle.player_active_pokemon_instance
                if not player_pokemon:
                    raise NoActivePokemonException("你没有派出宝可梦。")
                
                # 查找玩家宝可梦拥有的与输入名称匹配的技能
                skill = None
                skill_id = None
                for s in player_pokemon.skills:
                    if s.name.lower() == skill_name.lower():
                        skill = s
                        skill_id = s.skill_id
                        break
                
                if not skill:
                    raise SkillNotFoundException(f"你的宝可梦没有名为 '{skill_name}' 的技能。")
            
            # 确定目标
            target_pokemon_instance_id = None
            if len(args) > 1:
                try:
                    target_pokemon_instance_id = int(args[1])
                except ValueError:
                    # 如果目标参数不是数字，则使用默认目标（对手的宝可梦）
                    if battle.is_wild_battle:
                        target_pokemon_instance_id = battle.wild_pokemon_instance_id
                    else:
                        target_pokemon_instance_id = battle.opponent_active_pokemon_instance_id
            else:
                # 默认目标是对手的宝可梦
                if battle.is_wild_battle:
                    target_pokemon_instance_id = battle.wild_pokemon_instance_id
                else:
                    target_pokemon_instance_id = battle.opponent_active_pokemon_instance_id
            
            action = {
                "type": "skill",
                "skill_id": skill_id,
                "target_pokemon_instance_id": target_pokemon_instance_id
            }
            
        elif command == "use" or command == "item":
            # 解析使用道具命令
            if not args:
                raise InvalidBattleActionException("请指定要使用的道具ID。")
            
            try:
                item_id = int(args[0])
            except ValueError:
                raise InvalidBattleActionException("道具ID必须是一个数字。")
            
            # 确定目标
            target_type = "player_pokemon"  # 默认目标是自己的宝可梦
            target_id = battle.player_active_pokemon_instance_id
            
            if len(args) >= 3:
                target_type = args[1]
                try:
                    target_id = int(args[2])
                except ValueError:
                    raise InvalidBattleActionException("目标ID必须是一个数字。")
            
            if target_type not in ["player_pokemon", "wild_pokemon"]:
                raise InvalidBattleActionException("无效的目标类型。有效的目标类型: player_pokemon, wild_pokemon")
            
            # 如果目标是野生宝可梦，使用野生宝可梦ID
            if target_type == "wild_pokemon":
                if not battle.wild_pokemon_instance_id:
                    raise InvalidBattleActionException("当前战斗没有野生宝可梦。")
                target_id = battle.wild_pokemon_instance_id
            
            action = {
                "type": "item",
                "item_id": item_id,
                "target_instance_id": target_id
            }
            
        elif command == "switch":
            # 解析切换宝可梦命令
            if not args:
                raise InvalidBattleActionException("请指定要切换的宝可梦ID。")
            
            try:
                pokemon_instance_id = int(args[0])
            except ValueError:
                raise InvalidBattleActionException("宝可梦ID必须是一个数字。")
            
            action = {
                "type": "switch",
                "pokemon_instance_id": pokemon_instance_id
            }
            
        elif command == "run":
            # 解析逃跑命令
            action = {"type": "run"}
            
        elif command == "catch":
            # 解析捕获命令
            if len(args) != 1:
                raise InvalidBattleActionException("用法: catch <精灵球道具ID>")
                
            try:
                item_id = int(args[0])
                # 验证道具ID是否为精灵球
                service_provider = ServiceProvider.get_instance()
                item_service = service_provider.item_service
                item = await item_service.get_item(item_id)
                
                if not item:
                    raise ItemNotFoundException(f"找不到ID为 {item_id} 的道具。")
                    
                if item.effect_type != "capture":
                    raise InvalidBattleActionException(f"道具 {item.name} 不是精灵球，无法用于捕获宝可梦。")
                
                action = {"type": "catch", "item_id": item_id}
            except ValueError:
                raise InvalidBattleActionException("道具ID必须是数字。")
            
        else:
            raise InvalidBattleActionException(f"未知的战斗命令：{command}")
        
        return action

async def handle_addpokemon_command(player_id: str, pokemon_race_id: int) -> str:
    """
    处理添加宝可梦的调试命令。
    格式: addpokemon <宝可梦种族ID>
    注意：这是一个调试命令，在生产环境中应该被移除或限制使用。
    """
    try:
        # 检查玩家是否存在
        player = await player_service.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")
        
        # 检查玩家是否在战斗中
        active_battle = await battle_service.get_player_active_battle(player_id)
        if active_battle:
            return "你正在战斗中，无法添加宝可梦！"
        
        # 生成一个随机等级（1-20级用于调试）
        import random
        level = random.randint(1, 20)
        
        # 创建宝可梦实例并添加到玩家收藏
        new_pokemon = await pokemon_service.create_pokemon_instance(
            race_id=pokemon_race_id,
            level=level,
            player_id=player_id
        )
        
        if new_pokemon:
            # 尝试将宝可梦添加到队伍中，如果队伍已满则添加到盒子
            try:
                await pokemon_service.add_pokemon_to_party(player_id, new_pokemon.instance_id)
                location = "队伍"
            except PartyFullException:
                await pokemon_service.add_pokemon_to_box(player_id, new_pokemon.instance_id)
                location = "宝可梦盒"
            
            return f"成功添加了一只 Lv.{level} 的宝可梦（种族ID: {pokemon_race_id}）到你的{location}中！"
        else:
            return "添加宝可梦失败，请检查种族ID是否有效。"
        
    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except Exception as e:
        logger.error(f"处理添加宝可梦命令时发生错误: {e}", exc_info=True)
        return "添加宝可梦时发生错误，请稍后再试。"

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
        elif command == 'status':
            return await handle_battle_status_command(player_id, args)
        elif command == 'talk':
            return await handle_talk_command(player_id, args)
        elif command == 'shop':
            return await handle_shop_command(player_id, args)
        else:
            return f"未知命令 '{command}'。使用 'help' 查看所有可用命令。"

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

async def handle_fight_command(player_id: str, args: List[str]) -> str:
    """
    处理玩家在战斗中使用技能的命令。
    格式: fight <技能ID或技能名称> [目标ID]
    """
    try:
        # 获取玩家当前的战斗
        battle = await battle_service.get_player_active_battle(player_id)
        if not battle:
            return "你当前没有处于战斗中。"
        
        if battle.current_turn_player_id != player_id:
            return "当前不是你的回合，无法使用技能。"
        
        # 创建 PlayerCommands 实例来解析命令
        player_commands = PlayerCommands(battle_service)
        
        # 解析战斗命令为行动字典
        action = await player_commands.parse_action_from_command(
            player_id, "fight", args, battle
        )
        
        # 执行战斗行动
        battle_outcome = await player_commands.handle_player_action(player_id, action)
        
        # 解析战斗结果
        messages = battle_outcome.get("messages", [])
        message_text = "\n".join([
            msg.message if hasattr(msg, 'message') else str(msg) 
            for msg in messages
        ])
        
        return message_text or "使用了技能。"
        
    except InvalidBattleActionException as e:
        return str(e)
    except SkillNotFoundException as e:
        return str(e)
    except NoActivePokemonException as e:
        return str(e)
    except Exception as e:
        logger.error(f"处理战斗技能命令时发生错误: {e}", exc_info=True)
        return "使用技能时发生错误，请稍后再试。"

async def handle_battle_command(player_id: str, command: str, args: List[str], active_battle: Battle) -> str:
    """
    处理战斗中的特定命令。
    将命令委托给相应的处理函数。
    """
    # 根据命令类型路由到对应的处理函数
    if command == "fight":
        return await handle_fight_command(player_id, args)
    elif command == "run":
        return await handle_run_command(player_id, args)
    elif command == "catch":
        return await handle_catch_command(player_id, args)
    elif command == "use":
        return await handle_use_battle_item_command(player_id, args)
    elif command == "switch":
        return await handle_switch_pokemon_command(player_id, args)
    elif command == "status":
        return await handle_battle_status_command(player_id, args)
    else:
        return f"在战斗中不能使用 '{command}' 命令。可用命令: fight, run, catch, use, switch, status"

async def handle_switch_pokemon_command(player_id: str, args: List[str]) -> str:
    """
    处理玩家在战斗中切换宝可梦的命令。
    格式: switch <宝可梦实例ID>
    """
    try:
        # 获取玩家当前的战斗
        battle = await battle_service.get_player_active_battle(player_id)
        if not battle:
            return "你当前没有处于战斗中。"
        
        if battle.current_turn_player_id != player_id:
            return "当前不是你的回合，无法切换宝可梦。"
        
        # 创建 PlayerCommands 实例来解析命令
        player_commands = PlayerCommands(battle_service)
        
        # 解析战斗命令为行动字典
        action = await player_commands.parse_action_from_command(
            player_id, "switch", args, battle
        )
        
        # 执行战斗行动
        battle_outcome = await player_commands.handle_player_action(player_id, action)
        
        # 解析战斗结果
        messages = battle_outcome.get("messages", [])
        message_text = "\n".join([
            msg.message if hasattr(msg, 'message') else str(msg) 
            for msg in messages
        ])
        
        return message_text or "切换了宝可梦。"
        
    except InvalidBattleActionException as e:
        return str(e)
    except PokemonFaintedException as e:
        return str(e)
    except NoActivePokemonException as e:
        return str(e)
    except Exception as e:
        logger.error(f"处理切换宝可梦命令时发生错误: {e}", exc_info=True)
        return "切换宝可梦时发生错误，请稍后再试。"

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

        return "\n".join(messages)

    except PlayerNotFoundException:
        return "你还没有开始游戏，请先使用 'start [你的名字]' 命令开始游戏。"
    except Exception as e:
        logger.error(f"Error handling box command for player {player_id}: {e}", exc_info=True)
        return "查询宝可梦盒子时发生错误，请稍后再试。"



async def handle_useitem_command(player_id: str, item_identifier: str, target_arg: Optional[str] = None) -> str:
    """
    处理'useitem'命令，使用背包中的道具。
    """
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        # 检查玩家是否在战斗中
        active_battle = await battle_service.get_player_active_battle(player_id)
        if active_battle:
            # 在战斗中使用道具需要通过战斗系统处理
            # 将参数转换为handle_use_battle_item_command所需的格式
            try:
                item_id = int(item_identifier)
                args = [str(item_id)]
                
                if target_arg:
                    # 如果有目标参数，添加适当的目标类型和ID
                    # 默认目标是玩家的宝可梦
                    args.append("player_pokemon")
                    args.append(target_arg)
                
                return await handle_use_battle_item_command(player_id, args)
            except ValueError:
                return f"道具ID '{item_identifier}' 必须是一个数字。"

        # 如果不在战斗中，使用常规道具逻辑
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
        logger.error(f"处理使用道具命令时发生错误: {e}", exc_info=True)
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
        updated_battle = await battle_service.get_player_active_battle(player_id)  # 重新获取战斗状态
        if not updated_battle or not updated_battle.is_active:
             # 战斗已结束，执行必要的清理（例如，如果未捕获则删除野生宝可梦实例）
             if updated_battle:
                 await battle_service.cleanup_battle(updated_battle.battle_id, success)  # 传递捕获结果
             
             # 清理已经由 BattleService 处理
             pass

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


# --- NPC 和商店交互命令 ---

async def handle_talk_command(player_id: str, args: List[str]) -> str:
    """
    处理与 NPC 对话的命令。
    格式: talk <NPC ID>
    """
    service_provider = ServiceProvider.get_instance()
    dialog_service = service_provider.dialog_service
    player_service = service_provider.player_service
    
    try:
        if not args or len(args) < 1:
            return "用法: talk <NPC ID>"
        
        try:
            npc_id = int(args[0])
        except ValueError:
            return "NPC ID 必须是一个数字。"
        
        # 获取玩家当前位置
        player = await player_service.get_player(player_id)
        if not player:
            return "找不到玩家信息。"
        
        # 检查 NPC 是否在玩家当前位置
        dialog_result = await dialog_service.start_dialog(player_id, npc_id)
        return dialog_result.message
        
    except Exception as e:
        logger.error(f"处理对话命令时发生错误: {e}", exc_info=True)
        return "与 NPC 对话时发生错误，请稍后再试。"


async def handle_shop_command(player_id: str, args: List[str]) -> str:
    """
    处理商店交互的命令。
    格式: shop <NPC ID> [buy/list] [商品ID] [数量]
    """
    service_provider = ServiceProvider.get_instance()
    item_service = service_provider.item_service
    player_service = service_provider.player_service
    dialog_service = service_provider.dialog_service
    
    try:
        if not args or len(args) < 1:
            return "用法: shop <NPC ID> [buy/list] [商品ID] [数量]"
        
        try:
            npc_id = int(args[0])
        except ValueError:
            return "NPC ID 必须是一个数字。"
        
        # 获取玩家当前位置
        player = await player_service.get_player(player_id)
        if not player:
            return "找不到玩家信息。"
        
        # 检查商店 NPC 是否在玩家当前位置
        shop_info = await dialog_service.get_shop_info(npc_id)
        if not shop_info:
            return f"ID 为 {npc_id} 的 NPC 不是商店。"
            
        shop_name = shop_info.get("name", "商店")
        
        # 默认显示商品列表
        action = "list"
        if len(args) >= 2:
            action = args[1].lower()
        
        if action == "list":
            # 显示商品列表
            shop_items = await item_service.get_shop_items(npc_id)
            if not shop_items:
                return f"{shop_name}目前没有商品出售。"
                
            items_display = [f"{item.item_id}. {item.name} - {item.price}金币：{item.description}" for item in shop_items]
            return f"{shop_name}的商品列表：\n" + "\n".join(items_display) + "\n\n使用 shop {npc_id} buy <商品ID> [数量] 命令购买商品。"
        elif action == "buy":
            # 购买商品
            if len(args) < 3:
                return "请指定要购买的商品ID。"
                
            try:
                item_id = int(args[2])
                quantity = 1
                if len(args) >= 4:
                    quantity = int(args[3])
                    if quantity <= 0:
                        return "购买数量必须大于0。"
            except ValueError:
                return "商品ID和数量必须是数字。"
                
            # 执行购买
            purchase_result = await item_service.purchase_item(player_id, npc_id, item_id, quantity)
            return f"{shop_name}：{purchase_result}"
        else:
            return f"未知的商店操作 '{action}'。可用操作: list, buy"
            
    except Exception as e:
        logger.error(f"处理商店命令时发生错误: {e}", exc_info=True)
        return "与商店交互时发生错误，请稍后再试。"


# --- New Battle Command Handler ---

async def handle_run_command(player_id: str, args: List[str]) -> str:
    """
    处理玩家尝试从战斗中逃跑的命令。
    格式: run
    """
    try:
        # 获取玩家当前的战斗
        battle = await battle_service.get_player_active_battle(player_id)
        if not battle:
            return "你当前没有处于战斗中。"
        
        if battle.current_turn_player_id != player_id:
            return "当前不是你的回合，无法逃跑。"
        
        # 处理逃跑行为
        success_chance, messages, battle_ended = await battle_service.process_player_action(
            battle.battle_id,
            player_id,
            {
                "action_type": "run"
            }
        )
        
        # 如果战斗结束（由于逃跑成功），清理战斗会话
        if battle_ended:
            updated_battle = await battle_service.get_player_active_battle(player_id)
            if updated_battle and not updated_battle.is_active:
                await battle_service.cleanup_battle(updated_battle.battle_id)
        
        return "\n".join(messages)
        
    except BattleNotFoundException:
        return "找不到当前战斗。"
    except InvalidBattleActionException as e:
        return str(e)
    except Exception as e:
        logger.error(f"处理逃跑命令时发生错误: {e}", exc_info=True)
        return "尝试逃跑时发生错误，请稍后再试。"

async def handle_use_battle_item_command(player_id: str, args: List[str]) -> str:
    """
    处理玩家在战斗中使用道具的命令。
    格式: use <道具ID> [目标类型] [目标ID]
    目标类型: player_pokemon, wild_pokemon
    """
    service_provider = ServiceProvider.get_instance()
    battle_service = service_provider.battle_service
    item_service = service_provider.item_service
    
    try:
        if not args or len(args) < 1:
            return "请指定要使用的道具ID。"
        
        try:
            item_id = int(args[0])
        except ValueError:
            return "道具ID必须是一个数字。"
        
        # 获取玩家当前的战斗
        battle = await battle_service.get_player_active_battle(player_id)
        if not battle:
            return "你当前没有处于战斗中。"
        
        if battle.current_turn_player_id != player_id:
            return "当前不是你的回合，无法使用道具。"
        
        # 检查玩家是否有该道具
        has_item = await item_service.check_player_has_item(player_id, item_id)
        if not has_item:
            return "你没有指定的道具。"
        
        # 获取道具信息
        item = await item_service.get_item(item_id)
        if not item:
            return f"道具 {item_id} 不存在。"
        
        # 检查道具是否可在战斗中使用
        if not item.battle_usable:
            return f"道具 {item.name} 不能在战斗中使用。"
        
        # 确定使用目标
        target_type = "player_pokemon"  # 默认目标是自己的宝可梦
        target_id = battle.player_active_pokemon_instance_id
        
        if len(args) >= 3:
            target_type = args[1]
            try:
                target_id = int(args[2])
            except ValueError:
                raise InvalidBattleActionException("目标ID必须是一个数字。")
        
        # 验证目标类型
        if target_type not in ["player_pokemon", "wild_pokemon"]:
            raise InvalidBattleActionException("无效的目标类型。有效的目标类型: player_pokemon, wild_pokemon")
        
        # 如果目标是野生宝可梦，使用野生宝可梦ID
        if target_type == "wild_pokemon":
            if not battle.wild_pokemon_instance_id:
                raise InvalidBattleActionException("当前战斗没有野生宝可梦。")
            target_id = battle.wild_pokemon_instance_id
            
        # 处理使用道具行为
        action = {
            "action_type": "item",
            "item_id": item_id,
            "target_instance_id": target_id
        }

        # 创建 PlayerCommands 实例并调用方法
        player_commands = PlayerCommands(battle_service)
        battle_outcome = await player_commands.handle_player_action(player_id, action)

        
        # 解析战斗结果
        messages = battle_outcome.get("messages", [])
        message_text = "\n".join([msg.message if hasattr(msg, 'message') else str(msg) for msg in messages])
        
        return message_text or f"使用了 {item.name}。"
        
    except Exception as e:
        logger.error(f"处理战斗中使用道具命令时发生错误: {e}", exc_info=True)
        return "使用道具时发生错误，请稍后再试。"

async def handle_replace_skill_command(player_id: str, args: List[str]) -> str:
    """
    处理玩家替换宝可梦技能的命令。
    格式: replace_skill [宝可梦实例ID] [要替换的技能ID] [新技能ID]
    """
    try:
        if len(args) < 3:
            return "请提供宝可梦实例ID、要替换的技能ID和新技能ID。"
        
        try:
            pokemon_instance_id = int(args[0])
            old_skill_id = int(args[1])
            new_skill_id = int(args[2])
        except ValueError:
            return "宝可梦实例ID和技能ID必须是数字。"
        
        # 获取玩家宝可梦
        pokemon = await pokemon_service.get_pokemon_by_id(pokemon_instance_id)
        if not pokemon:
            return f"找不到ID为 {pokemon_instance_id} 的宝可梦。"
        
        # 验证这个宝可梦属于该玩家
        if pokemon.player_id != player_id:
            return "这不是你的宝可梦。"
        
        # 验证宝可梦有这个技能
        has_old_skill = False
        for skill in pokemon.skills:
            if skill.skill_id == old_skill_id:
                has_old_skill = True
                break
        
        if not has_old_skill:
            return f"该宝可梦没有ID为 {old_skill_id} 的技能。"
        
        # 验证新技能是否存在
        new_skill = await battle_service.get_skill_data(new_skill_id)
        if not new_skill:
            return f"找不到ID为 {new_skill_id} 的技能。"
        
        # 替换技能
        result = await pokemon_service.replace_pokemon_skill(
            pokemon_instance_id, 
            old_skill_id, 
            new_skill_id
        )
        
        return f"成功将 {pokemon.nickname} 的技能替换为 {new_skill.name}！"
        
    except PokemonNotInCollectionException:
        return "该宝可梦不属于你的收藏。"
    except SkillNotFoundException:
        return "找不到指定的技能。"
    except Exception as e:
        logger.error(f"处理技能替换命令时发生错误: {e}", exc_info=True)
        return "替换技能时发生错误，请稍后再试。"

async def handle_bag_command(player_id: str, args: List[str]) -> str:
    """
    处理查看背包的命令。
    格式: bag
    """
    try:
        player = await player_service.get_player(player_id)
        if not player:
            return "找不到玩家信息。"
        
        # 检查玩家是否在战斗中
        battle = await battle_service.get_player_active_battle(player_id)
        
        if battle:
            # 玩家在战斗中，只显示战斗中可用的道具
            battle_usable_items = []
            
            for item_id_str, count in player.inventory.items():
                if count > 0:
                    item_id = int(item_id_str)
                    item = await item_service.get_item(item_id)
                    
                    # 检查道具是否可在战斗中使用
                    if item and item.battle_usable:
                        battle_usable_items.append(f"{item.item_id}. {item.name} x{count} - {item.description}")
            
            if battle_usable_items:
                return "你的战斗背包：\n" + "\n".join(battle_usable_items) + "\n\n使用 use <道具ID> [目标类型] [目标ID] 命令使用道具。"
            else:
                return "你的背包中没有可在战斗中使用的道具。"
        else:
            # 玩家不在战斗中，显示所有道具
            # 已有代码...
            pass

    except PlayerNotFoundException:
        return "找不到玩家信息。"
    except Exception as e:
        logger.error(f"Error handling bag command for player {player_id}: {e}", exc_info=True)
        return "查询背包时发生错误，请稍后再试。"

async def handle_battle_status_command(player_id: str, args: List[str]) -> str:
    """
    显示当前战斗状态的详细信息。
    格式: status
    """
    try:
        battle = await battle_service.get_player_active_battle(player_id)
        if not battle:
            return "你当前没有处于战斗中。"
        
        # 获取玩家宝可梦信息
        player_pokemon = battle.player_active_pokemon_instance
        if not player_pokemon:
            return "你没有派出任何宝可梦。"
        
        # 获取对手宝可梦信息
        opponent_pokemon = battle.wild_active_pokemon_instance if battle.is_wild_battle else battle.opponent_active_pokemon_instance
        if not opponent_pokemon:
            return "对手没有派出任何宝可梦。"
        
        # 构建状态信息
        battle_info = [
            f"【战斗状态】",
            f"战斗类型: {'野生宝可梦战斗' if battle.is_wild_battle else '训练师战斗'}",
            f"当前回合: {battle.current_turn}",
            f"当前行动方: {'你' if battle.current_turn_player_id == player_id else '对手'}",
            f"\n【你的宝可梦】",
            f"{player_pokemon.nickname or player_pokemon.name} (Lv.{player_pokemon.level})",
            f"HP: {player_pokemon.current_hp}/{player_pokemon.max_hp}",
            f"状态: {player_pokemon.status_condition or '正常'}"
        ]
        
        # 添加玩家宝可梦的状态效果
        if player_pokemon.status_effects:
            battle_info.append("状态效果:")
            for effect in player_pokemon.status_effects:
                battle_info.append(f"- {effect.name}: {effect.description} (剩余回合: {effect.remaining_turns})")
        
        battle_info.extend([
            f"\n【对手宝可梦】",
            f"{opponent_pokemon.name} (Lv.{opponent_pokemon.level})",
            f"HP: {opponent_pokemon.current_hp}/{opponent_pokemon.max_hp}",
            f"状态: {opponent_pokemon.status_condition or '正常'}"
        ])
        
        # 添加对手宝可梦的状态效果
        if opponent_pokemon.status_effects:
            battle_info.append("状态效果:")
            for effect in opponent_pokemon.status_effects:
                battle_info.append(f"- {effect.name}: {effect.description} (剩余回合: {effect.remaining_turns})")
        
        # 添加场地效果
        if battle.field_effects:
            battle_info.append("\n【场地效果】")
            for effect in battle.field_effects:
                battle_info.append(f"- {effect.name}: {effect.description} (剩余回合: {effect.remaining_turns})")
        
        return "\n".join(battle_info)
        
    except Exception as e:
        logger.error(f"获取战斗状态时发生错误: {e}", exc_info=True)
        return "获取战斗状态时发生错误，请稍后再试。"

async def handle_encounter(player_id: str, wild_pokemon: Pokemon) -> str:
    """处理野外遇敌事件"""
    service_provider = ServiceProvider.get_instance()
    player_service = service_provider.player_service
    battle_service = service_provider.battle_service
    
    try:
        # 获取玩家信息
        player = await player_service.get_player(player_id)
        if not player:
            return "找不到玩家信息。"
        
        # 检查玩家是否有可用宝可梦
        if not player.party_pokemon_ids:
            # 玩家没有宝可梦，野生宝可梦逃跑
            return f"一只野生的 {wild_pokemon.name} (Lv.{wild_pokemon.level}) 出现了！但你没有宝可梦，它很快就跑掉了。"
        
        # 检查玩家的宝可梦是否都已失去战斗能力
        party_pokemon = await player_service.get_player_party(player_id)
        active_pokemon = None
        
        for pokemon in party_pokemon:
            if pokemon.current_hp > 0:
                active_pokemon = pokemon
                break
        
        if not active_pokemon:
            # 玩家的所有宝可梦都已失去战斗能力
            return f"一只野生的 {wild_pokemon.name} (Lv.{wild_pokemon.level}) 出现了！但你的所有宝可梦都已失去战斗能力，它很快就跑掉了。"
        
        # 创建战斗
        battle_id = await battle_service.create_wild_battle(player_id, wild_pokemon.instance_id, active_pokemon.instance_id)
        
        # 返回战斗开始信息
        return f"一只野生的 {wild_pokemon.name} (Lv.{wild_pokemon.level}) 出现了！\n{active_pokemon.nickname or active_pokemon.name}，就决定是你了！\n\n使用 'fight <技能ID>' 命令战斗，或使用 'run' 尝试逃跑。"
        
    except Exception as e:
        logger.error(f"处理遇敌时发生错误: {e}", exc_info=True)
        return "处理遇敌时发生错误，请稍后再试。"
