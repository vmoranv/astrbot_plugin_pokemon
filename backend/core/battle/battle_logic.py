# backend/core/battle/battle_logic.py

import math
import random
from typing import List, Dict, Any, Tuple, Optional, Callable
# Assuming Pokemon and Battle models are defined
from backend.models.pokemon import Pokemon
from backend.models.battle import Battle
# Assuming Skill model is defined
from backend.models.skill import Skill, SecondaryEffect # Import SecondaryEffect
# Assuming Attribute and StatusEffect models are defined
from backend.models.attribute import Attribute
from backend.models.status_effect import StatusEffect # Import StatusEffect model
from backend.models.ability import Ability # Import Ability model
from backend.models.item import Item # Import Item model
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
    ConfusionDamageEvent # Import ConfusionDamageEvent
)
# Import the new StatusEffectHandler
from backend.core.battle.status_effect_handler import StatusEffectHandler # Import StatusEffectHandler

from backend.utils.logger import get_logger
# Assuming custom exceptions for battle are defined in utils/exceptions.py
from backend.utils.exceptions import (
    InvalidBattleActionException, BattleFinishedException,
    PokemonNotFoundException, PlayerNotFoundException
)

logger = get_logger(__name__)

# Define the type hint for event listeners
EventListener = Callable[[Battle, BattleEvent], None]

class BattleLogic:
    """
    Handles the core logic of a Pokemon battle.
    This class is responsible for processing turns, executing actions,
    calculating outcomes, and managing battle state.
    It should be purely logic-based and not interact directly with the database
    or external systems.
    """
    def __init__(self, metadata_repo: MetadataRepository):
        """
        Initializes the BattleLogic with necessary dependencies.
        """
        self._metadata_repo = metadata_repo
        # Event system: maps event types to lists of listener functions
        self._event_listeners: Dict[str, List[EventListener]] = {}

        # Subscribe core battle logic handlers to events
        self.subscribe("stat_stage_change", self._handle_stat_stage_change_event)
        self.subscribe("damage_dealt", self._handle_damage_dealt_event)
        self.subscribe("faint", self._handle_faint_event)
        self.subscribe("status_effect_applied", self._handle_status_effect_applied_event)
        self.subscribe("status_effect_removed", self._handle_status_effect_removed_event)
        self.subscribe("heal", self._handle_heal_event)
        self.subscribe("ability_trigger", self._handle_ability_trigger_event) # Subscribe new handler
        self.subscribe("field_effect", self._handle_field_effect_event) # Subscribe new handler
        self.subscribe("volatile_status_change", self._handle_volatile_status_change_event) # Subscribe new handler
        self.subscribe("forced_switch", self._handle_forced_switch_event) # Subscribe new handler
        self.subscribe("item_trigger", self._handle_item_trigger_event) # Subscribe new handler
        self.subscribe("ability_change", self._handle_ability_change_event) # Subscribe new handler
        self.subscribe("confusion_damage", self._handle_confusion_damage_event) # Register handler for ConfusionDamageEvent
        # TODO: Subscribe handlers for other events as they are implemented (S122 refinement)

        # Initialize the StatusEffectHandler
        self._status_effect_handler = StatusEffectHandler(metadata_repo) # Initialize StatusEffectHandler

        logger.info("BattleLogic initialized with event subscriptions.")

    def subscribe(self, event_type: str, listener: EventListener):
        """Subscribes a listener function to an event type."""
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(listener)
        logger.debug(f"Subscribed listener to event type: {event_type}")

    def publish(self, battle: Battle, event: BattleEvent):
        """Publishes an event to all subscribed listeners."""
        logger.debug(f"Publishing event: {event.event_type}")
        if event.event_type in self._event_listeners:
            for listener in self._event_listeners[event.event_type]:
                try:
                    # Pass the battle object and the event to the listener
                    listener(battle, event)
                except Exception as e:
                    logger.error(f"Error in event listener for '{event.event_type}': {e}", exc_info=True)

    def _handle_stat_stage_change_event(self, battle: Battle, event: StatStageChangeEvent):
        """Handler for StatStageChangeEvent."""
        # Apply the stat stage change to the pokemon model
        # Note: This modifies the pokemon object in place within the battle state
        pokemon = event.pokemon
        stat_type = event.stat_type
        stages_changed = event.stages_changed

        # Ensure stat stage is within bounds [-6, 6]
        current_stage = pokemon.stat_stages.get(stat_type, 0)
        new_stage = max(-6, min(6, current_stage + stages_changed))
        pokemon.stat_stages[stat_type] = new_stage
        event.new_stage = new_stage # Update event with actual new stage

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled StatStageChangeEvent for {event.pokemon.nickname}: {event.message}")

    def _handle_damage_dealt_event(self, battle: Battle, event: DamageDealtEvent):
        """Handler for DamageDealtEvent."""
        # Apply damage to the target pokemon
        # Note: This modifies the pokemon object in place within the battle state
        defender = event.defender
        damage = event.damage
        defender.current_hp = max(0, defender.current_hp - damage)

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled DamageDealtEvent: {event.message}")

    def _handle_faint_event(self, battle: Battle, event: FaintEvent):
        """Handler for FaintEvent."""
        # Mark the pokemon as fainted
        # Note: This modifies the pokemon object in place within the battle state
        fainted_pokemon = event.fainted_pokemon
        fainted_pokemon.current_hp = 0 # Ensure HP is 0
        # TODO: Add a 'is_fainted' flag or similar to Pokemon model if needed (S123 refinement)

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled FaintEvent: {event.message}")

    def _handle_status_effect_applied_event(self, battle: Battle, event: StatusEffectAppliedEvent):
        """Handler for StatusEffectAppliedEvent."""
        # Apply the status effect to the pokemon
        # Note: This modifies the pokemon object in place within the battle state
        pokemon = event.pokemon
        status_effect = event.status_effect
        # TODO: Implement logic to handle unique status effects (e.g., only one major status) (S124 refinement)
        pokemon.status_effects.append(status_effect)

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled StatusEffectAppliedEvent for {event.pokemon.nickname}: {event.message}")

    def _handle_status_effect_removed_event(self, battle: Battle, event: StatusEffectRemovedEvent):
        """Handler for StatusEffectRemovedEvent."""
        # Remove the status effect from the pokemon
        # Note: This modifies the pokemon object in place within the battle state
        pokemon = event.pokemon
        status_id_to_remove = event.status_id

        # Find and remove the status effect
        pokemon.status_effects = [
            se for se in pokemon.status_effects if se.status_id != status_id_to_remove
        ]

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled StatusEffectRemovedEvent for {event.pokemon.nickname}: {event.message}")

    def _handle_heal_event(self, battle: Battle, event: HealEvent):
        """Handler for HealEvent."""
        # Apply healing to the pokemon
        # Note: This modifies the pokemon object in place within the battle state
        pokemon = event.pokemon
        heal_amount = event.heal_amount
        pokemon.current_hp = min(pokemon.max_hp, pokemon.current_hp + heal_amount)

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled HealEvent for {event.pokemon.nickname}: {event.message}")

    def _handle_ability_trigger_event(self, battle: Battle, event: AbilityTriggerEvent):
        """Handler for AbilityTriggerEvent."""
        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled AbilityTriggerEvent for {event.pokemon.nickname}: {event.message}")
        # TODO: Implement logic for specific ability effects if needed (S125 refinement)

    def _handle_field_effect_event(self, battle: Battle, event: FieldEffectEvent):
        """Handler for FieldEffectEvent."""
        # Apply field effect to battle state
        # Note: This modifies the battle object in place
        battle.field_state[event.effect_type] = event.effect_details
        # TODO: Implement logic for specific field effects (weather, terrain) (S126 refinement)

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled FieldEffectEvent: {event.message}")

    def _handle_volatile_status_change_event(self, battle: Battle, event: VolatileStatusChangeEvent):
        """Handler for VolatileStatusChangeEvent."""
        # Apply volatile status to pokemon
        # Note: This modifies the pokemon object in place within the battle state
        pokemon = event.pokemon
        volatile_status_key = event.volatile_status_key
        is_applied = event.is_applied

        if is_applied:
            # TODO: Implement logic for specific volatile statuses (confusion, flinch, etc.) (S127 refinement)
            if volatile_status_key not in pokemon.volatile_status:
                pokemon.volatile_status[volatile_status_key] = event.details.get("duration", -1) # Store duration, -1 for indefinite
        else:
            pokemon.volatile_status.pop(volatile_status_key, None)

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled VolatileStatusChangeEvent for {event.pokemon.nickname}: {event.message}")

    def _handle_forced_switch_event(self, battle: Battle, event: ForcedSwitchEvent):
        """Handler for ForcedSwitchEvent."""
        # TODO: Implement logic for forced switches (e.g., Roar, Whirlwind) (S128 refinement)
        # This will likely involve updating the active pokemon in the battle state
        # and potentially triggering switch-in abilities/effects.

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled ForcedSwitchEvent for {event.pokemon.nickname}: {event.message}")

    def _handle_item_trigger_event(self, battle: Battle, event: ItemTriggerEvent):
        """Handler for ItemTriggerEvent."""
        # TODO: Implement logic for item effects (S129 refinement)
        # This could involve healing, status removal, etc.

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled ItemTriggerEvent for {event.pokemon.nickname}: {event.message}")

    def _handle_ability_change_event(self, battle: Battle, event: AbilityChangeEvent):
        """Handler for AbilityChangeEvent."""
        # TODO: Implement logic for ability changes (e.g., Gastro Acid, Simple Beam) (S130 refinement)
        # This will involve updating the pokemon's active ability.

        # Add message to battle state
        battle.current_turn_messages.append(event.message)
        logger.debug(f"Handled AbilityChangeEvent for {event.pokemon.nickname}: {event.message}")

    def _handle_confusion_damage_event(self, battle: Battle, event: ConfusionDamageEvent) -> List[BattleEvent]:
        """Handles the ConfusionDamageEvent, calculates and applies damage."""
        events: List[BattleEvent] = []
        pokemon = event.pokemon
        base_power = event.base_power

        logger.debug(f"Handling ConfusionDamageEvent for {pokemon.nickname}")

        # Calculate confusion damage
        # Confusion damage is a typeless physical attack with base power 40.
        # It uses the attacker's (the confused Pokemon's) Attack and Defense stats.
        # Critical hits are possible. Abilities and items can affect it.
        # We need to call the central calculate_damage function.
        # Assuming calculate_damage signature: calculate_damage(battle: Battle, attacker: Pokemon, defender: Pokemon, base_power: int, attack_category: str, attack_type: Optional[Attribute], is_critical: bool) -> int:
        # We need to get the 'physical' category and potentially the 'Normal' attribute for typeless.
        # Let's assume 'physical' is a string and None type means typeless for calculate_damage.
        # Critical hit chance for confusion self-damage is usually the standard critical hit chance.
        # Let's roll for critical hit here before calling calculate_damage.
        is_critical = random.random() < 0.0625 # TODO: Make base critical hit chance configurable (S104 refinement)
        # TODO: Consider abilities/items that affect critical hit chance for confusion self-damage (if any exist) (S104 refinement)

        # Call the damage calculation function
        # Need to pass the battle object for full context (abilities, items, field effects)
        # Need to pass the attacker as both attacker and defender
        # Need to pass base_power, attack_category='physical', attack_type=None (typeless)
        # Need to pass is_critical
        # Assuming calculate_damage is async
        # This handler needs to be async if calculate_damage is async.
        # Let's make event handlers async if they might call async functions.
        # This requires changing the publish mechanism to handle async handlers.
        # For now, let's assume calculate_damage is synchronous or we handle async differently.
        # Let's assume calculate_damage is synchronous for this step.

        # Need to get the 'physical' category. Let's assume a string 'physical'.
        attack_category = 'physical' # TODO: Use a proper enum or constant for attack categories (S108 refinement)
        attack_type = None # Typeless damage

        # Call calculate_damage
        # Assuming calculate_damage(battle: Battle, attacker: Pokemon, defender: Pokemon, base_power: int, attack_category: str, attack_type: Optional[Attribute], is_critical: bool) -> int:
        damage = calculate_damage(battle, pokemon, pokemon, base_power, attack_category, attack_type, is_critical)

        logger.debug(f"Calculated confusion damage: {damage}")

        # Publish DamageDealtEvent to apply the damage and check for faint
        # The DamageDealtEvent handler will apply the damage and check for faint.
        message = f"{pokemon.nickname} 对自己造成了 {damage} 点伤害！" # TODO: Refine message (S131 refinement)
        if is_critical:
             message += " 这是击中要害！" # Add critical hit message

        events.append(DamageDealtEvent(
            attacker=pokemon, # Attacker is the confused Pokemon
            defender=pokemon, # Defender is the confused Pokemon
            skill=None, # No skill used
            damage=damage,
            is_critical=is_critical,
            is_effective=False, # Confusion self-damage is not affected by type effectiveness
            is_not_effective=False,
            is_immune=False,
            message=message
        ))
        # No need to publish here, the main publish loop will process the events returned by the handler.

        return events

    # TODO: Implement a method to determine turn order based on speed and priority (S41 refinement)
    # This method will use the speed order calculation formula (Q2)
    # def determine_turn_order(self, battle: Battle, player_action: Dict[str, Any], opponent_action: Dict[str, Any]) -> List[Tuple[Pokemon, Dict[str, Any]]]:
    #     """Determines the order of actions for the turn."""
    #     # Use the formula: speed * 0.3 + priority * 0.7
    #     # If values are equal, compare priority. If priorities are equal, randomize.
    #     pass # Implementation needed

    # TODO: Implement a method to process a full turn (S41 refinement)
    # This method will call execute_action for each pokemon in the determined order
    # def process_turn(self, battle: Battle, player_action: Dict[str, Any], opponent_action: Dict[str, Any]) -> List[BattleEvent]:
    #     """Processes a single turn of the battle."""
    #     events: List[BattleEvent] = []
    #     # Determine turn order
    #     # Execute actions in order
    #     # Apply end-of-turn effects
    #     # Check for battle end
    #     return events # Return list of events generated during the turn

    # TODO: Refactor _execute_action to be more specific (e.g., execute_skill, execute_item, execute_switch, execute_run) (S105 refinement)
    # async def _execute_action(self, battle: Battle, attacker: Pokemon, defender: Pokemon, action: Dict[str, Any], is_player_action: bool) -> Tuple[bool, Optional[str]]:
    #     """Executes a single action (skill, item, switch, or run) in the battle."""
    #     action_type = action.get('type')
    #     events: List[BattleEvent] = [] # Collect events generated by this action
    #     battle_ended = False
    #     outcome = None

    #     if action_type == 'skill':
    #         # Call execute_skill and collect events
    #         skill_events = self.execute_skill(battle, attacker, defender, action)
    #         events.extend(skill_events)
    #         # After executing skill, check for fainting and battle end
    #         # This check might need to be moved to process_turn or a post-action handler
    #         if defender.is_fainted():
    #              self.publish(battle, FaintEvent(fainted_pokemon=defender, message=f"{defender.nickname} 失去了战斗能力！"))
    #              # TODO: Check for battle end after fainting (S131 refinement)
    #              # battle_ended, outcome = await self._check_battle_end(battle) # This is async, needs refactoring

    #     elif action_type == 'item':
    #         # Call execute_item and collect events
    #         # item_events = self.execute_item(battle, attacker, action) # Assuming execute_item exists
    #         pass # TODO: Implement item action execution (S116 refinement)

    #     elif action_type == 'switch':
    #         # Call execute_switch and collect events
    #         # switch_events = self.execute_switch(battle, attacker.owner_id, attacker, action.get('next_pokemon_instance_id')) # Assuming execute_switch exists
    #         pass # TODO: Implement switch action execution (S117 refinement)

    #     elif action_type == 'run':
    #         # Call execute_run and collect events
    #         # run_events = self.execute_run(battle, attacker.owner_id) # Assuming execute_run exists
    #         pass # TODO: Implement run action execution (S118 refinement)

    #     else:
    #         raise InvalidBattleActionException(f"Unknown action type: {action_type}")

    #     # Publish all events generated by this action
    #     # for event in events:
    #     #     self.publish(battle, event)

    #     # The return value of _execute_action might need to change to reflect events and battle state changes
    #     # For now, keeping the old signature but the logic needs to be updated.
    #     return battle_ended, outcome # This return is likely obsolete with event system

    def execute_skill(self, battle: Battle, attacker: Pokemon, target: Pokemon, skill: Skill) -> List[BattleEvent]:
        """
        Executes a skill action.
        Handles skill failure, accuracy, critical hits, damage calculation,
        secondary effects, and event generation.
        Modifies the battle and pokemon states in place.
        """
        events: List[BattleEvent] = []
        logger.info(f"{attacker.nickname} 使用了 {skill.name}！")

        # Publish SkillUsedEvent
        events.append(SkillUsedEvent(attacker=attacker, skill=skill, message=f"{attacker.nickname} 使用了 {skill.name}！"))
        self.publish(battle, events[-1]) # Publish immediately for real-time feedback

        # TODO: Check for move failure conditions (e.g., status effects like sleep/paralysis, abilities) (S106 refinement)
        # If move fails, publish a message event and return
        # Example: Check for paralysis
        # if attacker.has_status_effect("paralysis") and random.random() < 0.25: # Assuming paralysis has 25% chance of full paralysis
        #     message = f"{attacker.nickname} 麻痹了，无法行动！"
        #     events.append(BattleMessageEvent(message=message))
        #     self.publish(battle, events[-1])
        #     return events # Skill failed

        # Check accuracy
        # TODO: Implement accuracy check logic using formulas.check_accuracy (S73 refinement)
        # hit = check_accuracy(attacker, target, skill, battle.field_state) # Assuming check_accuracy exists and takes field state
        hit = True # For MVP, assume moves always hit

        if not hit:
            logger.info(f"{attacker.nickname} 的攻击没有命中！")
            message = f"{attacker.nickname} 的攻击没有命中！"
            events.append(MoveMissedEvent(attacker=attacker, defender=target, skill=skill, message=message))
            self.publish(battle, events[-1])
            return events # Skill missed

        # TODO: Handle different skill categories (Physical, Special, Status) (S107 refinement)
        # The logic below is primarily for damaging moves.

        if skill.category in ["physical", "special"]:
            # It's a damaging move

            # Check for critical hit
            # TODO: Implement critical hit check using formulas.check_critical_hit (S109 refinement)
            # is_critical = check_critical_hit(attacker, skill.critical_hit_ratio) # Assuming check_critical_hit exists
            is_critical = False # Placeholder

            # Calculate type effectiveness
            # TODO: Implement type effectiveness calculation using formulas.calculate_type_effectiveness (S110 refinement)
            # effectiveness = calculate_type_effectiveness(skill.skill_type, target.types, battle.field_state) # Assuming calculate_type_effectiveness exists and takes field state
            effectiveness = 1.0 # Placeholder
            is_effective = effectiveness > 1.0
            is_not_effective = effectiveness < 1.0
            is_immune = effectiveness == 0.0

            if is_immune:
                message = f"{target.nickname} 不受 {skill.name} 的影响！"
                events.append(BattleMessageEvent(message=message))
                self.publish(battle, events[-1])
                return events # Skill had no effect

            # Calculate damage
            # TODO: Implement actual damage calculation using formulas.calculate_damage (S108 refinement)
            # damage = calculate_damage(attacker, target, skill, effectiveness, is_critical, battle.field_state) # Assuming calculate_damage exists and takes field state
            damage = skill.power if skill.power is not None else 0 # Simplified damage calculation for now

            # Apply damage to the target
            # Note: Damage application is handled by the DamageDealtEvent handler (_handle_damage_dealt_event)
            message = f"{attacker.nickname} 对 {target.nickname} 造成了 {damage} 点伤害！"
            # TODO: Refine damage message based on critical hit and effectiveness (S111 refinement)
            if is_critical:
                message += " 这是击中要害！"
            if is_effective:
                message += " 效果绝佳！"
            elif is_not_effective:
                message += " 效果不理想..."

            events.append(DamageDealtEvent(
                attacker=attacker,
                defender=target,
                skill=skill,
                damage=damage,
                is_critical=is_critical,
                is_effective=is_effective,
                is_not_effective=is_not_effective,
                is_immune=is_immune,
                message=message
            ))
            self.publish(battle, events[-1])

            # Check for fainting after damage is applied (handled by event handler)
            # The FaintEvent will be published by _handle_damage_dealt_event if HP drops to 0 or below.

            # Handle secondary effects (S113 refinement)
            # Iterate through skill.secondary_effects and apply them with their chance
            for effect in skill.secondary_effects:
                if random.random() < effect.chance:
                    if effect.effect_type == "stat_change":
                        stat_type = effect.details.get("stat")
                        stages = effect.details.get("stages")
                        effect_target_str = effect.details.get("target", "target") # Default to skill target

                        effect_target = target if effect_target_str == "target" else attacker

                        if stat_type and stages:
                            # Note: Stat stage change is handled by the StatStageChangeEvent handler
                            # message = f"{effect_target.nickname} 的 {stat_type} { '提升' if stages > 0 else '下降' }了 {abs(stages)} 级！" # TODO: Refine stat change message (S134 refinement)
                            # events.append(StatStageChangeEvent(pokemon=effect_target, stat_type=stat_type, stages_changed=stages, new_stage=effect_target.stat_stages.get(stat_type, 0), message=message))
                            # self.publish(battle, events[-1])
                            # Use StatusEffectHandler to apply stat stage changes
                            stat_change_events = self._status_effect_handler.apply_stat_stage_change(effect_target, stat_type, stages)
                            events.extend(stat_change_events)
                            for event in stat_change_events:
                                self.publish(battle, event)

                    elif effect.effect_type == "status":
                        status_id = effect.details.get("status_id")
                        effect_target_str = effect.details.get("target", "target") # Default to skill target
                        effect_target = target if effect_target_str == "target" else attacker

                        status_effect = self._metadata_repo.get_status_effect(status_id)
                        if status_effect:
                            # TODO: Check if target already has a major status effect (S124 refinement)
                            # This check should ideally be within StatusEffectHandler.apply_status_effect
                            # For now, we'll rely on the handler to prevent applying multiple major statuses.

                            # Check if target is immune to this status based on type (S132 refinement)
                            is_immune_by_type = False
                            if status_effect.logic_key == 'poison' or status_effect.logic_key == 'toxic':
                                # Poison and Steel types are immune to poison
                                if any(t.name in ['Poison', 'Steel'] for t in effect_target.types):
                                    is_immune_by_type = True
                                    message = f"{effect_target.nickname} 不会中毒！" # TODO: Refine immunity message
                                    events.append(BattleMessageEvent(message=message))
                                    self.publish(battle, events[-1])
                            elif status_effect.logic_key == 'paralysis':
                                # Electric types are immune to paralysis
                                if any(t.name == 'Electric' for t in effect_target.types):
                                    is_immune_by_type = True
                                    message = f"{effect_target.nickname} 不会麻痹！" # TODO: Refine immunity message
                                    events.append(BattleMessageEvent(message=message))
                                    self.publish(battle, events[-1])
                            # TODO: Add checks for other type-based immunities (e.g., Fire to Burn, Ice to Freeze, Grass to Sleep Powder/Spore) (S132 refinement)

                            if not is_immune_by_type:
                                # message = f"{effect_target.nickname} {status_effect.name}了！" # TODO: Refine status message (S133 refinement)
                                # events.append(StatusEffectAppliedEvent(pokemon=effect_target, status_effect=status_effect, message=message))
                                # self.publish(battle, events[-1])
                                # Use StatusEffectHandler to apply status effects
                                status_events = self._status_effect_handler.apply_status_effect(effect_target, status_effect)
                                events.extend(status_events)
                                for event in status_events:
                                    self.publish(battle, event)
                            else:
                                logger.debug(f"Pokemon {effect_target.nickname} is immune to {status_effect.name} due to type.")


                    # TODO: Handle other secondary effects (e.g., flinch, recoil, drain, etc.) (S121 refinement)
                    # Add elif blocks for other effect_type values

                    else:
                        logger.warning(f"Unknown secondary effect type: {effect.effect_type}")


        elif skill.category == "status":
            # TODO: Implement logic for status moves (S114 refinement)
            # This will involve applying status effects, stat changes, field effects, etc.
            # based on skill.effect_logic_key or secondary_effects.
            # For now, let's process secondary effects for status moves as well.
            for effect in skill.secondary_effects:
                 if random.random() < effect.chance:
                    if effect.effect_type == "stat_change":
                        stat_type = effect.details.get("stat")
                        stages = effect.details.get("stages")
                        effect_target_str = effect.details.get("target", "target") # Default to skill target

                        effect_target = target if effect_target_str == "target" else attacker

                        if stat_type and stages:
                            stat_change_events = self._status_effect_handler.apply_stat_stage_change(effect_target, stat_type, stages)
                            events.extend(stat_change_events)
                            for event in stat_change_events:
                                self.publish(battle, event)

                    elif effect.effect_type == "status":
                        status_id = effect.details.get("status_id")
                        effect_target_str = effect.details.get("target", "target") # Default to skill target
                        effect_target = target if effect_target_str == "target" else attacker

                        status_effect = self._metadata_repo.get_status_effect(status_id)
                        if status_effect:
                             # Check if target is immune to this status based on type (S132 refinement)
                            is_immune_by_type = False
                            if status_effect.logic_key == 'poison' or status_effect.logic_key == 'toxic':
                                if any(t.name in ['Poison', 'Steel'] for t in effect_target.types):
                                    is_immune_by_type = True
                                    message = f"{effect_target.nickname} 不会中毒！" # TODO: Refine immunity message
                                    events.append(BattleMessageEvent(message=message))
                                    self.publish(battle, events[-1])
                            elif status_effect.logic_key == 'paralysis':
                                if any(t.name == 'Electric' for t in effect_target.types):
                                    is_immune_by_type = True
                                    message = f"{effect_target.nickname} 不会麻痹！" # TODO: Refine immunity message
                                    events.append(BattleMessageEvent(message=message))
                                    self.publish(battle, events[-1])
                            # TODO: Add checks for other type-based immunities (S132 refinement)

                            if not is_immune_by_type:
                                status_events = self._status_effect_handler.apply_status_effect(effect_target, status_effect)
                                events.extend(status_events)
                                for event in status_events:
                                    self.publish(battle, event)
                            else:
                                logger.debug(f"Pokemon {effect_target.nickname} is immune to {status_effect.name} due to type.")

                    # TODO: Handle other secondary effects for status moves (S121 refinement)
                    else:
                        logger.warning(f"Unknown secondary effect type for status move: {effect.effect_type}")

            # TODO: Implement main effect logic for status moves based on skill.effect_logic_key (S114 refinement)
            # This will be separate from secondary effects and might involve calling other handlers
            pass # Implementation needed

        # TODO: Handle abilities/items that trigger after a skill is used (S122, S123 refinement)
        # This might involve checking attacker's and target's abilities/items

        return events

    # TODO: Implement a method to execute item action (S116 refinement)
    # def execute_item(self, battle: Battle, user: Pokemon, item: Item) -> List[BattleEvent]:
    #     """Executes an item action."""
    #     events: List[BattleEvent] = []
    #     # Logic for item effects (healing, status removal, etc.)
    #     # Generate ItemUsedEvent and other relevant events
    #     pass # Implementation needed

    # TODO: Implement a method to execute switch action (S117 refinement)
    # def execute_switch(self, battle: Battle, player: Player, current_pokemon: Pokemon, next_pokemon: Pokemon) -> List[BattleEvent]:
    #     """Executes a pokemon switch action."""
    #     events: List[BattleEvent] = []
    #     # Logic for switching pokemon
    #     # Generate SwitchOutEvent and SwitchInEvent
    #     pass # Implementation needed

    # TODO: Implement a method to execute run action (S118 refinement)
    async def _execute_run_action(self, battle: Battle, player_pokemon: Pokemon) -> Tuple[List[BattleEvent], bool]:
        """
        Executes a run action attempt.

        Args:
            battle: The current Battle object.
            player_pokemon: The player's active Pokemon attempting to run.

        Returns:
            A tuple containing:
                - A list of BattleEvent objects generated by the attempt.
                - A boolean indicating if the run was successful.
        """
        events: List[BattleEvent] = []
        run_successful = False
        logger.debug(f"{player_pokemon.nickname} 尝试逃跑！")
        events.append(RunAttemptEvent(pokemon=player_pokemon, success=False, message=f"{player_pokemon.nickname} 尝试逃跑！")) # Initial message (S1 refinement)

        # S118: Implement run success check
        # TODO: Implement run success check using formulas.check_run_success (S118 refinement)
        # This involves player's pokemon speed, opponent's pokemon speed, and number of run attempts.
        # For now, a simplified check.
        # run_successful = check_run_success(player_pokemon, battle.opponent_pokemon, battle.run_attempts) # Assuming check_run_success exists
        # Simplified run check: 50% chance + 10% for each failed attempt
        run_chance = 0.5 + (battle.run_attempts * 0.1) # TODO: Make run chance formula configurable (S118 refinement)
        if random.random() < run_chance:
             run_successful = True
             events[-1].success = True # Update the event
             events[-1].details['success'] = True
             events[-1].details['message'] = f"{player_pokemon.nickname} 成功逃跑了！" # TODO: Refine message (S1 refinement)
             logger.info(f"{player_pokemon.nickname} successfully ran away.")
        else:
             battle.run_attempts += 1
             events[-1].details['message'] = f"{player_pokemon.nickname} 逃跑失败了！" # TODO: Refine message (S1 refinement)
             logger.debug(f"{player_pokemon.nickname} failed to run away.")


        return events, run_successful

    # TODO: Implement a method to execute catch action (S115 refinement)
    async def _execute_catch_action(self, battle: Battle, player_pokemon: Pokemon, item: Item) -> Tuple[List[BattleEvent], bool]:
        """
        Executes a catch action attempt.

        Args:
            battle: The current Battle object.
            player_pokemon: The player's active Pokemon (used for context, though catch is on opponent).
            item: The item used for catching (e.g., Poke Ball).

        Returns:
            A tuple containing:
                - A list of BattleEvent objects generated by the attempt.
                - A boolean indicating if the catch was successful.
        """
        events: List[BattleEvent] = []
        catch_success = False
        logger.debug(f"{player_pokemon.nickname} 使用了 {item.name} 尝试捕捉 {battle.opponent_pokemon.nickname}！")
        events.append(CatchAttemptEvent(pokemon=battle.opponent_pokemon, item=item, success=False, message=f"{player_pokemon.nickname} 使用了 {item.name} 尝试捕捉 {battle.opponent_pokemon.nickname}！")) # Initial message (S1 refinement)

        # S115: Implement catch rate calculation and shakes
        # TODO: Implement catch rate calculation using formulas.calculate_catch_rate_value_A (S115 refinement)
        # This involves wild pokemon's race catch rate, current HP, status effects, and the used item.
        # For now, a simplified calculation.
        # value_a = calculate_catch_rate_value_A(battle.opponent_pokemon, item, battle.field_state) # Assuming calculate_catch_rate_value_A exists
        # Simplified value_a calculation (example: based on remaining HP and item)
        max_hp = battle.opponent_pokemon.max_hp
        current_hp = battle.opponent_pokemon.current_hp
        catch_rate = self._metadata_repo.get_race(battle.opponent_pokemon.race_id).catch_rate # Get base catch rate from metadata
        # Simplified A = ( (3 * MaxHP - 2 * CurrentHP) * CatchRate * ItemModifier ) / (3 * MaxHP)
        # ItemModifier depends on the item (e.g., Poke Ball = 1, Great Ball = 1.5, Ultra Ball = 2)
        # TODO: Get item catch rate modifier from metadata (S115 refinement)
        item_modifier = 1.0 # Placeholder
        if item.name == "Great Ball": # Example check
             item_modifier = 1.5
        elif item.name == "Ultra Ball": # Example check
             item_modifier = 2.0

        # Avoid division by zero
        if max_hp == 0:
             max_hp = 1

        value_a = int(((3 * max_hp - 2 * current_hp) * catch_rate * item_modifier) / (3 * max_hp))
        logger.debug(f"Catch rate value A: {value_a}")

        # If A is 255 or more, the catch is guaranteed (unless there are other factors like abilities)
        if value_a >= 255:
             shakes = 4 # 4 shakes means caught
             logger.debug("Value A >= 255, guaranteed catch (basic check).")
        else:
             # TODO: Implement shake check using formulas.perform_catch_shakes (S115 refinement)
             # This involves calculating value B and performing up to 4 random checks.
             # For now, a simplified shake check based on value_a.
             # shakes = perform_catch_shakes(value_a, battle.opponent_pokemon.status_effect) # Assuming perform_catch_shakes exists
             # Simplified shake check: number of shakes based on A (more shakes for higher A)
             # This is NOT the official shake formula, just a placeholder.
             shakes = 0
             if value_a > 0:
                  # Example: 1 shake if A > 30, 2 shakes if A > 70, 3 shakes if A > 150, 4 shakes if A > 200
                  if value_a > 30: shakes = 1
                  if value_a > 70: shakes = 2
                  if value_a > 150: shakes = 3
                  if value_a > 200: shakes = 4 # This is just an example logic

             # TODO: Incorporate status effect modifier (sleep/freeze increase catch rate) (S115 refinement)
             if battle.opponent_pokemon.status_effect:
                  if battle.opponent_pokemon.status_effect.logic_key in ['sleep', 'freeze']:
                       # Increase shakes or chance based on status (check rules)
                       # Example: Add 1 or 2 shakes
                       shakes += 1 # Simplified

             logger.debug(f"Catch attempt resulted in {shakes} shakes.")


        # S115: Determine catch success based on shakes
        if shakes == 4:
             catch_success = True
             events[-1].success = True # Update the event
             events[-1].details['success'] = True
             events[-1].details['message'] = f"恭喜！{battle.opponent_pokemon.nickname} 被抓住了！" # TODO: Refine message (S1 refinement)
             logger.info(f"{battle.opponent_pokemon.nickname} was caught.")
             # TODO: Add pokemon to player's team/storage (S136 refinement)
             events.extend(self._process_battle_end(battle, "catch")) # End battle on successful catch
        else:
             events[-1].details['message'] = f"{battle.opponent_pokemon.nickname} 从球里逃脱了！" # TODO: Refine message (S1 refinement)
             logger.debug(f"{battle.opponent_pokemon.nickname} escaped.")
             # TODO: Add messages for each shake (S1 refinement)
             # events.append(BattleMessageEvent(message="摇晃了一下..."))
             # events.append(BattleMessageEvent(message="又摇晃了一下..."))
             # ...

        return events, catch_success

    # TODO: Implement get_effective_stat function (S111 refinement)
    # This function is in formulas.py, but keeping the TODO here for tracking its usage.

    def publish(self, battle: Battle, event: BattleEvent):
        """
        Publishes a battle event to all subscribers.
        """
        # TODO: Implement event publishing mechanism (S2 refinement)
        # This could involve calling a callback function provided by the service layer
        # For now, just print the event for debugging
        logger.info(f"Event Published: {event.event_type} - {event.details.get('message', event.details)}")
        # Assuming battle object has a list of subscribers/callbacks
        # for subscriber in battle.subscribers:
        #      subscriber(event)
