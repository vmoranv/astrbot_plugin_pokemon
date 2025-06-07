import math
import random
from typing import List, Dict, Any, Tuple, Optional, Callable
from backend.models.event import MissEvent
from backend.models.pokemon import Pokemon, VolatileStatusInstance
from backend.models.battle import Battle
from backend.models.skill import Skill, SecondaryEffect
from backend.models.attribute import Attribute
from backend.models.status_effect import StatusEffect, MajorStatusType
from backend.models.item import Item, ItemEffectType
from backend.core.battle.formulas import (
    calculate_damage,
    get_type_effectiveness,
    check_run_success,
    calculate_catch_rate_value_A,
    perform_catch_shakes,
    calculate_type_effectiveness,
    check_accuracy,
    check_critical_hit,
    calculate_stat_stage_modifier,
    get_effective_stat
)
from backend.data_access.metadata_loader import MetadataRepository
from backend.core.battle.events import (
    BattleEvent, StatStageChangeEvent, DamageDealtEvent, FaintEvent,
    StatusEffectAppliedEvent, StatusEffectRemovedEvent, HealEvent,
    AbilityTriggerEvent, FieldEffectEvent, VolatileStatusChangeEvent,
    ForcedSwitchEvent, ItemTriggerEvent, AbilityChangeEvent,
    MoveMissedEvent, BattleMessageEvent, SkillUsedEvent,
    BattleEndEvent, SwitchOutEvent, SwitchInEvent, ExperienceChangeEvent,
    SkillLearnedEvent, EvolutionEvent, CatchAttemptEvent, RunAttemptEvent,
    ConfusionDamageEvent, FlinchEvent,
    ItemUsedEvent,
    CaptureAttemptEvent, CaptureSuccessEvent, CaptureFailureEvent,
    PPHealEvent, VolatileStatusAppliedEvent, VolatileStatusRemovedEvent, 
    VolatileStatusTriggeredEvent, MissEvent
)
from backend.core.battle.status_effect_handler import StatusEffectHandler
from backend.utils.logger import get_logger
from backend.core.game_logic import GameLogic
from backend.core.pet.evolution_handler import EvolutionHandler
from backend.core.services.pokemon_factory import PokemonFactory


logger = get_logger(__name__)

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
        self._evolution_handler = EvolutionHandler(metadata_repo, pokemon_factory) # 初始化 EvolutionHandler
        self._pokemon_factory = pokemon_factory # 保存 pokemon_factory 实例
        self._game_logic = GameLogic(metadata_repo) # 初始化 GameLogic
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
        执行战斗中的道具使用动作。

        Args:
            battle: 当前的战斗对象。
            user: 使用道具的宝可梦。
            item_id: 使用的道具ID。
            target_pokemon_id: 目标宝可梦的实例ID。

        Returns:
            一个包含本次动作产生的战斗事件的列表。
        """
        events: List[BattleEvent] = []
        item = await self._metadata_repo.get_item_by_id(item_id)
        if not item:
            logger.error(f"Item with ID {item_id} not found in metadata.")
            events.append(BattleMessageEvent(message="找不到指定的道具。"))
            return events

        target_pokemon: Optional[Pokemon] = None
        if target_pokemon_id:
            target_pokemon = battle.get_pokemon_by_instance_id(target_pokemon_id)

        item_effect_type = item.effect_type

        def create_item_used_event(consumed: bool = True) -> ItemUsedEvent:
            message = f"{user.nickname} 对 {target_pokemon.nickname} 使用了 {item.name}！" if target_pokemon else f"{user.nickname} 使用了 {item.name}！"
            return ItemUsedEvent(
                item_id=item.item_id,
                item_name=item.name,
                user_id=user.instance_id,
                user_name=user.nickname,
                target_id=target_pokemon.instance_id if target_pokemon else None,
                target_name=target_pokemon.nickname if target_pokemon else None,
                message=message,
                consumed=consumed
            )

        # 大多数治疗和增益道具需要一个目标
        if item_effect_type in [
            ItemEffectType.HEAL_HP.value,
            ItemEffectType.CURE_STATUS.value,
            ItemEffectType.HEAL_PP.value,
            ItemEffectType.STAT_BOOST_BATTLE.value
        ]:
            if not target_pokemon:
                logger.warning(f"Item {item.name} ({item_effect_type}) requires a target Pokemon.")
                events.append(BattleMessageEvent(message=f"使用 {item.name} 需要选择一个宝可梦作为目标。"))
                return events

        # 处理各种道具效果类型
        if item_effect_type == ItemEffectType.HEAL_HP.value:
            if target_pokemon.current_hp <= 0:
                events.append(BattleMessageEvent(message=f"{target_pokemon.nickname} 已经倒下，无法恢复HP。"))
                return events
            if target_pokemon.current_hp >= target_pokemon.stats['hp']:
                events.append(BattleMessageEvent(message=f"{target_pokemon.nickname} 的HP已满。"))
                return events

            heal_amount = 0
            if item.use_effect and item.use_effect.isdigit():
                heal_amount = int(item.use_effect)
            elif item.use_effect == 'max':
                heal_amount = target_pokemon.stats['hp']
            
            if heal_amount > 0:
                original_hp = target_pokemon.current_hp
                target_pokemon.current_hp = min(target_pokemon.stats['hp'], original_hp + heal_amount)
                amount_healed = target_pokemon.current_hp - original_hp
                
                events.append(create_item_used_event())
                events.append(HealEvent(
                    target_instance_id=target_pokemon.instance_id,
                    target_name=target_pokemon.nickname,
                    amount_healed=amount_healed,
                    current_hp=target_pokemon.current_hp,
                    max_hp=target_pokemon.stats['hp'],
                    source='item',
                    message=f"{target_pokemon.nickname} 恢复了 {amount_healed} HP！"
                ))
            else:
                events.append(BattleMessageEvent(message=f"{item.name} 没有效果。"))

        elif item_effect_type == ItemEffectType.CURE_STATUS.value:
            if not target_pokemon.major_status:
                events.append(BattleMessageEvent(message=f"{target_pokemon.nickname} 没有异常状态。"))
                return events

            status_to_cure = item.use_effect.upper()
            if status_to_cure == 'ALL' or status_to_cure == target_pokemon.major_status.name:
                cured_status = target_pokemon.major_status
                target_pokemon.major_status = None
                events.append(create_item_used_event())
                events.append(StatusEffectRemovedEvent(
                    target_instance_id=target_pokemon.instance_id,
                    target_name=target_pokemon.nickname,
                    status_name=cured_status.value,
                    message=f"{target_pokemon.nickname} 的 {cured_status.value} 状态解除了！"
                ))
            else:
                events.append(BattleMessageEvent(message=f"{item.name} 对 {target_pokemon.nickname} 的状态没有效果。"))

        elif item_effect_type == ItemEffectType.HEAL_PP.value:
            pp_healed_total = 0
            for skill_instance in target_pokemon.skills:
                skill_data = await self._metadata_repo.get_skill_by_id(skill_instance.skill_id)
                if skill_instance.current_pp < skill_data.pp:
                    heal_amount = 0
                    if item.use_effect and item.use_effect.isdigit():
                        heal_amount = int(item.use_effect)
                    elif item.use_effect == 'max':
                        heal_amount = skill_data.pp
                    
                    original_pp = skill_instance.current_pp
                    skill_instance.current_pp = min(skill_data.pp, original_pp + heal_amount)
                    pp_healed_total += (skill_instance.current_pp - original_pp)

            if pp_healed_total > 0:
                events.append(create_item_used_event())
                events.append(PPHealEvent(
                    target_instance_id=target_pokemon.instance_id,
                    target_name=target_pokemon.nickname,
                    amount_healed=pp_healed_total,
                    message=f"{target_pokemon.nickname} 的技能PP恢复了！"
                ))
            else:
                events.append(BattleMessageEvent(message=f"{target_pokemon.nickname} 的所有技能PP都已回满。"))

        elif item_effect_type == ItemEffectType.STAT_BOOST_BATTLE.value:
            try:
                stat_str, stage_str = item.use_effect.split(':')
                stage_change = int(stage_str)
                stat_to_boost = stat_str.lower()
                
                current_stage = target_pokemon.stat_stages.get(stat_to_boost, 0)
                if current_stage >= self.MAX_STAT_STAGE:
                    events.append(BattleMessageEvent(message=f"{target_pokemon.nickname} 的能力已经无法再提升了！"))
                    return events
                
                new_stage = min(self.MAX_STAT_STAGE, current_stage + stage_change)
                actual_change = new_stage - current_stage
                target_pokemon.stat_stages[stat_to_boost] = new_stage
                
                events.append(create_item_used_event())
                events.append(StatStageChangeEvent(
                    target_instance_id=target_pokemon.instance_id,
                    target_name=target_pokemon.nickname,
                    stat=stat_to_boost,
                    change=actual_change,
                    message=f"{target_pokemon.nickname} 的 {stat_to_boost} 大幅提升了！" if actual_change > 1 else f"{target_pokemon.nickname} 的 {stat_to_boost} 提升了！"
                ))
            except (ValueError, KeyError) as e:
                logger.error(f"解析道具 {item.name} 的 use_effect '{item.use_effect}' 失败: {e}", exc_info=True)
                events.append(BattleMessageEvent(message=f"使用 {item.name} 时发生错误。"))

        elif item_effect_type == ItemEffectType.EVOLUTION.value:
            if not target_pokemon:
                logger.warning(f"道具 {item.name} (EVOLUTION) 需要目标宝可梦。")
                events.append(BattleMessageEvent(message=f"使用 {item.name} 需要选择一个宝可梦作为目标。"))
                return events
            
            try:
                evolution_event = await self._evolution_handler.check_and_process_evolution(target_pokemon, item)
                
                if evolution_event:
                    events.append(create_item_used_event())
                    events.append(evolution_event)
                else:
                    events.append(BattleMessageEvent(message=f"{item.name} 对 {target_pokemon.nickname} 没有效果。"))
            except Exception as e:
                logger.error(f"使用进化道具 {item.name} 时发生错误: {e}", exc_info=True)
                events.append(BattleMessageEvent(message=f"使用 {item.name} 时发生错误。"))

        elif item_effect_type == ItemEffectType.CAPTURE.value:
            if not target_pokemon:
                logger.warning(f"道具 {item.name} (CAPTURE) 需要目标宝可梦。")
                events.append(BattleMessageEvent(message=f"使用 {item.name} 需要选择一个宝可梦作为目标。"))
                return events
            
            if target_pokemon.trainer_id is not None and target_pokemon.trainer_id != 0:
                logger.warning(f"不能捕获训练家的宝可梦 {target_pokemon.name}。")
                events.append(BattleMessageEvent(message=f"不能捕获训练家的宝可梦。"))
                return events
            
            if battle.battle_type != "wild":
                logger.warning(f"只能在野生战斗中使用捕获道具 {item.name}。")
                events.append(BattleMessageEvent(message=f"只能在野生战斗中使用 {item.name}。"))
                return events
            
            events.append(create_item_used_event())

            capture_rate_modifier = 1.0
            if item.use_effect:
                try:
                    capture_rate_modifier = float(item.use_effect)
                except ValueError:
                    logger.warning(f"道具 {item.name} 的 use_effect 值 '{item.use_effect}' 无法解析为捕获率修正值，使用默认值 1.0。")
            
            base_capture_rate = await self._metadata_repo.get_pokemon_capture_rate(target_pokemon.race_id)
            if base_capture_rate is None:
                base_capture_rate = 45
            
            status_bonus = 1.0
            if target_pokemon.major_status:
                if target_pokemon.major_status in [MajorStatusType.SLEEP, MajorStatusType.FREEZE]:
                    status_bonus = 2.5
                else:
                    status_bonus = 1.5

            A = calculate_catch_rate_value_A(
                max_hp=target_pokemon.stats['hp'],
                current_hp=target_pokemon.current_hp,
                capture_rate=base_capture_rate,
                ball_bonus=capture_rate_modifier,
                status_bonus=status_bonus
            )
            
            shakes = perform_catch_shakes(A)
            
            events.append(CaptureAttemptEvent(
                item_name=item.name,
                target_name=target_pokemon.nickname,
                shakes=shakes,
                message=f"你扔出了一个 {item.name}！"
            ))
            
            if shakes == 4:
                battle.is_capture_successful = True
                events.append(CaptureSuccessEvent(
                    pokemon_name=target_pokemon.nickname,
                    message=f"太棒了！{target_pokemon.nickname} 被成功捕获了！"
                ))
            else:
                messages = [
                    "噢，不对！差一点就抓住了！",
                    "可恶！就差那么一点了！",
                    "唉！它从精灵球里出来了！"
                ]
                events.append(CaptureFailureEvent(
                    pokemon_name=target_pokemon.nickname,
                    message=random.choice(messages)
                ))
        else:
            logger.warning(f"未知的道具效果类型: {item_effect_type} for item {item.name}")
            events.append(BattleMessageEvent(message=f"无法使用 {item.name}。"))

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
    
    async def execute_skill(self, battle: Battle, attacker: Pokemon, defender: Pokemon, skill: Skill) -> Dict[str, Any]:
        """
        执行技能攻击，计算伤害并生成事件。
        
        参数:
            battle: 当前战斗信息
            attacker: 攻击方宝可梦
            defender: 防守方宝可梦
            skill: 使用的技能
            
        返回:
            包含事件和状态效果的字典
        """
        result = {
            "events": [],
            "status_effects": []
        }
        
        # 检查技能是否命中
        accuracy_check = self.calculate_accuracy_check(attacker, defender, skill)
        if not accuracy_check["hit"]:
            # 技能未命中
            result["events"].append(MissEvent(
                attacker_instance_id=attacker.instance_id,
                attacker_name=attacker.nickname,
                defender_instance_id=defender.instance_id,
                defender_name=defender.nickname,
                skill_id=skill.skill_id,
                skill_name=skill.name,
                message=f"{skill.name}没有命中！"
            ))
            return result
        
        # 计算技能伤害
        if skill.category in ["physical", "special"]:
            damage_result = self.calculate_damage(attacker, defender, skill)
            damage = damage_result["damage"]
            is_critical = damage_result["is_critical"]
            type_effectiveness = damage_result["type_effectiveness"]
            
            # 应用伤害
            defender.current_hp = max(0, defender.current_hp - damage)
            if defender.current_hp == 0:
                defender.is_fainted = True
            
            # 添加伤害事件
            result["events"].append(DamageDealtEvent(
                attacker_instance_id=attacker.instance_id,
                attacker_name=attacker.nickname,
                defender_instance_id=defender.instance_id,
                defender_name=defender.nickname,
                skill_id=skill.skill_id,
                skill_name=skill.name,
                damage=damage,
                is_critical=is_critical,
                type_effectiveness=type_effectiveness,
                message=self._get_damage_message(damage, is_critical, type_effectiveness, defender.nickname)
            ))
        
        # 处理状态效果
        if skill.status_effect_chance > 0 and random.random() < skill.status_effect_chance:
            status_effect = self.metadata_repo.get_status_effect_by_id(skill.status_effect_id)
            if status_effect:
                # 检查目标是否已有该状态效果
                has_effect = any(se.status_effect_id == status_effect.status_effect_id 
                                for se in defender.current_status_effects)
                
                if not has_effect:
                    # 创建新的状态效果实例
                    effect_instance = StatusEffect(
                        status_effect_id=status_effect.status_effect_id,
                        name=status_effect.name,
                        effect_type=status_effect.effect_type,
                        duration=status_effect.base_duration,
                        application_message=status_effect.application_message,
                        effect_data=status_effect.effect_data
                    )
                    
                    # 添加到结果中
                    result["status_effects"].append({
                        "target": defender,
                        "effect": effect_instance
                    })
        
        return result

    def _get_damage_message(self, damage: int, is_critical: bool, type_effectiveness: float, defender_name: str) -> str:
        """生成伤害消息。"""
        message = f"对 {defender_name} 造成了 {damage} 点伤害！"
        
        if is_critical:
            message = "会心一击！" + message
        
        if type_effectiveness > 1.0:
            message += "效果拔群！"
        elif type_effectiveness < 1.0 and type_effectiveness > 0:
            message += "效果不太好..."
        elif type_effectiveness == 0:
            message = f"对 {defender_name} 没有效果..."
        
        return message
    
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
