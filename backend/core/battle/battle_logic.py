# backend/core/battle/battle_logic.py

import math
import random
from typing import List, Dict, Any, Tuple, Optional, Callable
# Assuming Pokemon and Battle models are defined
from backend.models.pokemon import Pokemon, VolatileStatusInstance
from backend.models.battle import Battle
# Assuming Skill model is defined
from backend.models.skill import Skill, SecondaryEffect # Import SecondaryEffect
# Assuming Attribute and StatusEffect models are defined
from backend.models.attribute import Attribute
from backend.models.status_effect import StatusEffect, MajorStatusType # Import StatusEffect model and MajorStatusType
from backend.models.ability import Ability # Import Ability model
from backend.models.item import Item, ItemEffectType # Import Item model and ItemEffectType
# Import formulas for calculations
from backend.core.battle.formulas import (
    calculate_damage,
    get_type_effectiveness, # This function is now deprecated/modified, will be replaced by calculate_type_effectiveness
    check_run_success,
    calculate_catch_rate_value_A,
    perform_catch_shakes,
    calculate_type_effectiveness, # Import the modified function
    check_accuracy,
    check_critical_hit,
    calculate_stat_stage_modifier,
    get_effective_stat # Import calculation functions
)
# Assuming MetadataRepository is available
from backend.data_access.metadata_loader import MetadataRepository # Import MetadataRepository
# Import battle events
from backend.core.battle.events import (
    BattleEvent, StatStageChangeEvent, DamageDealtEvent, FaintEvent,
    StatusEffectAppliedEvent, StatusEffectRemovedEvent, HealEvent,
    AbilityTriggerEvent, FieldEffectEvent, VolatileStatusChangeEvent,
    ForcedSwitchEvent, ItemTriggerEvent, AbilityChangeEvent, # Import new event types
    MoveMissedEvent, BattleMessageEvent, SkillUsedEvent, # Import additional events and SkillUsedEvent
    BattleEndEvent, SwitchOutEvent, SwitchInEvent, ExperienceChangeEvent,
    SkillLearnedEvent, EvolutionEvent, CatchAttemptEvent, RunAttemptEvent,
    ConfusionDamageEvent, FlinchEvent, # Import ConfusionDamageEvent and FlinchEvent
    ItemUsedEvent, # Import ItemUsedEvent
    CaptureAttemptEvent, # Import CaptureAttemptEvent
    CaptureSuccessEvent, # Import CaptureSuccessEvent
    CaptureFailureEvent, # Import CaptureFailureEvent
    PPHealEvent, # Import PPHealEvent
    VolatileStatusAppliedEvent, VolatileStatusRemovedEvent, 
    VolatileStatusTriggeredEvent
)
# Import handlers
from backend.core.battle.status_effect_handler import StatusEffectHandler # Import StatusEffectHandler
# Import logger
from backend.utils.logger import get_logger
from backend.core.game_logic import GameLogic # Import GameLogic for use in BattleLogic
from backend.utils.effectiveness import EffectivenessCalculator
from backend.core.pet.evolution_handler import EvolutionHandler # Import EvolutionHandler
from backend.core.pokemon_factory import PokemonFactory # Import PokemonFactory
import json # 导入 json 模块
from backend.models.events import (
    BattleEvent, DamageEvent, HealEvent, StatusEffectEvent, 
    FaintEvent, BattleMessageEvent, ExperienceGainedEvent, LevelUpEvent, 
    EvolutionEvent, SkillLearnedEvent, PPHealEvent, MissEvent,
    StatStageChangeEvent # 新增导入
)

logger = get_logger(__name__)

# Define event listener type hint
EventListener = Callable[[Battle, BattleEvent], None]

class BattleLogic:
    """
    Handles the core logic of a Pokemon battle.

    This class is responsible for processing turns, executing actions,
    calculating outcomes, and managing battle state.
    """

    MAX_STAT_STAGE = 6
    MIN_STAT_STAGE = -6

    def __init__(self, metadata_repo: MetadataRepository, status_effect_handler: StatusEffectHandler, pokemon_factory: PokemonFactory): # 添加 pokemon_factory 参数
        self._metadata_repo = metadata_repo
        self._status_effect_handler = status_effect_handler
        self._pokemon_factory = pokemon_factory # 初始化 PokemonFactory
        self._evolution_handler = EvolutionHandler(metadata_repo, pokemon_factory) # 初始化 EvolutionHandler
        self._event_subscribers: Dict[str, List[Callable[[BattleEvent], None]]] = {}
        self._battle_event_history: List[BattleEvent] = []

    def subscribe(self, event_type: str, listener: Callable[[BattleEvent], None]):
        """Subscribes a listener function to a specific event type."""
        if event_type not in self._event_subscribers:
            self._event_subscribers[event_type] = []
        self._event_subscribers[event_type].append(listener)

    def publish(self, battle: Battle, event: BattleEvent):
        """Publishes an event to all subscribed listeners."""
        logger.debug(f"Publishing event: {event.event_type}")
        self._battle_event_history.append(event) # Record event history
        if event.event_type in self._event_subscribers:
            for listener in self._event_subscribers[event.event_type]:
                try:
                    # Listeners should ideally be synchronous or handle their own async
                    listener(event)
                except Exception as e:
                    logger.error(f"Error in event listener for {event.event_type}: {e}", exc_info=True)

    async def _execute_item_action(self, battle: Battle, user: Pokemon, item_id: int, target_pokemon_id: Optional[int] = None) -> List[BattleEvent]:
        """
        Executes the action of using an item in battle.

        Args:
            battle: The current battle instance.
            user: The Pokemon using the item.
            item_id: The ID of the item being used.
            target_pokemon_id: The ID of the target Pokemon, if applicable.

        Returns:
            A list of BattleEvents generated by the item action.
        """
        events: List[BattleEvent] = []
        item = await self._metadata_repo.get_item_data(item_id)
        if not item:
            logger.error(f"在 _execute_item_action 中找不到道具 ID: {item_id}")
            events.append(BattleMessageEvent(message=f"找不到指定的道具。"))
            return events

        actual_user = battle.get_pokemon_instance_by_id(user.pokemon_id)
        if not actual_user:
            logger.error(f"道具使用者 {user.name} (ID: {user.pokemon_id}) 不在战斗中。")
            events.append(BattleMessageEvent(message=f"道具使用者不在战斗中。"))
            return events

        target_pokemon = None
        if target_pokemon_id:
            target_pokemon = battle.get_pokemon_instance_by_id(target_pokemon_id)
            if not target_pokemon:
                logger.error(f"道具目标 ID: {target_pokemon_id} 不在战斗中。")
                events.append(BattleMessageEvent(message=f"道具目标不在战斗中。"))
                return events
        
        item_effect_type = item.effect_type
        
        # 处理各种道具效果类型
        if item_effect_type == ItemEffectType.HEAL_HP.value:
            # ... 已有代码 ...
        elif item_effect_type == ItemEffectType.CURE_STATUS.value:
            # ... 已有代码 ...
        elif item_effect_type == ItemEffectType.HEAL_PP.value:
            # ... 已有代码 ...
        elif item_effect_type == ItemEffectType.STAT_BOOST_BATTLE.value:
            # ... 已有代码 ...
        elif item_effect_type == ItemEffectType.EVOLUTION.value:
            # 进化道具需要目标宝可梦
            if not target_pokemon:
                logger.warning(f"道具 {item.name} (EVOLUTION) 需要目标宝可梦。")
                events.append(BattleMessageEvent(message=f"使用 {item.name} 需要选择一个宝可梦作为目标。"))
                return events
            
            # 检查目标是否是玩家的宝可梦（不能对敌方宝可梦使用进化道具）
            if target_pokemon.trainer_id != user.trainer_id:
                logger.warning(f"不能对敌方宝可梦 {target_pokemon.name} 使用进化道具 {item.name}。")
                events.append(BattleMessageEvent(message=f"不能对敌方宝可梦使用 {item.name}。"))
                return events
            
            # 使用 EvolutionHandler 检查并处理进化
            try:
                # 假设 battle_logic 有一个 evolution_handler 属性
                evolution_event = await self._evolution_handler.check_and_process_evolution(target_pokemon, item)
                
                if evolution_event:
                    # 进化成功
                    events.append(evolution_event)
                    events.append(ItemUsedEvent(
                        item_id=item.item_id,
                        item_name=item.name,
                        user_id=user.pokemon_id,
                        user_name=user.name,
                        target_id=target_pokemon.pokemon_id if target_pokemon else None,
                        target_name=target_pokemon.name if target_pokemon else None,
                        message=f"{user.name} 对 {target_pokemon.name} 使用了 {item.name}！"
                    ))
                    return events
                else:
                    # 进化未发生 (可能条件不满足，或者道具不能触发进化)
                    events.append(BattleMessageEvent(message=f"{item.name} 对 {target_pokemon.name} 没有效果。"))
                    return events # 道具不消耗
            except Exception as e:
                logger.error(f"使用进化道具 {item.name} 时发生错误: {e}", exc_info=True)
                events.append(BattleMessageEvent(message=f"使用 {item.name} 时发生错误。"))
                return events
                
        elif item_effect_type == ItemEffectType.CAPTURE.value:
            # 捕获道具需要目标宝可梦
            if not target_pokemon:
                logger.warning(f"道具 {item.name} (CAPTURE) 需要目标宝可梦。")
                events.append(BattleMessageEvent(message=f"使用 {item.name} 需要选择一个宝可梦作为目标。"))
                return events
            
            # 检查目标是否是野生宝可梦（不能捕获训练家的宝可梦）
            if target_pokemon.trainer_id is not None and target_pokemon.trainer_id != 0:
                logger.warning(f"不能捕获训练家的宝可梦 {target_pokemon.name}。")
                events.append(BattleMessageEvent(message=f"不能捕获训练家的宝可梦。"))
                return events
            
            # 检查战斗类型是否允许捕获
            if battle.battle_type != "wild":
                logger.warning(f"只能在野生战斗中使用捕获道具 {item.name}。")
                events.append(BattleMessageEvent(message=f"只能在野生战斗中使用 {item.name}。"))
                return events
            
            # 解析捕获率修正值
            capture_rate_modifier = 1.0
            if item.use_effect:
                try:
                    capture_rate_modifier = float(item.use_effect)
                except ValueError:
                    logger.warning(f"道具 {item.name} 的 use_effect 值 '{item.use_effect}' 无法解析为捕获率修正值，使用默认值 1.0。")
            
            # 计算捕获成功率
            # 这里简化处理，实际游戏中捕获率计算更复杂
            base_capture_rate = await self._metadata_repo.get_pokemon_capture_rate(target_pokemon.race_id)
            if base_capture_rate is None:
                base_capture_rate = 45  # 默认值，大多数普通宝可梦的捕获率
            
            # 计算HP比例因子 (HP越低，捕获率越高)
            hp_factor = 1.0
            if hasattr(target_pokemon, 'current_hp') and hasattr(target_pokemon, 'get_stat'):
                max_hp = target_pokemon.get_stat("hp")
                if max_hp > 0:
                    hp_ratio = target_pokemon.current_hp / max_hp
                    hp_factor = 2.0 - hp_ratio  # HP为满时是1.0，HP为0时是2.0
            
            # 计算状态效果因子 (有些状态效果会提高捕获率)
            status_factor = 1.0
            for status in target_pokemon.status_effects:
                if status.effect_type in ["sleep", "freeze"]:
                    status_factor = 2.5
                    break
                elif status.effect_type in ["paralyze", "poison", "burn"]:
                    status_factor = 1.5
                    break
            
            # 最终捕获率计算
            final_capture_rate = min(255, base_capture_rate * capture_rate_modifier * hp_factor * status_factor)
            
            # 随机决定是否捕获成功
            capture_roll = random.randint(0, 255)
            capture_success = capture_roll < capture_threshold
            
            if capture_success:
                # 捕获成功
                events.append(BattleMessageEvent(message=f"{target_pokemon.name} 被捕获了！"))
                events.append(ItemUsedEvent(
                    item_id=item.item_id,
                    item_name=item.name,
                    user_id=user.pokemon_id,
                    user_name=user.name,
                    target_id=target_pokemon.pokemon_id,
                    target_name=target_pokemon.name,
                    message=f"{user.name} 对 {target_pokemon.name} 使用了 {item.name}！"
                ))
                
                # 设置战斗结果为捕获成功
                battle.result = "capture"
                battle.captured_pokemon_id = target_pokemon.pokemon_id
                
                # 结束战斗
                battle.is_active = False
                battle_end_event = BattleEndEvent(
                    winner_id=user.trainer_id,
                    loser_id=None,  # 野生战斗没有败者ID
                    result="capture",
                    message=f"战斗结束！{user.name} 成功捕获了野生的 {target_pokemon.name}！"
                )
                events.append(battle_end_event)
                
                return events
            else:
                # 捕获失败
                shake_count = min(3, int(capture_threshold / 85))  # 0-3次摇晃
                shake_message = ""
                if shake_count == 0:
                    shake_message = f"{target_pokemon.name} 立刻从精灵球中挣脱出来了！"
                elif shake_count == 1:
                    shake_message = f"精灵球摇晃了1次，但 {target_pokemon.name} 挣脱出来了！"
                elif shake_count == 2:
                    shake_message = f"精灵球摇晃了2次，但 {target_pokemon.name} 挣脱出来了！"
                elif shake_count == 3:
                    shake_message = f"精灵球摇晃了3次，差一点就成功了，但 {target_pokemon.name} 挣脱出来了！"
                
                events.append(BattleMessageEvent(message=shake_message))
                events.append(ItemUsedEvent(
                    item_id=item.item_id,
                    item_name=item.name,
                    user_id=user.pokemon_id,
                    user_name=user.name,
                    target_id=target_pokemon.pokemon_id,
                    target_name=target_pokemon.name,
                    message=f"{user.name} 对 {target_pokemon.name} 使用了 {item.name}！"
                ))
                
                return events
        else:
            logger.warning(f"未知的道具效果类型: {item_effect_type} for item {item.name}")
            events.append(BattleMessageEvent(message=f"道具 {item.name} 似乎没有任何效果。"))
        
        return events

    def _apply_stat_stage_change(self, pokemon: Pokemon, stat_name: str, change: int, source_name: str) -> Tuple[int, int, Optional[str]]:
        """
        应用能力等级变化到指定的宝可梦。

        Args:
            pokemon: 目标宝可梦。
            stat_name: 要改变的能力名称 (e.g., "attack", "speed")。
            change: 能力等级的变化量 (e.g., +1, +2, -1)。
            source_name: 效果来源的名称 (例如道具名或技能名)。

        Returns:
            Tuple[int, int, Optional[str]]:
                - actual_change: 实际发生的能力等级变化量。
                - new_stage: 变化后的新能力等级。
                - message_override: 一个可选的消息字符串，用于覆盖默认的 StatStageChangeEvent 消息
                                   (例如，当能力已达上限/下限时)。
        """
        stat_translation_cn = {
            "attack": "攻击", "defense": "防御", "special_attack": "特攻",
            "special_defense": "特防", "speed": "速度", "accuracy": "命中率", "evasion": "闪避率"
        }
        stat_name_cn = stat_translation_cn.get(stat_name, stat_name)

        if stat_name not in pokemon.battle_stat_stages:
            logger.error(f"尝试修改宝可梦 {pokemon.name} 未知的战斗属性: {stat_name}")
            # 返回0变化，当前等级，以及一个错误消息
            return 0, pokemon.battle_stat_stages.get(stat_name, 0), f"错误：{pokemon.name} 没有名为 {stat_name_cn} 的战斗能力。"

        current_stage = pokemon.battle_stat_stages[stat_name]
        
        if change > 0: # 尝试提升
            if current_stage >= self.MAX_STAT_STAGE:
                logger.info(f"{pokemon.name} 的 {stat_name_cn} 等级已达最高 ({self.MAX_STAT_STAGE})，无法再提升。")
                return 0, current_stage, f"因为 {source_name}，{pokemon.name} 的 {stat_name_cn} 已经最高，无法再提升了！"
            
            new_stage = min(current_stage + change, self.MAX_STAT_STAGE)
        elif change < 0: # 尝试降低
            if current_stage <= self.MIN_STAT_STAGE:
                logger.info(f"{pokemon.name} 的 {stat_name_cn} 等级已达最低 ({self.MIN_STAT_STAGE})，无法再降低。")
                return 0, current_stage, f"因为 {source_name}，{pokemon.name} 的 {stat_name_cn} 已经最低，无法再降低了！"
            new_stage = max(current_stage + change, self.MIN_STAT_STAGE)
        else: # change is 0
            return 0, current_stage, None # 没有变化，无需特定消息

        actual_change = new_stage - current_stage
        pokemon.battle_stat_stages[stat_name] = new_stage
        
        logger.debug(f"{pokemon.name} 的 {stat_name_cn} 等级因 {source_name} 从 {current_stage} 变为 {new_stage} (请求变化: {change}, 实际变化: {actual_change})")
        
        # 如果有实际变化，让 StatStageChangeEvent 自己生成消息
        if actual_change != 0:
            return actual_change, new_stage, None 
        else: # 如果没有实际变化（例如，尝试提升已达上限的属性），我们已经返回了特定消息
            # 此处逻辑上不应该到达，因为上面已经处理了 change > 0 和 change < 0 且已达极限的情况
            # 但为了保险，如果 actual_change 是0但没有 message_override，说明逻辑可能有误
            logger.warning(f"在 _apply_stat_stage_change 中，actual_change 为0但没有 message_override。Stat: {stat_name}, Change: {change}, Current: {current_stage}")
            return 0, current_stage, f"{pokemon.name} 的 {stat_name_cn} 没有变化。"

    def process_turn_start(self, battle: Battle) -> List[BattleEvent]:
        """
        处理回合开始时的逻辑，包括检查和处理各种状态效果。
        
        Args:
            battle: 战斗实例
            
        Returns:
            List[BattleEvent]: 处理过程中产生的事件列表
        """
        events = []
        
        # 处理所有参与战斗的宝可梦
        all_pokemons = battle.player_pokemons + battle.wild_pokemons
        
        for pokemon in all_pokemons:
            # 处理持久状态效果（如中毒、麻痹等）
            # 这部分逻辑可能已经在其他地方实现
            
            # 处理挥发性状态效果
            events.extend(self._process_volatile_status_turn_start(pokemon))
            
        return events
    
    def process_turn_end(self, battle: Battle) -> List[BattleEvent]:
        """
        处理回合结束时的逻辑，包括检查和处理各种状态效果。
        
        Args:
            battle: 战斗实例
            
        Returns:
            List[BattleEvent]: 处理过程中产生的事件列表
        """
        events = []
        
        # 处理所有参与战斗的宝可梦
        all_pokemons = battle.player_pokemons + battle.wild_pokemons
        
        for pokemon in all_pokemons:
            # 处理持久状态效果（如中毒、麻痹等）
            # 这部分逻辑可能已经在其他地方实现
            
            # 处理挥发性状态效果
            events.extend(self._process_volatile_status_turn_end(pokemon))
            
        return events
    
    def _process_volatile_status_turn_start(self, pokemon: Pokemon) -> List[BattleEvent]:
        """
        处理回合开始时的挥发性状态效果。
        
        Args:
            pokemon: 宝可梦实例
            
        Returns:
            List[BattleEvent]: 处理过程中产生的事件列表
        """
        events = []
        
        # 创建一个新的列表来存储需要保留的状态
        statuses_to_keep = []
        
        for status in pokemon.volatile_status:
            # 检查状态是否已经过期
            if status.turns_remaining is not None:
                status.turns_remaining -= 1
                
                if status.turns_remaining <= 0:
                    # 状态已过期，生成移除事件
                    message = f"{pokemon.nickname}的{status.status_type}状态消失了！"
                    events.append(VolatileStatusRemovedEvent(
                        pokemon=pokemon,
                        status_type=status.status_type,
                        message=message
                    ))
                    continue  # 不将此状态添加到保留列表中
            
            # 处理特定状态的回合开始效果
            if status.status_type == "confusion":
                # 混乱状态在回合开始时检查是否会自伤
                if random.random() < 0.5:  # 50%几率自伤
                    # 计算自伤伤害（通常是一个固定公式）
                    damage = max(1, pokemon.max_hp // 8)  # 示例：最大HP的1/8，至少1点
                    old_hp = pokemon.current_hp
                    pokemon.current_hp = max(0, pokemon.current_hp - damage)
                    new_hp = pokemon.current_hp
                    
                    events.append(ConfusionDamageEvent(
                        pokemon=pokemon,
                        damage=damage,
                        old_hp=old_hp,
                        new_hp=new_hp
                    ))
                    
                    events.append(VolatileStatusTriggeredEvent(
                        pokemon=pokemon,
                        status_type="confusion",
                        effect_description="self_damage",
                        message=f"{pokemon.nickname}混乱了，攻击了自己！"
                    ))
                    
                    # 检查是否因自伤而失去战斗能力
                    if pokemon.current_hp <= 0:
                        pokemon.is_fainted = True
                        events.append(FaintEvent(
                            pokemon=pokemon,
                            message=f"{pokemon.nickname}失去了战斗能力！"
                        ))
            
            # 将未过期的状态添加到保留列表
            statuses_to_keep.append(status)
        
        # 更新宝可梦的挥发性状态列表
        pokemon.volatile_status = statuses_to_keep
        
        return events
    
    def _process_volatile_status_turn_end(self, pokemon: Pokemon) -> List[BattleEvent]:
        """
        处理回合结束时的挥发性状态效果。
        
        Args:
            pokemon: 宝可梦实例
            
        Returns:
            List[BattleEvent]: 处理过程中产生的事件列表
        """
        events = []
        
        # 创建一个新的列表来存储需要保留的状态
        statuses_to_keep = []
        
        for status in pokemon.volatile_status:
            # 某些状态在回合结束时自动解除，如畏缩
            if status.status_type == "flinch":
                events.append(VolatileStatusRemovedEvent(
                    pokemon=pokemon,
                    status_type="flinch",
                    message=f"{pokemon.nickname}不再畏缩。"
                ))
                continue  # 不将畏缩状态添加到保留列表
            
            # 处理其他可能在回合结束时有特殊效果的状态
            # ...
            
            # 将需要保留的状态添加到列表
            statuses_to_keep.append(status)
        
        # 更新宝可梦的挥发性状态列表
        pokemon.volatile_status = statuses_to_keep
        
        return events
    
    def can_pokemon_act(self, pokemon: Pokemon) -> Tuple[bool, Optional[str], Optional[BattleEvent]]:
        """
        检查宝可梦是否能够行动，考虑各种状态效果。
        
        Args:
            pokemon: 宝可梦实例
            
        Returns:
            Tuple[bool, Optional[str], Optional[BattleEvent]]: 
                - 是否能够行动
                - 不能行动的原因（如果不能行动）
                - 相关的事件（如果有）
        """
        # 检查是否已经失去战斗能力
        if pokemon.is_fainted:
            return False, "fainted", None
        
        # 检查持久状态效果（如麻痹、睡眠等）
        # 这部分逻辑可能已经在其他地方实现
        
        # 检查挥发性状态效果
        for status in pokemon.volatile_status:
            if status.status_type == "flinch":
                event = FlinchEvent(pokemon=pokemon)
                return False, "flinch", event
            
            # 检查其他可能阻止行动的状态
            # ...
        
        return True, None, None
    
    def apply_volatile_status(self, pokemon: Pokemon, status_type: str, turns: Optional[int] = None, 
                             source_skill_id: Optional[int] = None, data: Dict[str, Any] = None) -> List[BattleEvent]:
        """
        给宝可梦施加一个挥发性状态。
        
        Args:
            pokemon: 目标宝可梦
            status_type: 状态类型
            turns: 持续回合数
            source_skill_id: 来源技能ID
            data: 额外的状态数据
            
        Returns:
            List[BattleEvent]: 处理过程中产生的事件列表
        """
        events = []
        
        # 检查是否已经有相同类型的状态
        for existing_status in pokemon.volatile_status:
            if existing_status.status_type == status_type:
                # 某些状态可能有特殊的叠加或覆盖规则
                if status_type == "confusion":
                    # 混乱状态不叠加，但可以刷新持续时间
                    existing_status.turns_remaining = turns
                    events.append(BattleMessageEvent(
                        message=f"{pokemon.nickname}已经处于混乱状态！"
                    ))
                    return events
                # 处理其他状态的叠加规则
                # ...
        
        # 创建新的状态实例
        new_status = VolatileStatusInstance(
            status_type=status_type,
            turns_remaining=turns,
            source_skill_id=source_skill_id,
            data=data or {}
        )
        
        # 添加到宝可梦的状态列表
        pokemon.volatile_status.append(new_status)
        
        # 生成状态施加事件
        message = self._get_volatile_status_message(pokemon, status_type, "applied")
        events.append(VolatileStatusAppliedEvent(
            pokemon=pokemon,
            status_type=status_type,
            turns=turns,
            message=message
        ))
        
        return events
    
    def remove_volatile_status(self, pokemon: Pokemon, status_type: str) -> List[BattleEvent]:
        """
        移除宝可梦的一个挥发性状态。
        
        Args:
            pokemon: 目标宝可梦
            status_type: 状态类型
            
        Returns:
            List[BattleEvent]: 处理过程中产生的事件列表
        """
        events = []
        
        # 检查宝可梦是否有此状态
        has_status = False
        new_status_list = []
        
        for status in pokemon.volatile_status:
            if status.status_type == status_type:
                has_status = True
                continue  # 不将此状态添加到新列表
            new_status_list.append(status)
        
        if has_status:
            # 更新宝可梦的状态列表
            pokemon.volatile_status = new_status_list
            
            # 生成状态移除事件
            message = self._get_volatile_status_message(pokemon, status_type, "removed")
            events.append(VolatileStatusRemovedEvent(
                pokemon=pokemon,
                status_type=status_type,
                message=message
            ))
        
        return events
    
    def _get_volatile_status_message(self, pokemon: Pokemon, status_type: str, action: str) -> str:
        """
        获取挥发性状态变化的消息文本。
        
        Args:
            pokemon: 宝可梦实例
            status_type: 状态类型
            action: 动作类型（"applied"或"removed"）
            
        Returns:
            str: 消息文本
        """
        messages = {
            "confusion": {
                "applied": f"{pokemon.nickname}混乱了！",
                "removed": f"{pokemon.nickname}不再混乱了！"
            },
            "flinch": {
                "applied": f"{pokemon.nickname}畏缩了！",
                "removed": f"{pokemon.nickname}不再畏缩。"
            },
            "taunt": {
                "applied": f"{pokemon.nickname}被挑衅了！",
                "removed": f"{pokemon.nickname}不再被挑衅。"
            },
            "encore": {
                "applied": f"{pokemon.nickname}被再来一次了！",
                "removed": f"{pokemon.nickname}不再被再来一次。"
            },
            "protect": {
                "applied": f"{pokemon.nickname}保护自己！",
                "removed": f"{pokemon.nickname}的保护消失了。"
            },
            "leech_seed": {
                "applied": f"{pokemon.nickname}被种子寄生了！",
                "removed": f"{pokemon.nickname}摆脱了种子寄生。"
            },
            # 添加更多状态类型的消息
        }
        
        # 获取指定状态和动作的消息，如果没有定义则使用默认消息
        default_messages = {
            "applied": f"{pokemon.nickname}获得了{status_type}状态！",
            "removed": f"{pokemon.nickname}的{status_type}状态消失了！"
        }
        
        return messages.get(status_type, default_messages).get(action, default_messages[action])
    
    def execute_skill(self, battle: Battle, attacker: Pokemon, target: Pokemon, skill: Skill) -> List[BattleEvent]:
        """
        执行技能攻击。
        
        Args:
            battle: 战斗实例
            attacker: 攻击方宝可梦
            target: 防守方宝可梦
            skill: 使用的技能
            
        Returns:
            List[BattleEvent]: 执行过程中产生的事件列表
        """
        events = []
        
        # 检查攻击方是否能够行动
        can_act, reason, event = self.can_pokemon_act(attacker)
        if not can_act:
            if event:
                events.append(event)
            return events
        
        # 检查技能是否命中
        # 这部分逻辑可能已经在其他地方实现
        
        # 处理技能效果
        # 这部分逻辑可能已经在其他地方实现
        
        # 处理技能的附加效果，如施加挥发性状态
        if skill.additional_effects:
            for effect in skill.additional_effects:
                if effect.effect_type == "apply_volatile_status":
                    # 根据几率判断是否触发附加效果
                    if random.random() < effect.chance:
                        status_type = effect.params.get("status_type")
                        turns = effect.params.get("turns")
                        events.extend(self.apply_volatile_status(
                            pokemon=target,
                            status_type=status_type,
                            turns=turns,
                            source_skill_id=skill.skill_id
                        ))
        
        return events
    
    def handle_battle_end(self, battle: Battle) -> None:
        """
        处理战斗结束时的清理工作，包括清除所有宝可梦的挥发性状态。
        
        Args:
            battle: 战斗实例
        """
        # 清除所有参与战斗的宝可梦的挥发性状态
        all_pokemons = battle.player_pokemons + battle.wild_pokemons
        
        for pokemon in all_pokemons:
            # 清空挥发性状态列表
            pokemon.volatile_status = []
            
            # 重置战斗中的能力等级变化
            pokemon.battle_stat_stages = {
                "attack": 0,
                "defense": 0,
                "special_attack": 0,
                "special_defense": 0,
                "speed": 0,
                "accuracy": 0,
                "evasion": 0
            }
            
            # 标记宝可梦不再处于战斗中
            pokemon.is_in_battle = False
