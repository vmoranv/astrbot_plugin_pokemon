from typing import Optional, Dict, Any, List, Tuple
from backend.models.player import Player
from backend.models.pokemon import Pokemon, PokemonSkill
from backend.models.battle import Battle
from backend.models.skill import Skill # Import Skill model
from backend.models.item import Item # Import Item model
from backend.data_access.repositories.player_repository import PlayerRepository
from backend.data_access.repositories.pokemon_repository import PokemonRepository
from backend.data_access.repositories.battle_repository import BattleRepository # Assuming BattleRepository exists or will be created
from backend.data_access.repositories.metadata_repository import MetadataRepository # Need MetadataRepository for skills and items
from backend.core.battle.battle_logic import BattleLogic # Import BattleLogic
from backend.core.services.item_service import ItemService # Import ItemService for item usage
from backend.utils.logger import get_logger
from backend.utils.exceptions import (
    BattleNotFoundException, InvalidBattleActionException,
    PokemonFaintedException, SkillNotFoundException,
    InvalidTargetException, NotEnoughPokemonException,
    BattleFinishedException, ItemNotFoundException, InvalidItemException, # Import ItemNotFoundException and InvalidItemException
    PreventSwitchException, PlayerNotFoundException
)
from backend.core.battle.events import (
    BattleStartEvent, BattleEndEvent, BattleMessageEvent,
    PokemonSwitchEvent, DamageDealtEvent, FaintEvent,
    ExpGainEvent, EvolutionAvailableEvent, StatusEffectAppliedEvent,
    StatusEffectRemovedEvent, StatStageChangeEvent, SwitchOutEvent,
    SwitchInEvent, HealEvent, AbilityTriggerEvent, ItemTriggerEvent,
    MoveMissedEvent, SkillReplacementRequiredEvent, PokemonEvolvedEvent,
    SkillLearnedEvent,
    AttackEvent, DamageEvent, MissEvent, CriticalHitEvent,
    TypeEffectivenessEvent, StatusEffectEvent, WildPokemonFledEvent
)
from backend.models.item import ItemEffectType
from backend.core.battle import calculations  # 如果该模块存在
# 添加以下导入
from backend.models.event import (
    BattleEvent, PokemonFaintEvent, PokemonSwitchRequiredEvent,
    AbilityTriggeredEvent, ItemUseEvent, PokemonCaughtEvent,
    PokemonStoredEvent, CaptureFailEvent, ItemUsedEvent
)
from backend.utils.exceptions import PokemonNotFoundException
import random
from datetime import datetime
from backend.core.pet import pet_skill
from backend.core.battle.formulas import calculate_stats

logger = get_logger(__name__)

class BattleService:
    """Service for managing battle sessions and orchestrating battle logic."""

    def __init__(
        self,
        player_repo: Optional[PlayerRepository] = None,
        pokemon_repo: Optional[PokemonRepository] = None,
        battle_repo: Optional[BattleRepository] = None,
        metadata_repo: Optional[MetadataRepository] = None,
        item_service: Optional[ItemService] = None,
        battle_logic: Optional[BattleLogic] = None
    ):
        """
        初始化战斗服务。
        
        Args:
            player_repo: 玩家数据仓库，如果为None则创建默认实例
            pokemon_repo: 宝可梦数据仓库，如果为None则创建默认实例
            battle_repo: 战斗数据仓库，如果为None则创建默认实例
            metadata_repo: 元数据仓库，如果为None则创建默认实例
            item_service: 道具服务，如果为None则创建默认实例
            battle_logic: 战斗逻辑处理器，如果为None则创建默认实例
        """
        self.player_repo = player_repo or PlayerRepository()
        self.pokemon_repo = pokemon_repo or PokemonRepository()
        self.battle_repo = battle_repo or BattleRepository()
        self.metadata_repo = metadata_repo or MetadataRepository()
        self.item_service = item_service or ItemService()
        # 如果未提供battle_logic，则创建一个实例并传入metadata_repo
        self.battle_logic = battle_logic or BattleLogic(metadata_repo=self.metadata_repo)


    async def start_wild_pokemon_battle(self, player_id: str, wild_pokemon_race_id: int, wild_pokemon_level: int) -> Tuple[List[str], Optional[str], List[Any]]:
        """Starts a battle between a player and a wild pokemon."""
        logger.info(f"Attempting to start wild pokemon battle for player {player_id} against race {wild_pokemon_race_id} level {wild_pokemon_level}")
        messages = []
        events = []  # 初始化事件列表用于收集战斗事件
        try:
            player = await self.player_repo.get_player(player_id)
            if not player:
                raise PlayerNotFoundException(f"Player with ID {player_id} not found.")

            # Check if player is already in a battle
            if player.battle_id:
                 messages.append("你已经在战斗中！")
                 return messages, None, events # Player is already in a battle

            # Get player's party
            player_party = await self.pokemon_repo.get_player_pokemons(player_id)
            if not player_party:
                 messages.append("你没有宝可梦可以战斗！")
                 return messages, None, events # Player has no pokemon

            # Find the first available pokemon in the party
            active_pokemon = None
            for pokemon in player_party:
                 if not pokemon.is_fainted:
                      active_pokemon = pokemon
                      break

            if not active_pokemon:
                 messages.append("你的所有宝可梦都已濒死，无法开始战斗！")
                 return messages, None, events # All pokemon fainted

            # Create a wild pokemon instance
            # Need race data to create the instance
            wild_race_data = self.metadata_repo.get_race_by_id(wild_pokemon_race_id)
            if not wild_race_data:
                 logger.error(f"Wild pokemon race ID {wild_pokemon_race_id} not found in metadata.")
                 messages.append("无法找到该野生宝可梦的数据。")
                 return messages, None, events

            # Create the wild pokemon instance
            wild_pokemon = Pokemon(
                player_id=None, # Wild pokemon has no owner
                race_id=wild_pokemon_race_id,
                nickname=wild_race_data.name, # Use race name as nickname for wild pokemon
                level=wild_pokemon_level,
                # IVs and EVs are randomly generated by default in Pokemon model
            )

            # Load race data into the pokemon instance and calculate initial stats
            wild_pokemon.race = wild_race_data
            calculate_stats(wild_pokemon, wild_pokemon.race, self.metadata_repo) # Calculate initial stats
            wild_pokemon.current_hp = wild_pokemon.max_hp # Start with full HP

            # Save the wild pokemon instance to get an instance_id
            wild_pokemon_instance_id = await self.pokemon_repo.save_pokemon_instance(wild_pokemon)
            wild_pokemon.instance_id = wild_pokemon_instance_id # Set the instance_id on the object

            # Load race data for player's active pokemon as well
            if not active_pokemon.race:
                 active_pokemon.race = self.metadata_repo.get_race_by_id(active_pokemon.race_id)
                 if active_pokemon.race:
                      calculate_stats(active_pokemon, active_pokemon.race, self.metadata_repo)
                      # Initialize current HP if it's None after loading
                      if active_pokemon.current_hp is None and active_pokemon.max_hp is not None:
                           active_pokemon.current_hp = active_pokemon.max_hp
                 else:
                      logger.error(f"Could not load race data for player pokemon {active_pokemon.nickname} (ID: {active_pokemon.race_id}).")
                      messages.append(f"无法加载 {active_pokemon.nickname} 的种族数据。")
                      await self.pokemon_repo.delete_pokemon_instance(wild_pokemon_instance_id)
                      return messages, None, events

            # Create a new battle instance
            battle = Battle(
                player_id=player_id,
                wild_pokemon_instance_id=wild_pokemon.instance_id,
                player_active_pokemon_instance_id=active_pokemon.instance_id,
                turn_number=1,
                is_finished=False,
                outcome=None,
                # Initialize other battle state fields as needed
                player_party_instance_ids=[p.instance_id for p in player_party], # Store party instance IDs
                wild_pokemon_original_race_id=wild_pokemon_race_id, # Store original race ID for EXP/Catch rate
                wild_pokemon_original_level=wild_pokemon_level, # Store original level for EXP
            )

            # Save the battle instance
            battle_id = await self.battle_repo.save_battle(battle)
            battle.battle_id = battle_id # Set the battle_id on the object

            # Link the battle to the player
            player.battle_id = battle_id
            await self.player_repo.save_player(player)

            messages.append(f"你遇到了野生的 {wild_pokemon.nickname} (Lv.{wild_pokemon.level})！")
            messages.append(f"你派出了 {active_pokemon.nickname}！")
            
            # 发布战斗开始事件
            battle_start_event = BattleStartEvent(
                battle_id=battle.battle_id,
                player_id=player_id,
                player_pokemon_id=active_pokemon.instance_id,
                player_pokemon_name=active_pokemon.nickname,
                wild_pokemon_id=wild_pokemon.instance_id,
                wild_pokemon_name=wild_pokemon.nickname,
                wild_pokemon_level=wild_pokemon.level,
                message=messages[-2]
            )
            events.append(battle_start_event)

            return messages, None, events # Battle started, not finished yet

        except PlayerNotFoundException as e:
            logger.warning(f"Failed to start battle: {e}")
            messages.append(str(e))
            return messages, None, events
        except Exception as e:
            logger.error(f"An unexpected error occurred while starting battle for player {player_id}: {e}", exc_info=True)
            messages.append("开始战斗时发生未知错误。")
            # 实现更健壮的清理机制
            try:
                # 清理已创建的野生宝可梦
                if 'wild_pokemon_instance_id' in locals() and wild_pokemon_instance_id:
                    await self.pokemon_repo.delete_pokemon_instance(wild_pokemon_instance_id)
                
                # 清理已创建的战斗记录
                if 'battle_id' in locals() and battle_id:
                    await self.battle_repo.delete_battle(battle_id)
                    
                # 清理玩家的战斗状态
                if 'player' in locals() and player and player.battle_id:
                    player.battle_id = None
                    await self.player_repo.save_player(player)
            except Exception as cleanup_error:
                logger.error(f"清理战斗资源时发生错误: {cleanup_error}", exc_info=True)
                
            return messages, None, events

    async def get_player_active_battle(self, player_id: str) -> Optional[Battle]:
        """Gets the active battle for a player."""
        player = await self.player_repo.get_player(player_id)
        if player and player.battle_id:
            return await self.battle_repo.get_battle(player.battle_id)
        return None

    async def process_player_action(self, player_id: str, action: Dict[str, Any]) -> Tuple[List[str], Optional[str], List[Any]]:
        """Processes a player's action during a battle turn."""
        messages = []
        events = []  # 初始化事件列表用于收集战斗事件
        outcome = None # 'win', 'lose', 'ran', 'caught', 'draw', 'error'
        battle_ended = False

        try:
            player = await self.player_repo.get_player(player_id)
            if not player or not player.battle_id:
                messages.append("你当前不在战斗中。")
                return messages, None, events

            battle = await self.battle_repo.get_battle(player.battle_id)
            if not battle:
                # This should not happen if player.battle_id is set, but handle defensively
                logger.error(f"Battle ID {player.battle_id} not found for player {player_id}.")
                player.battle_id = None # Clear invalid battle_id
                await self.player_repo.save_player(player)
                messages.append("战斗状态异常，已退出。")
                return messages, None, events


            if battle.is_finished:
                 messages.append("战斗已经结束了。")
                 # Clear player's battle_id if battle is finished but still linked
                 player.battle_id = None
                 await self.player_repo.save_player(player)
                 return messages, battle.outcome, events # Return the actual outcome if battle was finished


            # Get active pokemon instances
            player_pokemon = await self.pokemon_repo.get_pokemon_instance_by_id(battle.player_active_pokemon_instance_id)
            wild_pokemon = await self.pokemon_repo.get_pokemon_instance_by_id(battle.wild_pokemon_instance_id)

            if not player_pokemon or not wild_pokemon:
                 logger.error(f"Active pokemon not found for battle {battle.battle_id}. Player active: {battle.player_active_pokemon_instance_id}, Wild: {battle.wild_pokemon_instance_id}")
                 messages.append("战斗中的宝可梦数据异常，战斗已结束。")
                 await self.end_battle(battle.battle_id, 'error')
                 return messages, 'error', events

            # Ensure race data is loaded for active pokemon
            if not player_pokemon.race:
                 player_pokemon.race = self.metadata_repo.get_race_by_id(player_pokemon.race_id)
                 if player_pokemon.race:
                      calculate_stats(player_pokemon, player_pokemon.race, self.metadata_repo)
                      if player_pokemon.current_hp is None and player_pokemon.max_hp is not None:
                           player_pokemon.current_hp = player_pokemon.max_hp
                 else:
                      logger.error(f"Could not load race data for player pokemon {player_pokemon.nickname} (ID: {player_pokemon.race_id}).")
                      messages.append(f"无法加载 {player_pokemon.nickname} 的种族数据。")
                      await self.end_battle(battle.battle_id, 'error')
                      return messages, 'error', events


            if not wild_pokemon.race:
                 wild_pokemon.race = self.metadata_repo.get_race_by_id(wild_pokemon.race_id)
                 if wild_pokemon.race:
                      calculate_stats(wild_pokemon, wild_pokemon.race, self.metadata_repo)
                      if wild_pokemon.current_hp is None and wild_pokemon.max_hp is not None:
                           wild_pokemon.current_hp = wild_pokemon.max_hp
                 else:
                      logger.error(f"Could not load race data for wild pokemon {wild_pokemon.nickname} (ID: {wild_pokemon.race_id}).")
                      messages.append(f"无法加载野生 {wild_pokemon.nickname} 的种族数据。")
                      await self.end_battle(battle.battle_id, 'error')
                      return messages, 'error', events


            # Validate player action
            action_type = action.get('type')
            if action_type not in ['skill', 'switch', 'item', 'run', 'catch']:
                 raise InvalidBattleActionException(f"Invalid action type: {action_type}")

            # Check if player's active pokemon is fainted, only switch/item/run allowed
            if player_pokemon.is_fainted and action_type not in ['switch', 'item', 'run']:
                 raise PokemonFaintedException(f"{player_pokemon.nickname} 已经濒死，无法执行 {action_type} 行动。请切换宝可梦。")

            # Process the player action based on type
            if action_type == 'skill':
                skill_id = action.get('skill_id')
                target_instance_id = action.get('target_instance_id') # Target of the skill
                # Call the specific skill action processing method
                action_events, battle_ended, outcome = await self._process_skill_action(battle, player_pokemon, wild_pokemon, action)
                events.extend(action_events) # Collect events from skill action
            elif action_type == 'switch':
                switch_to_id = action.get('pokemon_id')
                if not switch_to_id:
                    messages.append("请选择要切换的宝可梦。")
                    return messages, None, events
                
                # 获取玩家的完整宝可梦队伍
                player_party = await self.pokemon_repo.get_player_pokemon(player_id)
                if not player_party:
                    messages.append("你没有可用的宝可梦。")
                    return messages, None, events
                
                # 检查选择的宝可梦是否在队伍中
                switch_to_pokemon = None
                for pokemon in player_party:
                    if pokemon.instance_id == switch_to_id:
                        switch_to_pokemon = pokemon
                        break
                
                if not switch_to_pokemon:
                    messages.append("该宝可梦不在你的队伍中。")
                    return messages, None, events
                
                if switch_to_pokemon.is_fainted:
                    messages.append(f"{switch_to_pokemon.nickname} 已经濒死，无法参战！")
                    return messages, None, events
                
                if switch_to_pokemon.instance_id == player_pokemon.instance_id:
                    messages.append(f"{player_pokemon.nickname} 已经在场上了！")
                    return messages, None, events
                
                # 执行切换
                old_pokemon_name = player_pokemon.nickname
                battle.player_active_pokemon_instance_id = switch_to_pokemon.instance_id
                await self.battle_repo.save_battle(battle)
                
                messages.append(f"你收回了 {old_pokemon_name}！")
                messages.append(f"你派出了 {switch_to_pokemon.nickname}！")
                
                # 生成切换事件
                switch_event = PokemonSwitchEvent(
                    player_id=player_id,
                    old_pokemon_id=player_pokemon.instance_id,
                    old_pokemon_name=old_pokemon_name,
                    new_pokemon_id=switch_to_pokemon.instance_id,
                    new_pokemon_name=switch_to_pokemon.nickname,
                    message=f"你将 {old_pokemon_name} 换成了 {switch_to_pokemon.nickname}！"
                )
                events.append(switch_event)
                
                # 切换后，野生宝可梦会进行一次攻击
                # 更新player_pokemon为新的活跃宝可梦
                player_pokemon = switch_to_pokemon
            elif action_type == 'item':
                item_id = action.get('item_id')
                target_id = action.get('target_id')  # 可能是宝可梦ID或null
                
                if not item_id:
                    messages.append("请选择要使用的道具。")
                    return messages, None, events
                
                # 获取道具信息
                item = await self.item_service.get_item(item_id)
                if not item:
                    messages.append("无效的道具ID。")
                    return messages, None, events
                
                # 检查玩家是否拥有该道具
                has_item = await self.item_service.check_player_has_item(player_id, item_id)
                if not has_item:
                    messages.append(f"你没有 {item.name}。")
                    return messages, None, events
                
                # 根据道具类型处理不同的效果
                if item.effect_type == ItemEffectType.CAPTURE.value:
                    # 处理捕捉道具
                    if battle.is_trainer_battle:
                        messages.append("你不能在训练师战斗中使用精灵球！")
                        return messages, None, events
                    
                    # 计算捕获成功率
                    catch_rate = self.battle_logic.calculate_catch_rate(
                        pokemon=wild_pokemon,
                        item=item,
                        battle=battle
                    )
                    
                    # 随机决定是否捕获成功
                    catch_success = random.random() < catch_rate
                    
                    # 减少道具数量
                    await self.item_service.use_player_item(player_id, item_id, 1)
                    
                    if catch_success:
                        # 捕获成功
                        messages.append(f"你使用了 {item.name}！")
                        messages.append(f"抓到了野生的 {wild_pokemon.nickname}！")
                        
                        # 将野生宝可梦转为玩家宝可梦
                        wild_pokemon.player_id = player_id
                        await self.pokemon_repo.save_pokemon_instance(wild_pokemon)
                        
                        # 结束战斗
                        battle_ended = True
                        outcome = "caught"
                    else:
                        # 捕获失败
                        shake_count = min(3, int(catch_rate * 4))
                        messages.append(f"你使用了 {item.name}！")
                        if shake_count == 0:
                            messages.append("精灵球立刻弹开了！")
                        else:
                            messages.append(f"精灵球摇晃了 {shake_count} 次，但 {wild_pokemon.nickname} 挣脱了出来！")
                
                elif item.effect_type in [ItemEffectType.HEAL_HP.value, ItemEffectType.HEAL_PP.value, ItemEffectType.CURE_STATUS.value]:
                    # 处理治疗类道具
                    target_pokemon = None
                    
                    # 如果有指定目标，尝试获取目标宝可梦
                    if target_id:
                        for pokemon in player_party:
                            if pokemon.instance_id == target_id:
                                target_pokemon = pokemon
                                break
                    else:
                        # 默认使用在当前的活跃宝可梦上
                        target_pokemon = player_pokemon
                    
                    if not target_pokemon:
                        messages.append("无效的目标宝可梦。")
                        return messages, None, events
                    
                    # 使用道具
                    item_use_events = await self.item_service.use_item(
                        item=item,
                        target_pokemon=target_pokemon,
                        player_id=player_id
                    )
                    
                    # 收集事件和消息
                    events.extend(item_use_events)
                    for event in item_use_events:
                        messages.append(event.message)
                
                else:
                    messages.append(f"无法在战斗中使用 {item.name}。")
                    return messages, None, events
            elif action_type == 'run':
                # 训练师战斗不能逃跑
                if battle.is_trainer_battle:
                    messages.append("你不能从训练师战斗中逃跑！")
                    return messages, None, events
                
                # 计算逃跑成功率
                escape_rate = self.battle_logic.calculate_escape_rate(
                    player_pokemon=player_pokemon,
                    wild_pokemon=wild_pokemon,
                    battle=battle
                )
                
                # 如果这是第n次尝试逃跑，增加成功率
                if "escape_attempts" not in battle.battle_state:
                    battle.battle_state["escape_attempts"] = 0
                battle.battle_state["escape_attempts"] += 1
                escape_rate += battle.battle_state["escape_attempts"] * 0.1  # 每次尝试增加10%
                
                # 随机决定是否逃跑成功
                escape_success = random.random() < escape_rate
                
                if escape_success:
                    # 逃跑成功
                    messages.append("成功逃离了战斗！")
                    battle_ended = True
                    outcome = "ran"
                else:
                    # 逃跑失败
                    messages.append("逃跑失败！")
                    
                    # 逃跑失败后，野生宝可梦会进行一次攻击
                    battle.current_turn_player_id = "wild"
                    await self.battle_repo.update_battle(battle)
            elif action_type == 'catch':
                # 实现捕获逻辑
                action_events, battle_ended, outcome = await self._process_catch_action(battle, player_pokemon, wild_pokemon, action)
                events.extend(action_events)
                for event in action_events:
                    messages.append(event.message)

            # 处理玩家使用技能的动作
            if action_type == "use_skill":
                skill_id = action.get("skill_id")
                if not skill_id:
                    messages.append("请选择要使用的技能。")
                    return messages, None, events
                
                # 获取技能数据
                skill_data = None
                for skill in player_pokemon.skills:
                    if skill.skill_id == skill_id:
                        skill_data = skill
                        break
                
                if not skill_data:
                    messages.append(f"{player_pokemon.nickname} 没有学会这个技能。")
                    return messages, None, events
                
                # 检查PP值
                if skill_data.current_pp <= 0:
                    messages.append(f"{skill_data.name} 的PP不足，无法使用！")
                    return messages, None, events
                
                # 减少PP值
                skill_data.current_pp -= 1
                
                # 使用战斗逻辑处理技能使用
                skill_use_events = await self.battle_logic.use_skill(
                    attacker=player_pokemon,
                    defender=wild_pokemon,
                    skill=skill_data,
                    battle=battle
                )
                
                # 收集事件和消息
                events.extend(skill_use_events)
                for event in skill_use_events:
                    messages.append(event.message)
                
                # 检查是否有宝可梦濒死
                if wild_pokemon.is_fainted:
                    # 野生宝可梦濒死，战斗结束
                    battle_ended = True
                    outcome = "win"
                    
                    # 计算经验值并生成经验获取事件
                    exp_gain = self.battle_logic.calculate_exp_gain(
                        winner=player_pokemon,
                        loser=wild_pokemon,
                        battle_type="wild"
                    )
                    
                    exp_event = ExpGainEvent(
                        pokemon_instance_id=player_pokemon.instance_id,
                        pokemon_name=player_pokemon.nickname,
                        exp_gained=exp_gain,
                        message=f"{player_pokemon.nickname} 获得了 {exp_gain} 点经验值！"
                    )
                    events.append(exp_event)
                    messages.append(exp_event.message)
                    
                    # 应用经验值并检查升级
                    level_up_events = await self.battle_logic.apply_exp_gain(player_pokemon, exp_gain)
                    events.extend(level_up_events)
                    for event in level_up_events:
                        messages.append(event.message)
                    
                    # 检查进化条件
                    if player_pokemon.can_evolve():
                        evolution_event = EvolutionAvailableEvent(
                            pokemon_instance_id=player_pokemon.instance_id,
                            pokemon_name=player_pokemon.nickname,
                            current_race_id=player_pokemon.race_id,
                            evolved_race_id=player_pokemon.get_evolution_target(),
                            message=f"{player_pokemon.nickname} 可以进化了！"
                        )
                        events.append(evolution_event)
                        messages.append(evolution_event.message)

            # 处理战斗回合结束逻辑
            if not battle_ended:
                # 如果战斗没有结束，让野生宝可梦行动
                wild_move_events = await self.battle_logic.process_wild_pokemon_turn(
                    player_pokemon=player_pokemon,
                    wild_pokemon=wild_pokemon,
                    battle=battle
                )
                
                # 收集野生宝可梦行动的事件和消息
                events.extend(wild_move_events)
                for event in wild_move_events:
                    messages.append(event.message)
                
                # 检查玩家宝可梦是否濒死
                if player_pokemon.is_fainted:
                    # 检查玩家是否还有其他可用宝可梦
                    has_available_pokemon = False
                    for pokemon in player_party:
                        if pokemon.instance_id != player_pokemon.instance_id and not pokemon.is_fainted:
                            has_available_pokemon = True
                            break
                    
                    if has_available_pokemon:
                        # 玩家还有其他可用宝可梦，提示切换
                        messages.append(f"{player_pokemon.nickname} 濒死了！请选择下一只宝可梦。")
                        
                        # 生成宝可梦濒死事件
                        faint_event = PokemonFaintEvent(
                            pokemon_instance_id=player_pokemon.instance_id,
                            pokemon_name=player_pokemon.nickname,
                            message=f"{player_pokemon.nickname} 濒死了！"
                        )
                        events.append(faint_event)
                        
                        # 设置战斗状态为需要切换宝可梦
                        battle.battle_state["need_switch"] = True
                        await self.battle_repo.save_battle(battle)
                    else:
                        # 玩家没有其他可用宝可梦，战斗结束，失败
                        messages.append("你的所有宝可梦都濒死了！")
                        battle_ended = True
                        outcome = "lose"
                
                # 如果野生宝可梦濒死，玩家胜利
                if wild_pokemon.is_fainted:
                    messages.append(f"野生的 {wild_pokemon.nickname} 濒死了！")
                    battle_ended = True
                    outcome = "win"
                    
                    # 计算经验值并生成经验获取事件
                    exp_gain = self.battle_logic.calculate_exp_gain(
                        winner=player_pokemon,
                        loser=wild_pokemon,
                        battle_type="wild"
                    )
                    
                    exp_event = ExpGainEvent(
                        pokemon_instance_id=player_pokemon.instance_id,
                        pokemon_name=player_pokemon.nickname,
                        exp_gained=exp_gain,
                        message=f"{player_pokemon.nickname} 获得了 {exp_gain} 点经验值！"
                    )
                    events.append(exp_event)
                    messages.append(exp_event.message)
                    
                    # 应用经验值并检查升级
                    level_up_events = await self.battle_logic.apply_exp_gain(player_pokemon, exp_gain)
                    events.extend(level_up_events)
                    for event in level_up_events:
                        messages.append(event.message)
                
                # 处理回合结束时的状态效果
                if not battle_ended:
                    # 处理玩家宝可梦的状态效果
                    player_status_events = await self.battle_logic.status_effect_handler.process_status_end_of_turn(
                        player_pokemon, battle
                    )
                    events.extend(player_status_events)
                    for event in player_status_events:
                        messages.append(event.message)
                    
                    # 处理野生宝可梦的状态效果
                    wild_status_events = await self.battle_logic.status_effect_handler.process_status_end_of_turn(
                        wild_pokemon, battle
                    )
                    events.extend(wild_status_events)
                    for event in wild_status_events:
                        messages.append(event.message)
                    
                    # 增加回合数
                    battle.turn_number += 1
                    await self.battle_repo.save_battle(battle)

            # S53: Collect messages from BattleLogic events
            # Process the collected events and generate detailed messages
            generated_messages = self._format_battle_events_to_messages(events)
            messages.extend(generated_messages) # Add generated messages to the list

            # 如果战斗结束，更新战斗状态
            if battle_ended:
                await self.end_battle(battle.battle_id, outcome)
                
                # 战斗结束事件
                battle_end_event = BattleEndEvent(
                    battle_id=battle.battle_id,
                    outcome=outcome,
                    message=f"战斗结束！结果：{outcome}"
                )
                events.append(battle_end_event)
                
                # 如果是胜利，检查宝可梦是否可以进化
                if outcome == "win" and player_pokemon.can_evolve():
                    evolution_event = EvolutionAvailableEvent(
                        pokemon_instance_id=player_pokemon.instance_id,
                        pokemon_name=player_pokemon.nickname,
                        current_race_id=player_pokemon.race_id,
                        evolved_race_id=player_pokemon.get_evolution_target(),
                        message=f"{player_pokemon.nickname} 可以进化了！"
                    )
                    events.append(evolution_event)
                    messages.append(evolution_event.message)

            # 保存宝可梦状态
            await self.pokemon_repo.save_pokemon_instance(player_pokemon)
            if not battle_ended or outcome != "caught":  # 如果不是捕获成功，也保存野生宝可梦状态
                await self.pokemon_repo.save_pokemon_instance(wild_pokemon)

            # 记录战斗详细数据
            battle_record = {
                "battle_id": battle.battle_id,
                "player_id": player.player_id,
                "is_trainer_battle": battle.is_trainer_battle,
                "opponent_id": battle.trainer_id if battle.is_trainer_battle else battle.wild_pokemon_instance_id,
                "outcome": outcome,
                "duration": (battle.end_time - battle.start_time).total_seconds(),
                "location": battle.location,
                "timestamp": battle.end_time.isoformat()
            }
            
            # 保存战斗记录到数据库
            await self.battle_repo.save_battle_record(battle_record)
            
            # 更新玩家的战斗统计
            player.battle_history.append(battle_record)
            await self.player_repo.save_player(player)

            return messages, outcome if battle_ended else None, events

        except (InvalidBattleActionException, PokemonFaintedException, InvalidTargetException, SkillNotFoundException) as e:
            messages.append(str(e))
            # If an error occurs, the battle state is not changed (except potentially clearing battle_id on critical errors)
            # The battle continues, and the player can try another action.
            return messages, None, events # Battle did not end due to invalid action

        except Exception as e:
            logger.error(f"An unexpected error occurred while processing battle action for player {player_id}: {e}", exc_info=True)
            messages.append("处理战斗行动时发生未知错误。")
            # On unexpected errors, end the battle with an error outcome
            if battle and battle.battle_id:
                 await self.end_battle(battle.battle_id, 'error')
            return messages, 'error', events

    async def _process_skill_action(self, battle: Battle, player_pokemon: Pokemon, wild_pokemon: Pokemon, action: Dict[str, Any]) -> Tuple[List[BattleEvent], bool, Optional[str]]:
        """Handles the 'skill' action."""
        events: List[BattleEvent] = []
        battle_ended = False
        outcome = None

        skill_id = action.get('skill_id')
        target_instance_id = action.get('target_instance_id')

        if skill_id is None or target_instance_id is None:
             raise InvalidBattleActionException("Skill action requires 'skill_id' and 'target_instance_id'.")

        # Get the skill instance from the player's pokemon
        player_pokemon_skills = await self.pokemon_repo.get_pokemon_skills(player_pokemon.instance_id)
        pokemon_skill = next((ps for ps in player_pokemon_skills if ps.skill_id == skill_id), None)

        if not pokemon_skill:
             raise SkillNotFoundException(f"{player_pokemon.nickname} 没有学会 ID 为 {skill_id} 的技能。")

        # Get the skill metadata
        skill = self.metadata_repo.get_skill(skill_id)
        if not skill:
             # This should not happen if pokemon_skill exists, but handle defensively
             logger.error(f"Skill metadata not found for skill ID: {skill_id}")
             raise SkillNotFoundException(f"未找到技能 ID {skill_id} 的元数据。")

        # Check if skill has enough PP
        if pokemon_skill.current_pp <= 0:
            # 如果没有PP的技能，尝试使用挣扎技能
            struggle_skill = self.metadata_repo.get_struggle_skill()
            if not struggle_skill:
                # 如果找不到挣扎技能，简单地跳过回合
                events.append(BattleMessageEvent(message=f"{player_pokemon.nickname} 无法行动！"))
                
                # 转为野生宝可梦的回合
                battle.current_turn_player_id = "wild"
                await self.battle_repo.update_battle(battle)
                
                return events, False, None
            else:
                events.append(BattleMessageEvent(message=f"{player_pokemon.nickname} 的 {skill.name} 没有PP了！"))
                events.append(BattleMessageEvent(message=f"{player_pokemon.nickname} 使用了挣扎！"))
                
                # 挣扎会对自己造成反伤
                struggle_damage = max(1, int(player_pokemon.max_hp * 0.25))
                player_pokemon.current_hp = max(0, player_pokemon.current_hp - struggle_damage)
                events.append(DamageDealtEvent(
                    attacker_instance_id=player_pokemon.instance_id,
                    attacker_name=player_pokemon.nickname,
                    defender_instance_id=player_pokemon.instance_id,
                    defender_name=player_pokemon.nickname,
                    skill_id=struggle_skill.skill_id,
                    skill_name=struggle_skill.name,
                    damage=struggle_damage,
                    is_critical=False,
                    type_effectiveness=1.0,
                    message=f"{player_pokemon.nickname} 因挣扎受到了 {struggle_damage} 点伤害！"
                ))
                
                # 对敌人造成伤害
                struggle_damage_to_enemy = max(1, int(wild_pokemon.max_hp * 0.1))
                wild_pokemon.current_hp = max(0, wild_pokemon.current_hp - struggle_damage_to_enemy)
                events.append(DamageDealtEvent(
                    attacker_instance_id=player_pokemon.instance_id,
                    attacker_name=player_pokemon.nickname,
                    defender_instance_id=wild_pokemon.instance_id,
                    defender_name=wild_pokemon.nickname,
                    skill_id=struggle_skill.skill_id,
                    skill_name=struggle_skill.name,
                    damage=struggle_damage_to_enemy,
                    is_critical=False,
                    type_effectiveness=1.0,
                    message=f"对 {wild_pokemon.nickname} 造成了 {struggle_damage_to_enemy} 点伤害！"
                ))
                
                # 检查是否有宝可梦因此失去战斗能力
                if player_pokemon.is_fainted:
                    events.append(FaintEvent(
                        pokemon_instance_id=player_pokemon.instance_id,
                        pokemon_name=player_pokemon.nickname,
                        message=f"{player_pokemon.nickname} 失去了战斗能力！"
                    ))
                    
                if wild_pokemon.is_fainted:
                    events.append(FaintEvent(
                        pokemon_instance_id=wild_pokemon.instance_id,
                        pokemon_name=wild_pokemon.nickname,
                        message=f"野生的 {wild_pokemon.nickname} 失去了战斗能力！"
                    ))
                    return events, True, "win"
                
                return events, False, None

        # Determine the actual target pokemon object
        target_pokemon = None

        if skill.target_type == "enemy":
            # 针对敌人的技能
            if target_instance_id == wild_pokemon.instance_id or target_instance_id is None:
                target_pokemon = wild_pokemon
            else:
                raise InvalidTargetException(f"技能 {skill.name} 必须指向敌方宝可梦。")
        elif skill.target_type == "self":
            # 针对自身的技能
            target_pokemon = player_pokemon
            # 忽略传入的target_instance_id
        elif skill.target_type == "ally":
            # 针对友方的技能（在多对多战斗中使用）
            if target_instance_id:
                # 检查目标是否是队伍中的宝可梦
                player_party = await self.pokemon_repo.get_player_pokemons(battle.player_id)
                for party_pokemon in player_party:
                    if party_pokemon.instance_id == target_instance_id:
                        target_pokemon = party_pokemon
                        break
            else:
                # 如果没有指定目标，默认为自己
                target_pokemon = player_pokemon
        elif skill.target_type == "all_enemies":
            # 针对所有敌人的技能（在多对多战斗中使用）
            # 在野外战斗中，就是单个野生宝可梦
            target_pokemon = wild_pokemon
        elif skill.target_type == "all_allies":
            # 针对所有友方的技能（在多对多战斗中使用）
            # 在单人战斗中，就是自己
            target_pokemon = player_pokemon
        elif skill.target_type == "all":
            # 针对场上所有宝可梦的技能
            # 这种情况需要特殊处理，可能需要传递多个目标
            # 为简化，我们先将目标设为对手
            target_pokemon = wild_pokemon

        if not target_pokemon:
            raise InvalidTargetException(f"技能 {skill.name} 的目标无效。")

        # Consume 1 PP from the skill
        pokemon_skill.current_pp -= 1

        # 更新宝可梦的技能列表中对应技能的PP
        for i, skill_in_list in enumerate(player_pokemon.skills):
            if skill_in_list.skill_id == pokemon_skill.skill_id:
                player_pokemon.skills[i] = pokemon_skill
                break

        # 将PP变化保存到数据库
        await self.pokemon_repo.save_pokemon_instance(player_pokemon)

        events.append(BattleMessageEvent(message=f"{player_pokemon.nickname} 使用了 {skill.name}！"))

        # S49: Call BattleLogic to execute the skill action
        # The BattleLogic will handle damage calculation, status effects, etc.
        # It should return whether the battle ended and the outcome, and publish events for messages.
        # TODO: Implement BattleLogic.execute_skill method (S97 refinement)
        # This method should take the battle state, attacker, defender, skill, etc.
        # It should modify the pokemon states in place and return a list of events.
        # For now, we'll simulate calling it and getting some events.

        # Call BattleLogic to execute the skill and get events
        skill_execution_result = await self.battle_logic.execute_skill(
            battle=battle,
            attacker=player_pokemon,
            defender=target_pokemon,
            skill=skill
        )

        # 获取技能执行产生的事件和效果
        skill_execution_events = skill_execution_result.get("events", [])
        events.extend(skill_execution_events)

        # 检查是否有状态效果被应用
        status_effects = skill_execution_result.get("status_effects", [])
        for status_effect in status_effects:
            target = status_effect["target"]
            effect = status_effect["effect"]
            
            # 应用状态效果
            await self.battle_logic.status_effect_handler.apply_status_effect(target, effect)
            
            # 添加状态效果事件
            events.append(StatusEffectAppliedEvent(
                pokemon_instance_id=target.instance_id,
                pokemon_name=target.nickname,
                status_effect_id=effect.status_effect_id,
                status_effect_name=effect.name,
                duration=effect.duration,
                message=f"{target.nickname} {effect.application_message}！"
            ))

            # 检查战斗结束条件
            battle_ended = False
            outcome = None

            # 检查野生宝可梦是否失去战斗能力
            if wild_pokemon.current_hp <= 0:
                wild_pokemon.current_hp = 0
                wild_pokemon.is_fainted = True
                if not any(e.event_type == "faint" and e.pokemon_instance_id == wild_pokemon.instance_id for e in events):
                    events.append(FaintEvent(
                        pokemon_instance_id=wild_pokemon.instance_id,
                        pokemon_name=wild_pokemon.nickname,
                        message=f"野生的 {wild_pokemon.nickname} 失去了战斗能力！"
                    ))
                battle_ended = True
                outcome = "win"
                
                # 计算获得的经验值
                exp_gained = self.battle_logic.calculate_exp_gain(player_pokemon, wild_pokemon)
                
                # 添加经验值获取事件
                events.append(ExpGainEvent(
                    pokemon_instance_id=player_pokemon.instance_id,
                    pokemon_name=player_pokemon.nickname,
                    exp_gained=exp_gained,
                    message=f"{player_pokemon.nickname} 获得了 {exp_gained} 点经验值！"
                ))
                
                # 更新宝可梦经验值并检查升级
                player_pokemon.exp += exp_gained
                level_up_result = await self.battle_logic.check_level_up(player_pokemon)
                
                if level_up_result.get("leveled_up", False):
                    new_level = level_up_result.get("new_level")
                    events.append(BattleMessageEvent(
                        message=f"{player_pokemon.nickname} 升级到了 {new_level} 级！"
                    ))
                    
                    # 检查是否学习了新技能
                    new_skills = level_up_result.get("new_skills", [])
                    for new_skill in new_skills:
                        if len(player_pokemon.skills) < 4:
                            # 直接学习新技能
                            events.append(BattleMessageEvent(
                                message=f"{player_pokemon.nickname} 学会了 {new_skill.name}！"
                            ))
                        else:
                            # 需要替换技能
                            events.append(SkillReplacementRequiredEvent(
                                pokemon_instance_id=player_pokemon.instance_id,
                                pokemon_name=player_pokemon.nickname,
                                new_skill_id=new_skill.skill_id,
                                new_skill_name=new_skill.name,
                                current_skills=[s.to_dict() for s in player_pokemon.skills],
                                message=f"{player_pokemon.nickname} 想要学习 {new_skill.name}，但已经学会了4个技能！请选择要替换的技能。"
                            ))
                    
                    # 检查是否进化
                    evolution_result = await self.battle_logic.check_evolution(player_pokemon)
                    if evolution_result.get("can_evolve", False):
                        evolution_to = evolution_result.get("evolution_to")
                        events.append(BattleMessageEvent(
                            message=f"恭喜！你的 {player_pokemon.nickname} 可以进化成 {evolution_to.name}！"
                        ))
                
                # 保存宝可梦状态
                await self.pokemon_repo.save_pokemon_instance(player_pokemon)

            # 检查玩家宝可梦是否失去战斗能力
            elif player_pokemon.current_hp <= 0:
                player_pokemon.current_hp = 0
                player_pokemon.is_fainted = True
                if not any(e.event_type == "faint" and e.pokemon_instance_id == player_pokemon.instance_id for e in events):
                    events.append(FaintEvent(
                        pokemon_instance_id=player_pokemon.instance_id,
                        pokemon_name=player_pokemon.nickname,
                        message=f"{player_pokemon.nickname} 失去了战斗能力！"
                    ))
                
                # 检查玩家是否有其他可用宝可梦
                player_party = await self.pokemon_repo.get_player_pokemons(battle.player_id)
                has_usable_pokemon = any(p for p in player_party if p.in_party and not p.is_fainted and p.instance_id != player_pokemon.instance_id)
                
                if not has_usable_pokemon:
                    battle_ended = True
                    outcome = "lose"
                    events.append(BattleMessageEvent(message="你没有可用的宝可梦了！"))
                else:
                    # 提示玩家需要更换宝可梦
                    events.append(PokemonSwitchRequiredEvent(
                        player_id=battle.player_id,
                        fainted_pokemon_id=player_pokemon.instance_id,
                        fainted_pokemon_name=player_pokemon.nickname,
                        message=f"{player_pokemon.nickname} 失去了战斗能力！请选择下一个出战的宝可梦。"
                    ))
        return events, battle_ended, outcome


    async def _process_switch_action(self, battle: Battle, player_pokemon: Pokemon, wild_pokemon: Pokemon, action: Dict[str, Any]) -> Tuple[List[BattleEvent], bool, Optional[str]]:
        """Handles the 'switch' action."""
        events: List[BattleEvent] = []
        battle_ended = False
        outcome = None

        target_pokemon_instance_id = action.get('target_pokemon_instance_id')

        if target_pokemon_instance_id is None:
             raise InvalidBattleActionException("Switch action requires 'target_pokemon_instance_id'.")

        if target_pokemon_instance_id == player_pokemon.instance_id:
             raise InvalidBattleActionException("你已经派出了这只宝可梦。")

        # Get the target pokemon from the player's party
        player_party = await self.pokemon_repo.get_player_pokemons(battle.player_id)
        target_pokemon = next((p for p in player_party if p.instance_id == target_pokemon_instance_id), None)

        if not target_pokemon:
             raise PokemonNotFoundException(f"队伍中没有找到 ID 为 {target_pokemon_instance_id} 的宝可梦。")

        if target_pokemon.is_fainted:
             raise PokemonFaintedException(f"{target_pokemon.nickname} 已经濒死，无法替换上场。")

        # TODO: Check for trapping abilities/effects that prevent switching (S54 refinement)

        # Perform the switch
        old_active_pokemon_nickname = player_pokemon.nickname
        battle.player_active_pokemon_instance_id = target_pokemon_instance_id
        # TODO: Reset stat stages, volatile status effects on switch out (S55 refinement)
        # This logic should probably be in BattleLogic or a dedicated PokemonBattleState class

        events.append(SwitchOutEvent(pokemon=player_pokemon, message=f"你收回了 {old_active_pokemon_nickname}！"))
        events.append(SwitchInEvent(pokemon=target_pokemon, message=f"你派出了 {target_pokemon.nickname}！"))

        # TODO: Trigger switch-in abilities/effects (S105 refinement)
        # This should also generate events.

        # 触发切换入场特性效果
        if target_pokemon.ability and target_pokemon.ability.triggers_on_switch_in:
            ability_result = await self.battle_logic.trigger_switch_in_ability(
                battle, target_pokemon, wild_pokemon
            )
            
            # 添加特性触发事件
            if ability_result.get("triggered", False):
                events.append(AbilityTriggeredEvent(
                    pokemon_instance_id=target_pokemon.instance_id,
                    pokemon_name=target_pokemon.nickname,
                    ability_id=target_pokemon.ability.ability_id,
                    ability_name=target_pokemon.ability.name,
                    message=ability_result.get("message", f"{target_pokemon.nickname}的{target_pokemon.ability.name}特性发动了！")
                ))
                
                # 添加特性产生的额外事件
                ability_events = ability_result.get("events", [])
                events.extend(ability_events)

        return events, battle_ended, outcome

    async def _process_run_action(self, battle: Battle, player_pokemon: Pokemon, wild_pokemon: Pokemon, action: Dict[str, Any]) -> Tuple[List[BattleEvent], bool, Optional[str]]:
        """处理玩家尝试逃跑的行为。"""
        events = []
        
        # 在野生宝可梦战斗中，逃跑成功率基于双方速度
        # 计算逃跑几率 (使用核心逻辑层的公式)
        escape_chance = self.battle_logic.calculate_escape_chance(player_pokemon, wild_pokemon)
        escape_successful = random.random() < escape_chance
        
        if escape_successful:
            message = f"{player_pokemon.nickname} 成功逃离了战斗！"
            events.append(BattleMessageEvent(message=message))
            
            # 更新战斗状态为结束
            battle.is_active = False
            battle.outcome = "escape"
            await self.battle_repo.update_battle(battle)
            
            return events, True, "escape"
        else:
            message = f"{player_pokemon.nickname} 没能逃脱！"
            events.append(BattleMessageEvent(message=message))
            
            # 逃跑失败后，野生宝可梦会进行一次攻击
            battle.current_turn_player_id = "wild"
            await self.battle_repo.update_battle(battle)
            
            return events, False, None

    async def _process_catch_action(self, battle: Battle, player_pokemon: Pokemon, wild_pokemon: Pokemon, action: Dict[str, Any]) -> Tuple[List[BattleEvent], bool, Optional[str]]:
        """处理玩家的捕获行动。"""
        events: List[BattleEvent] = []
        battle_ended = False
        outcome = None
        
        # 获取使用的精灵球ID
        ball_item_id = action.get('ball_item_id')
        if not ball_item_id:
            raise InvalidBattleActionException("捕获动作需要指定使用的精灵球。")
        
        # 检查玩家是否拥有该精灵球
        player_id = battle.player_id
        has_item = await self.item_service.check_player_has_item(player_id, ball_item_id)
        if not has_item:
            raise ItemNotFoundException("你没有这个精灵球。")
        
        # 获取精灵球信息
        ball_item = await self.item_service.get_item(ball_item_id)
        if not ball_item or ball_item.effect_type != ItemEffectType.CAPTURE.value:
            raise InvalidItemException("这个物品不是用于捕获的精灵球。")
        
        # 从玩家背包中移除一个精灵球
        await self.item_service.remove_item_from_player(player_id, ball_item_id, 1)
        
        # 创建使用精灵球的事件
        ball_use_event = ItemUseEvent(
            player_id=player_id,
            item_id=ball_item_id,
            item_name=ball_item.name,
            target_id=wild_pokemon.instance_id,
            target_name=wild_pokemon.nickname,
            message=f"你对野生的 {wild_pokemon.nickname} 使用了 {ball_item.name}！"
        )
        events.append(ball_use_event)
        
        # 计算捕获成功率
        catch_rate = self.battle_logic.calculate_catch_rate(
            pokemon=wild_pokemon,
            ball_item=ball_item,
            battle=battle
        )
        
        # 随机决定是否捕获成功
        catch_success = random.random() < catch_rate
        
        if catch_success:
            # 捕获成功
            caught_event = PokemonCaughtEvent(
                player_id=player_id,
                pokemon_instance_id=wild_pokemon.instance_id,
                pokemon_name=wild_pokemon.nickname,
                ball_used=ball_item.name,
                message=f"恭喜！你成功捕获了野生的 {wild_pokemon.nickname}！"
            )
            events.append(caught_event)
            
            # 将野生宝可梦添加到玩家的队伍或存储到电脑中
            wild_pokemon.player_id = player_id
            wild_pokemon.is_wild = False
            
            player_party = await self.pokemon_repo.get_player_pokemons(player_id)
            if len(player_party) < 6:
                # 如果队伍未满，添加到队伍
                wild_pokemon.in_party = True
            else:
                # 队伍已满，存储到电脑中
                wild_pokemon.in_party = False
                storage_event = PokemonStoredEvent(
                    player_id=player_id,
                    pokemon_instance_id=wild_pokemon.instance_id,
                    pokemon_name=wild_pokemon.nickname,
                    message=f"{wild_pokemon.nickname} 已存入电脑。"
                )
                events.append(storage_event)
            
            # 保存捕获的宝可梦
            await self.pokemon_repo.save_pokemon_instance(wild_pokemon)
            
            battle_ended = True
            outcome = "caught"
        else:
            # 捕获失败
            shake_count = self.battle_logic.calculate_shake_count(catch_rate)
            
            shake_message = "精灵球晃动了 "
            if shake_count == 0:
                shake_message += "0 次，宝可梦立刻挣脱了出来！"
            elif shake_count == 1:
                shake_message += "1 次，然后宝可梦挣脱了出来！"
            elif shake_count == 2:
                shake_message += "2 次，但宝可梦还是挣脱了出来！"
            elif shake_count == 3:
                shake_message += "3 次，差一点就成功了，但宝可梦最终还是挣脱了出来！"
            
            fail_event = CaptureFailEvent(
                player_id=player_id,
                pokemon_instance_id=wild_pokemon.instance_id,
                pokemon_name=wild_pokemon.nickname,
                shake_count=shake_count,
                message=shake_message
            )
            events.append(fail_event)
            
            # 捕获失败，战斗继续
            battle_ended = False
            outcome = None
        
        return events, battle_ended, outcome

    async def _process_item_action(self, battle: Battle, player_pokemon: Pokemon, wild_pokemon: Pokemon, action: Dict[str, Any]) -> Tuple[List[BattleEvent], bool, Optional[str]]:
        """处理玩家在战斗中使用道具的行为。"""
        events = []
        
        # 获取道具和目标信息
        item_id = action.get("item_id")
        if not item_id:
            raise InvalidBattleActionException("必须指定道具ID。")
        
        target_type = action.get("target_type", "player_pokemon")
        target_id = action.get("target_id")
        
        if not target_id:
            if target_type == "player_pokemon":
                target_id = player_pokemon.instance_id
            elif target_type == "wild_pokemon":
                target_id = wild_pokemon.instance_id
            else:
                raise InvalidBattleActionException(f"无效的目标类型: {target_type}")
        
        # 获取道具信息
        item = await self.item_service.get_item(item_id)
        if not item:
            raise ItemNotFoundException(f"道具 {item_id} 不存在。")
        
        # 检查玩家是否有该道具并消耗一个
        has_item = await self.item_service.check_player_has_item(battle.player_id, item_id)
        if not has_item:
            raise InvalidBattleActionException("你没有指定的道具。")
        
        await self.item_service.use_player_item(battle.player_id, item_id)
        
        # 根据目标类型获取目标宝可梦
        target_pokemon = None
        if target_type == "player_pokemon":
            if target_id == player_pokemon.instance_id:
                target_pokemon = player_pokemon
            else:
                # 获取玩家的其他宝可梦
                player_pokemons = await self.pokemon_repo.get_player_pokemons(battle.player_id)
                for pokemon in player_pokemons:
                    if pokemon.instance_id == target_id:
                        target_pokemon = pokemon
                        break
        elif target_type == "wild_pokemon":
            if target_id == wild_pokemon.instance_id:
                target_pokemon = wild_pokemon
        
        if not target_pokemon:
            raise InvalidTargetException(f"找不到ID为 {target_id} 的目标宝可梦。")
        
        # 根据道具类型应用效果
        item_effect_applied = False
        
        # 使用道具事件
        events.append(ItemUsedEvent(
            player_id=battle.player_id,
            item_id=item_id,
            item_name=item.name,
            target=target_type,
            target_id=target_id,
            message=f"{battle.player_name} 对 {target_pokemon.nickname} 使用了 {item.name}！"
        ))
        
        # 根据道具效果类型处理不同效果
        if item.effect_type == "heal_hp":
            # 计算恢复的HP (可能需要更复杂的公式)
            heal_amount = int(target_pokemon.max_hp * 0.5)  # 假设回复50%的HP
            old_hp = target_pokemon.current_hp
            target_pokemon.current_hp = min(target_pokemon.current_hp + heal_amount, target_pokemon.max_hp)
            actual_heal = target_pokemon.current_hp - old_hp
            
            events.append(HealEvent(
                target_instance_id=target_pokemon.instance_id,
                target_name=target_pokemon.nickname,
                amount_healed=actual_heal,
                current_hp=target_pokemon.current_hp,
                max_hp=target_pokemon.max_hp,
                source="item"
            ))
            
            # 更新宝可梦状态
            await self.pokemon_repo.update_pokemon(target_pokemon)
            item_effect_applied = True
            
        elif item.effect_type == "heal_pp":
            # 恢复所有技能的PP
            for skill in target_pokemon.skills:
                skill.current_pp = skill.max_pp
            
            events.append(BattleMessageEvent(
                message=f"{target_pokemon.nickname} 的所有技能PP都恢复了！"
            ))
            
            # 更新宝可梦状态
            await self.pokemon_repo.update_pokemon(target_pokemon)
            item_effect_applied = True
            
        elif item.effect_type == "cure_status":
            # 如果有状态异常，移除它
            if target_pokemon.status_condition:
                old_status = target_pokemon.status_condition
                target_pokemon.status_condition = None
                
                events.append(StatusEffectRemovedEvent(
                    pokemon=target_pokemon,
                    status_effect=old_status,
                    message=f"{target_pokemon.nickname} 的 {old_status.name} 状态被治愈了！"
                ))
                
                # 更新宝可梦状态
                await self.pokemon_repo.update_pokemon(target_pokemon)
                item_effect_applied = True
            else:
                events.append(BattleMessageEvent(
                    message=f"{target_pokemon.nickname} 没有状态异常，道具没有效果。"
                ))
        
        elif item.effect_type == "stat_boost_battle":
            # 临时提升能力值
            # 此处简化处理，实际应该根据道具的具体效果决定提升哪个能力值
            stat_boost_type = "attack"  # 假设提升攻击力
            
            # 如果宝可梦没有战斗中的临时状态，初始化它
            if not target_pokemon.volatile_status:
                target_pokemon.volatile_status = {}
            
            # 记录能力值提升
            if "stat_boosts" not in target_pokemon.volatile_status:
                target_pokemon.volatile_status["stat_boosts"] = {}
            
            current_boost = target_pokemon.volatile_status["stat_boosts"].get(stat_boost_type, 0)
            target_pokemon.volatile_status["stat_boosts"][stat_boost_type] = min(current_boost + 1, 6)  # 最多提升6级
            
            events.append(BattleMessageEvent(
                message=f"{target_pokemon.nickname} 的 {stat_boost_type} 提高了！"
            ))
            
            # 更新宝可梦状态
            await self.pokemon_repo.update_pokemon(target_pokemon)
            item_effect_applied = True
        
        # 如果道具效果应用成功，轮到对手的回合
        if item_effect_applied:
            battle.current_turn_player_id = "wild" if battle.current_turn_player_id == battle.player_id else battle.player_id
            await self.battle_repo.update_battle(battle)
        
        return events, False, None

    def _format_battle_events_to_messages(self, events: List[BattleEvent]) -> List[str]:
        """
        Formats a list of BattleEvent objects into a list of user-facing message strings.
        This method determines the level of detail based on the event type and its details.
        """
        messages: List[str] = []
        for event in events:
            # Use the message provided in the event if available
            if hasattr(event, 'message') and event.message:
                messages.append(event.message)
            else:
                # Fallback or more detailed formatting based on event type
                if isinstance(event, DamageDealtEvent):
                    msg = f"{event.attacker.nickname} 对 {event.defender.nickname} 造成了 {event.damage} 点伤害！"
                    if event.is_critical:
                        msg += " 这是击中要害！"
                    if event.is_effective:
                        msg += " 效果绝佳！"
                    if event.is_not_effective:
                        msg += " 效果不理想..."
                    if event.is_immune:
                        msg = f"{event.defender.nickname} 对 {event.skill.name} 没有反应！" # Immune overrides other messages
                    messages.append(msg)
                elif isinstance(event, StatusEffectAppliedEvent):
                    messages.append(f"{event.pokemon.nickname} {event.status_effect.name}了！")
                elif isinstance(event, StatusEffectRemovedEvent):
                     messages.append(f"{event.pokemon.nickname} 的 {event.status_effect.name} 消失了！")
                elif isinstance(event, StatStageChangeEvent):
                    change_word = "提升" if event.stages_changed > 0 else "下降"
                    messages.append(f"{event.pokemon.nickname} 的 {event.stat_type} {change_word}了 {abs(event.stages_changed)} 级！")
                elif isinstance(event, FaintEvent):
                    # Message is usually provided in the event, but fallback here
                    messages.append(f"{event.pokemon.nickname} 失去了战斗能力！")
                elif isinstance(event, SwitchOutEvent):
                     # Message is usually provided
                     messages.append(event.message)
                elif isinstance(event, SwitchInEvent):
                     # Message is usually provided
                     messages.append(event.message)
                elif isinstance(event, HealEvent):
                     messages.append(f"{event.pokemon.nickname} 恢复了 {event.amount} 点HP！")
                elif isinstance(event, AbilityTriggerEvent):
                     messages.append(f"{event.pokemon.nickname} 的特性【{event.ability.name}】发动了！")
                     if event.message: # Include specific ability message if provided
                          messages.append(event.message)
                elif isinstance(event, ItemTriggerEvent):
                     messages.append(f"{event.pokemon.nickname} 使用了 {event.item.name}！")
                     if event.message: # Include specific item message if provided
                          messages.append(event.message)
                elif isinstance(event, MoveMissedEvent):
                     messages.append(f"{event.pokemon.nickname} 的攻击没有命中！")
                elif isinstance(event, BattleMessageEvent):
                     # Generic message event, just append the message
                     messages.append(event.message)
                # TODO: Add formatting for other event types as they are implemented (S106 refinement)
                # Add more elif blocks here for other specific event types

        return messages


    async def end_battle(self, battle_id: int, outcome: str) -> None:
        """结束战斗并处理相关资源。"""
        # 获取战斗数据
        battle = await self.battle_repo.get_battle(battle_id)
        if not battle:
            logger.error(f"尝试结束不存在的战斗 ID: {battle_id}")
            return
        
        # 获取玩家数据
        player = await self.player_repo.get_player(battle.player_id)
        if player:
            # 清除玩家的战斗状态
            player.battle_id = None
            await self.player_repo.save_player(player)
        
        # 如果是野生宝可梦战斗，并且结果不是捕获
        if not battle.is_trainer_battle and outcome != "caught":
            # 删除野生宝可梦实例
            if battle.wild_pokemon_instance_id:
                await self.pokemon_repo.delete_pokemon_instance(battle.wild_pokemon_instance_id)
        
        # 更新战斗记录
        battle.is_active = False
        battle.outcome = outcome
        battle.end_time = datetime.now()
        await self.battle_repo.save_battle(battle)
        
        # 记录战斗统计
        if player:
            if outcome == "win":
                player.stats["battles_won"] = player.stats.get("battles_won", 0) + 1
            elif outcome == "lose":
                player.stats["battles_lost"] = player.stats.get("battles_lost", 0) + 1
            elif outcome == "caught":
                player.stats["pokemon_caught"] = player.stats.get("pokemon_caught", 0) + 1
            
            player.stats["total_battles"] = player.stats.get("total_battles", 0) + 1
            await self.player_repo.save_player(player)

    async def get_skill_data(self, skill_id: int) -> Skill:
        """
        获取技能数据的公共方法。
        
        Args:
            skill_id: 技能ID
            
        Returns:
            Skill: 技能数据对象
            
        Raises:
            SkillNotFoundException: 如果找不到指定ID的技能
        """
        try:
            return self.metadata_repo.get_skill(skill_id)
        except Exception as e:
            logger.error(f"获取技能数据失败: {e}")
            raise SkillNotFoundException(f"技能 ID {skill_id} 不存在")

    async def cleanup_battle(self, battle_id: str, capture_success: bool = False) -> None:
        """
        清理战斗结束后的状态。
        
        Args:
            battle_id: 要清理的战斗ID
            capture_success: 是否因为成功捕获而结束战斗
            
        Returns:
            None
        """
        try:
            # 获取战斗数据
            battle = await self.battle_repo.get_battle_by_id(battle_id)
            if not battle:
                logger.warning(f"尝试清理不存在的战斗: {battle_id}")
                return
            
            # 如果不是因为成功捕获而结束战斗，且有野生宝可梦，则需要清理野生宝可梦
            if not capture_success and battle.wild_pokemon_instance_id:
                await self.pokemon_repo.delete_pokemon(battle.wild_pokemon_instance_id)
                logger.debug(f"已删除未捕获的野生宝可梦: {battle.wild_pokemon_instance_id}")
            
            # 重置战斗中宝可梦的战斗状态
            player_pokemons = await self.pokemon_repo.get_player_pokemons(battle.player_id)
            for pokemon in player_pokemons:
                # 只重置参与过战斗的宝可梦
                if pokemon.instance_id == battle.player_active_pokemon_instance_id:
                    pokemon.in_battle = False
                    pokemon.volatile_status = {}  # 清除临时战斗状态
                    await self.pokemon_repo.update_pokemon(pokemon)
            
            # 设置战斗为非活跃状态（如果还没有设置）
            if battle.is_active:
                battle.is_active = False
                await self.battle_repo.update_battle(battle)
            
            logger.info(f"已完成战斗清理: {battle_id}")
        except Exception as e:
            logger.error(f"战斗清理过程中发生错误: {e}", exc_info=True)

    async def learn_new_skill(self, pokemon_instance_id: int, skill_id: int) -> List[str]:
        """让宝可梦学习新技能。"""
        messages = []
        
        # 获取宝可梦实例
        pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
        if not pokemon:
            messages.append("找不到指定的宝可梦。")
            return messages
        
        # 获取技能数据
        skill_metadata = await self.metadata_repo.get_skill(skill_id)
        if not skill_metadata:
            messages.append("找不到指定的技能。")
            return messages
        
        # 检查宝可梦是否已经学会了这个技能
        for existing_skill in pokemon.skills:
            if existing_skill.skill_id == skill_id:
                messages.append(f"{pokemon.nickname} 已经学会了 {skill_metadata.name}。")
                return messages
        
        # 检查宝可梦是否可以学习这个技能
        if not self.battle_logic.can_learn_skill(pokemon, skill_id):
            messages.append(f"{pokemon.nickname} 无法学习 {skill_metadata.name}。")
            return messages
        
        # 创建技能实例
        new_skill = PokemonSkill(
            skill_id=skill_id,
            name=skill_metadata.name,
            max_pp=skill_metadata.base_pp,
            current_pp=skill_metadata.base_pp
        )
        
        # 检查宝可梦的技能是否已满
        if len(pokemon.skills) >= 4:
            # 技能已满，需要替换
            messages.append(f"{pokemon.nickname} 已经学会了4个技能，需要替换一个技能才能学习 {skill_metadata.name}。")
            # 将新技能数据保存到临时状态，等待玩家选择要替换的技能
            pokemon.temp_data = {"pending_skill": new_skill.to_dict()}
            await self.pokemon_repo.save_pokemon_instance(pokemon)
        else:
            # 技能未满，直接学习
            pokemon.skills.append(new_skill)
            await self.pokemon_repo.save_pokemon_instance(pokemon)
            messages.append(f"{pokemon.nickname} 学会了 {skill_metadata.name}！")
        
        return messages

    async def replace_skill(self, pokemon_instance_id: int, old_skill_id: int) -> List[str]:
        """替换宝可梦的技能。"""
        messages = []
        
        # 获取宝可梦实例
        pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
        if not pokemon:
            messages.append("找不到指定的宝可梦。")
            return messages
        
        # 检查是否有待学习的技能
        if not pokemon.temp_data or "pending_skill" not in pokemon.temp_data:
            messages.append("该宝可梦没有待学习的技能。")
            return messages
        
        # 获取待学习的技能
        pending_skill_dict = pokemon.temp_data["pending_skill"]
        pending_skill = PokemonSkill(
            skill_id=pending_skill_dict["skill_id"],
            name=pending_skill_dict["name"],
            max_pp=pending_skill_dict["max_pp"],
            current_pp=pending_skill_dict["current_pp"]
        )
        
        # 查找要替换的技能
        skill_to_replace = None
        for i, skill in enumerate(pokemon.skills):
            if skill.skill_id == old_skill_id:
                skill_to_replace = skill
                skill_index = i
                break
        
        if not skill_to_replace:
            messages.append("找不到要替换的技能。")
            return messages
        
        # 替换技能
        pokemon.skills[skill_index] = pending_skill
        
        # 清除临时数据
        pokemon.temp_data.pop("pending_skill", None)
        
        # 保存宝可梦状态
        await self.pokemon_repo.save_pokemon_instance(pokemon)
        
        messages.append(f"{pokemon.nickname} 忘记了 {skill_to_replace.name}，学会了 {pending_skill.name}！")
        
        return messages

    async def evolve_pokemon(self, pokemon_instance_id: int) -> Tuple[List[str], Optional[BattleEvent]]:
        """处理宝可梦进化。"""
        messages = []
        event = None
        
        # 获取宝可梦实例
        pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
        if not pokemon:
            messages.append("找不到指定的宝可梦。")
            return messages, event
        
        # 检查是否可以进化
        if not pokemon.can_evolve():
            messages.append(f"{pokemon.nickname} 当前无法进化。")
            return messages, event
        
        # 获取进化目标
        evolution_target_id = pokemon.get_evolution_target()
        if not evolution_target_id:
            messages.append(f"找不到 {pokemon.nickname} 的进化形态。")
            return messages, event
        
        # 获取进化目标的元数据
        evolution_target = await self.metadata_repo.get_pokemon_race(evolution_target_id)
        if not evolution_target:
            messages.append("进化目标数据不存在。")
            return messages, event
        
        # 执行进化
        old_race_id = pokemon.race_id
        old_nickname = pokemon.nickname
        
        # 更新宝可梦的种族ID和相关属性
        pokemon.race_id = evolution_target_id
        
        # 更新基础属性值
        pokemon.base_hp = evolution_target.base_hp
        pokemon.base_attack = evolution_target.base_attack
        pokemon.base_defense = evolution_target.base_defense
        pokemon.base_sp_attack = evolution_target.base_sp_attack
        pokemon.base_sp_defense = evolution_target.base_sp_defense
        pokemon.base_speed = evolution_target.base_speed
        
        # 重新计算当前属性值
        self.battle_logic.recalculate_stats(pokemon)
        
        # 检查是否有新技能可以学习
        new_skills = self.battle_logic.get_evolution_skills(evolution_target_id)
        
        # 保存宝可梦状态
        await self.pokemon_repo.save_pokemon_instance(pokemon)
        
        # 创建进化事件
        event = PokemonEvolvedEvent(
            pokemon_instance_id=pokemon.instance_id,
            player_id=pokemon.player_id,
            old_race_id=old_race_id,
            new_race_id=evolution_target_id,
            old_name=old_nickname,
            new_name=pokemon.nickname,
            message=f"恭喜！你的 {old_nickname} 进化成了 {pokemon.nickname}！"
        )
        
        messages.append(event.message)
        
        # 如果有新技能可以学习，提示玩家
        for skill_id in new_skills:
            skill_metadata = await self.metadata_repo.get_skill(skill_id)
            if skill_metadata:
                messages.append(f"{pokemon.nickname} 可以学习新技能 {skill_metadata.name}！")
        
        return messages, event

    async def check_level_up_skills(self, pokemon: Pokemon, old_level: int, new_level: int) -> List[BattleEvent]:
        """检查宝可梦升级后是否可以学习新技能，并返回相关事件。"""
        events = []
        
        # 获取宝可梦种族数据
        race_data = await self.metadata_repo.get_pokemon_race(pokemon.race_id)
        if not race_data:
            return events
        
        # 获取这个级别范围内可以学习的技能
        for level in range(old_level + 1, new_level + 1):
            # 获取此级别可学习的技能列表
            level_skills = await self.metadata_repo.get_level_up_skills(pokemon.race_id, level)
            
            for skill_id in level_skills:
                # 检查宝可梦是否已经学会了这个技能
                already_known = False
                for existing_skill in pokemon.skills:
                    if existing_skill.skill_id == skill_id:
                        already_known = True
                        break
                
                if already_known:
                    continue
                
                # 获取技能数据
                skill_data = await self.metadata_repo.get_skill(skill_id)
                if not skill_data:
                    continue
                
                # 如果技能栏未满，直接学习
                if len(pokemon.skills) < 4:
                    # 创建新技能
                    new_skill = PokemonSkill(
                        skill_id=skill_id,
                        name=skill_data.name,
                        max_pp=skill_data.base_pp,
                        current_pp=skill_data.base_pp
                    )
                    
                    # 添加技能
                    pokemon.skills.append(new_skill)
                    
                    # 创建学习技能事件
                    learn_event = SkillLearnedEvent(
                        pokemon_instance_id=pokemon.instance_id,
                        pokemon_name=pokemon.nickname,
                        skill_id=skill_id,
                        skill_name=skill_data.name,
                        message=f"{pokemon.nickname} 学会了 {skill_data.name}！"
                    )
                    events.append(learn_event)
                else:
                    # 技能栏已满，需要替换
                    # 创建技能替换事件
                    current_skills_info = []
                    for skill in pokemon.skills:
                        current_skills_info.append({
                            "skill_id": skill.skill_id,
                            "name": skill.name,
                            "max_pp": skill.max_pp,
                            "current_pp": skill.current_pp
                        })
                    
                    replacement_event = SkillReplacementRequiredEvent(
                        pokemon_instance_id=pokemon.instance_id,
                        pokemon_name=pokemon.nickname,
                        new_skill_id=skill_id,
                        new_skill_name=skill_data.name,
                        current_skills=current_skills_info,
                        message=f"{pokemon.nickname} 想要学习 {skill_data.name}，但已经学会了4个技能。要忘记一个技能吗？"
                    )
                    events.append(replacement_event)
                    
                    # 将新技能数据保存到临时状态
                    if not hasattr(pokemon, "temp_data") or pokemon.temp_data is None:
                        pokemon.temp_data = {}
                    
                    pokemon.temp_data["pending_skill"] = {
                        "skill_id": skill_id,
                        "name": skill_data.name,
                        "max_pp": skill_data.base_pp,
                        "current_pp": skill_data.base_pp
                    }
                    
                    # 一次只处理一个替换请求
                    break
        
        # 保存宝可梦状态
        await self.pokemon_repo.save_pokemon_instance(pokemon)
        
        return events

    async def get_battle_info(self, battle_id: int) -> Dict[str, Any]:
        """获取战斗的详细信息。"""
        # 获取战斗数据
        battle = await self.battle_repo.get_battle(battle_id)
        if not battle:
            raise BattleNotFoundException(f"找不到战斗 ID: {battle_id}")
        
        # 获取玩家宝可梦
        player_pokemon = None
        if battle.player_active_pokemon_instance_id:
            player_pokemon = await self.pokemon_repo.get_pokemon_instance(battle.player_active_pokemon_instance_id)
        
        # 获取对手宝可梦
        opponent_pokemon = None
        if battle.is_trainer_battle and battle.trainer_active_pokemon_instance_id:
            opponent_pokemon = await self.pokemon_repo.get_pokemon_instance(battle.trainer_active_pokemon_instance_id)
        elif not battle.is_trainer_battle and battle.wild_pokemon_instance_id:
            opponent_pokemon = await self.pokemon_repo.get_pokemon_instance(battle.wild_pokemon_instance_id)
        
        # 获取玩家队伍
        player_party = await self.pokemon_repo.get_player_pokemons(battle.player_id)
        player_party = [p for p in player_party if p.in_party]
        
        # 获取训练师队伍（如果是训练师战斗）
        trainer_party = []
        if battle.is_trainer_battle and battle.trainer_id:
            trainer_party = await self.pokemon_repo.get_trainer_pokemons(battle.trainer_id)
        
        # 构建战斗信息
        battle_info = {
            "battle_id": battle.battle_id,
            "is_active": battle.is_active,
            "is_trainer_battle": battle.is_trainer_battle,
            "turn_number": battle.turn_number,
            "player_id": battle.player_id,
            "player_pokemon": player_pokemon.to_dict() if player_pokemon else None,
            "player_party": [p.to_dict() for p in player_party],
            "opponent_type": "trainer" if battle.is_trainer_battle else "wild",
            "opponent_pokemon": opponent_pokemon.to_dict() if opponent_pokemon else None,
            "opponent_party": [p.to_dict() for p in trainer_party] if battle.is_trainer_battle else [],
            "battle_state": battle.battle_state,
            "need_switch": battle.battle_state.get("need_switch", False),
            "outcome": battle.outcome
        }
        
        return battle_info

    async def get_valid_actions(self, battle_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """获取当前战斗中玩家可以执行的有效动作。"""
        # 获取战斗信息
        battle_info = await self.get_battle_info(battle_id)
        
        if not battle_info["is_active"]:
            return {"message": "战斗已结束", "actions": []}
        
        if battle_info["need_switch"]:
            # 如果需要切换宝可梦，只返回可用的切换选项
            switch_options = []
            for pokemon in battle_info["player_party"]:
                if not pokemon["is_fainted"] and pokemon["instance_id"] != battle_info["player_pokemon"]["instance_id"]:
                    switch_options.append({
                        "type": "switch",
                        "pokemon_id": pokemon["instance_id"],
                        "pokemon_name": pokemon["nickname"],
                        "level": pokemon["level"],
                        "current_hp": pokemon["current_hp"],
                        "max_hp": pokemon["max_hp"]
                    })
            
            return {
                "message": "请选择下一只宝可梦上场",
                "actions": switch_options
            }
        
        # 正常战斗动作
        valid_actions = []
        
        # 添加技能选项
        skill_options = []
        for skill in battle_info["player_pokemon"]["skills"]:
            skill_options.append({
                "type": "skill",
                "skill_id": skill["skill_id"],
                "name": skill["name"],
                "current_pp": skill["current_pp"],
                "max_pp": skill["max_pp"]
            })
        
        valid_actions.extend(skill_options)
        
        # 添加道具选项（精灵球、恢复道具等）
        player_id = battle_info["player_id"]
        player_items = await self.item_service.get_player_items(player_id)
        
        item_options = []
        for item in player_items:
            # 根据道具类型和战斗类型决定是否可用
            if item.effect_type == ItemEffectType.CAPTURE.value and not battle_info["is_trainer_battle"]:
                item_options.append({
                    "type": "item",
                    "item_id": item.item_id,
                    "name": item.name,
                    "count": item.count,
                    "effect_type": item.effect_type
                })
            elif item.effect_type in [ItemEffectType.HEAL_HP.value, ItemEffectType.HEAL_PP.value, ItemEffectType.CURE_STATUS.value]:
                item_options.append({
                    "type": "item",
                    "item_id": item.item_id,
                    "name": item.name,
                    "count": item.count,
                    "effect_type": item.effect_type
                })
        
        valid_actions.extend(item_options)
        
        # 添加切换宝可梦选项
        switch_options = []
        for pokemon in battle_info["player_party"]:
            if not pokemon["is_fainted"] and pokemon["instance_id"] != battle_info["player_pokemon"]["instance_id"]:
                switch_options.append({
                    "type": "switch",
                    "pokemon_id": pokemon["instance_id"],
                    "pokemon_name": pokemon["nickname"],
                    "level": pokemon["level"],
                    "current_hp": pokemon["current_hp"],
                    "max_hp": pokemon["max_hp"]
                })
        
        valid_actions.extend(switch_options)
        
        # 添加逃跑选项（仅野生战斗）
        if not battle_info["is_trainer_battle"]:
            valid_actions.append({
                "type": "run",
                "name": "逃跑"
            })
        
        return {
            "message": "请选择你的行动",
            "actions": valid_actions
        }

    # 在process_player_action方法中添加野生宝可梦的回合处理

    # 野生宝可梦的回合
    async def process_wild_pokemon_turn(self, player_pokemon: Pokemon, wild_pokemon: Pokemon, battle: Battle) -> List[BattleEvent]:
        """处理野生宝可梦的回合行动。"""
        events = []
        
        # 检查野生宝可梦是否已失去战斗能力
        if wild_pokemon.is_fainted or wild_pokemon.current_hp <= 0:
            return events
        
        # 检查玩家宝可梦是否已失去战斗能力
        if player_pokemon.is_fainted or player_pokemon.current_hp <= 0:
            return events
        
        # 随机选择一个野生宝可梦的技能
        available_skills = [s for s in wild_pokemon.skills if s.current_pp > 0]
        
        if not available_skills:
            # 如果没有可用技能，使用挣扎
            events.append(BattleMessageEvent(message=f"野生的 {wild_pokemon.nickname} 没有可用的技能了！"))
            events.append(BattleMessageEvent(message=f"野生的 {wild_pokemon.nickname} 使用了挣扎！"))
            
            # 挣扎对自己造成伤害
            struggle_damage = max(1, int(wild_pokemon.max_hp * 0.25))
            wild_pokemon.current_hp = max(0, wild_pokemon.current_hp - struggle_damage)
            events.append(DamageDealtEvent(
                attacker_instance_id=wild_pokemon.instance_id,
                attacker_name=wild_pokemon.nickname,
                defender_instance_id=wild_pokemon.instance_id,
                defender_name=wild_pokemon.nickname,
                skill_id=0,  # 挣扎技能ID
                skill_name="挣扎",
                damage=struggle_damage,
                is_critical=False,
                type_effectiveness=1.0,
                message=f"野生的 {wild_pokemon.nickname} 因挣扎受到了 {struggle_damage} 点伤害！"
            ))
            
            # 对玩家宝可梦造成伤害
            struggle_damage_to_player = max(1, int(player_pokemon.max_hp * 0.1))
            player_pokemon.current_hp = max(0, player_pokemon.current_hp - struggle_damage_to_player)
            events.append(DamageDealtEvent(
                attacker_instance_id=wild_pokemon.instance_id,
                attacker_name=wild_pokemon.nickname,
                defender_instance_id=player_pokemon.instance_id,
                defender_name=player_pokemon.nickname,
                skill_id=0,  # 挣扎技能ID
                skill_name="挣扎",
                damage=struggle_damage_to_player,
                is_critical=False,
                type_effectiveness=1.0,
                message=f"对 {player_pokemon.nickname} 造成了 {struggle_damage_to_player} 点伤害！"
            ))
        else:
            # 随机选择一个技能
            selected_skill = random.choice(available_skills)
            
            # 获取技能元数据
            skill_metadata = await self.metadata_repo.get_skill(selected_skill.skill_id)
            if not skill_metadata:
                events.append(BattleMessageEvent(message=f"野生的 {wild_pokemon.nickname} 尝试使用未知技能！"))
                return events
            
            events.append(BattleMessageEvent(message=f"野生的 {wild_pokemon.nickname} 使用了 {selected_skill.name}！"))
            
            # 消耗PP
            selected_skill.current_pp -= 1
            
            # 更新宝可梦的技能列表中对应技能的PP
            for i, skill_in_list in enumerate(player_pokemon.skills):
                if skill_in_list.skill_id == selected_skill.skill_id:
                    player_pokemon.skills[i] = selected_skill
                    break
            
            # 将PP变化保存到数据库
            await self.pokemon_repo.save_pokemon_instance(player_pokemon)
            
            # 执行技能效果
            skill_result = await self.battle_logic.execute_skill(
                battle=battle,
                attacker=wild_pokemon,
                defender=player_pokemon,
                skill=skill_metadata
            )
            
            # 添加技能执行事件
            skill_events = skill_result.get("events", [])
            events.extend(skill_events)
            
            # 处理状态效果
            status_effects = skill_result.get("status_effects", [])
            for status_effect in status_effects:
                target = status_effect["target"]
                effect = status_effect["effect"]
                
                await self.battle_logic.status_effect_handler.apply_status_effect(target, effect)
                
                events.append(StatusEffectAppliedEvent(
                    pokemon_instance_id=target.instance_id,
                    pokemon_name=target.nickname,
                    status_effect_id=effect.status_effect_id,
                    status_effect_name=effect.name,
                    duration=effect.duration,
                    message=f"{target.nickname} {effect.application_message}！"
                ))
        
        # 检查玩家宝可梦是否失去战斗能力
        if player_pokemon.current_hp <= 0:
            player_pokemon.current_hp = 0
            player_pokemon.is_fainted = True
            events.append(FaintEvent(
                pokemon_instance_id=player_pokemon.instance_id,
                pokemon_name=player_pokemon.nickname,
                message=f"{player_pokemon.nickname} 失去了战斗能力！"
            ))
        
        # 检查野生宝可梦是否失去战斗能力
        if wild_pokemon.current_hp <= 0:
            wild_pokemon.current_hp = 0
            wild_pokemon.is_fainted = True
            events.append(FaintEvent(
                pokemon_instance_id=wild_pokemon.instance_id,
                pokemon_name=wild_pokemon.nickname,
                message=f"野生的 {wild_pokemon.nickname} 失去了战斗能力！"
            ))
        
        return events