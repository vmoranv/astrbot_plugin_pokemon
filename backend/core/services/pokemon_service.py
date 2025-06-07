from typing import Optional, List, Tuple, Dict, Any
from backend.models.pokemon import Pokemon
from backend.models.player import Player
from backend.models.item import Item
from backend.models.race import Race
from backend.models.event import PokemonEvolvedEvent, WildPokemonFledEvent, HealEvent
from backend.data_access.repositories.pokemon_repository import PokemonRepository
from backend.data_access.repositories.metadata_repository import MetadataRepository
from backend.data_access.repositories.player_repository import PlayerRepository
from backend.utils.exceptions import PokemonNotFoundException, RaceNotFoundException, ItemNotFoundException, InsufficientItemException, PlayerNotFoundException, InvalidPartyOrderException, PartyFullException, PokemonNotInCollectionException, PokemonCreationException
from backend.utils.logger import get_logger
from backend.core.pet import pet_catch, pet_grow, pet_skill, pet_system, pet_evolution
from backend.core import pokemon_factory
from backend.core.battle import encounter_logic, formulas
from backend.core.battle import catch_logic
from backend.core.services.item_service import ItemService
from backend.core.services.player_service import PlayerService
from backend.core.pet import pet_equipment
import random
from backend.core.battle.formulas import calculate_catch_rate

logger = get_logger(__name__)

class PokemonService:
    """Service for Pokemon related business logic."""

    def __init__(self, item_service: Optional[ItemService] = None):
        self.pokemon_repo = PokemonRepository()
        self.metadata_repo = MetadataRepository()
        self.player_repo = PlayerRepository()
        self.pokemon_factory = pokemon_factory.PokemonFactory(self.metadata_repo)
        self.item_service = item_service or ItemService()
        self.player_service = PlayerService()
        self.encounter_logic = encounter_logic.EncounterLogic()

    async def get_pokemon_instance(self, pokemon_id: int) -> Pokemon:
        """
        Retrieves a specific pokemon instance. Raises PokemonNotFoundException if not found.
        """
        pokemon = await self.pokemon_repo.get_pokemon_instance_by_id(pokemon_id)
        if pokemon is None:
            raise PokemonNotFoundException(f"Pokemon instance with ID {pokemon_id} not found.")
        return pokemon

    async def get_player_pokemons(self, player_id: str) -> List[Pokemon]:
        """
        检索玩家拥有的所有宝可梦实例。
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        all_pokemon_ids = player.party_pokemon_ids + player.box_pokemon_ids
        pokemons = []
        orphaned_ids = []
        
        for pokemon_id in all_pokemon_ids:
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_id)
            if pokemon:
                pokemons.append(pokemon)
            else:
                logger.warning(f"Pokemon instance {pokemon_id} not found for player {player_id}.")
                orphaned_ids.append(pokemon_id)
        
        # 处理孤立ID
        if orphaned_ids:
            logger.info(f"Found {len(orphaned_ids)} orphaned pokemon IDs for player {player_id}.")
            
            # 从玩家的队伍和盒子列表中移除孤立ID
            party_orphaned = [pid for pid in orphaned_ids if pid in player.party_pokemon_ids]
            box_orphaned = [pid for pid in orphaned_ids if pid in player.box_pokemon_ids]
            
            if party_orphaned:
                player.party_pokemon_ids = [pid for pid in player.party_pokemon_ids if pid not in party_orphaned]
            
            if box_orphaned:
                player.box_pokemon_ids = [pid for pid in player.box_pokemon_ids if pid not in box_orphaned]
            
            # 标记所有孤立ID
            for orphaned_id in orphaned_ids:
                try:
                    await self.pokemon_repo.mark_orphaned_pokemon_id(orphaned_id, player_id)
                    logger.info(f"Marked orphaned pokemon ID {orphaned_id} for player {player_id}")
                except Exception as e:
                    logger.error(f"Error marking orphaned pokemon ID {orphaned_id}: {e}", exc_info=True)
            
            # 保存更新后的玩家数据
            await self.player_repo.save_player(player)
        
        return pokemons

    async def get_player_party_pokemon(self, player_id: str) -> List[Pokemon]:
        """
        检索玩家队伍中的宝可梦实例。
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        party_pokemons = []
        orphaned_ids = []
        
        for pokemon_id in player.party_pokemon_ids:
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_id)
            if pokemon:
                party_pokemons.append(pokemon)
            else:
                logger.warning(f"Pokemon instance {pokemon_id} in party not found for player {player_id}.")
                # 将孤立ID添加到列表中，稍后一次性处理
                orphaned_ids.append(pokemon_id)
        
        # 处理所有孤立ID
        if orphaned_ids:
            logger.info(f"Found {len(orphaned_ids)} orphaned pokemon IDs in player {player_id}'s party.")
            # 从玩家的队伍列表中移除孤立ID
            player.party_pokemon_ids = [pid for pid in player.party_pokemon_ids if pid not in orphaned_ids]
            # 标记这些ID以便后续清理
            for orphaned_id in orphaned_ids:
                try:
                    await self.pokemon_repo.mark_orphaned_pokemon_id(orphaned_id, player_id)
                    logger.info(f"Marked orphaned pokemon ID {orphaned_id} in party for player {player_id}")
                except Exception as e:
                    logger.error(f"Error marking orphaned pokemon ID {orphaned_id}: {e}", exc_info=True)
            
            # 保存更新后的玩家数据
            await self.player_repo.save_player(player)
        
        return party_pokemons

    async def get_player_box_pokemon(self, player_id: str) -> List[Pokemon]:
        """
        Retrieves the pokemon instances in the player's box.
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        box_pokemons = []
        orphaned_ids = []
        
        for pokemon_id in player.box_pokemon_ids:
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_id)
            if pokemon:
                box_pokemons.append(pokemon)
            else:
                logger.warning(f"Pokemon instance {pokemon_id} in box not found for player {player_id}.")
                # 将孤立ID添加到列表中
                orphaned_ids.append(pokemon_id)
        
        # 处理所有孤立ID
        if orphaned_ids:
            logger.info(f"Found {len(orphaned_ids)} orphaned pokemon IDs in player {player_id}'s box.")
            # 从玩家的盒子列表中移除孤立ID
            player.box_pokemon_ids = [pid for pid in player.box_pokemon_ids if pid not in orphaned_ids]
            # 标记这些ID以便后续清理
            for orphaned_id in orphaned_ids:
                try:
                    await self.pokemon_repo.mark_orphaned_pokemon_id(orphaned_id, player_id)
                    logger.info(f"Marked orphaned pokemon ID {orphaned_id} in box for player {player_id}")
                except Exception as e:
                    logger.error(f"Error marking orphaned pokemon ID {orphaned_id}: {e}", exc_info=True)
            
            # 保存更新后的玩家数据
            await self.player_repo.save_player(player)
        
        return box_pokemons

    async def save_pokemon(self, pokemon: Pokemon):
        """Saves a pokemon instance to the repository."""
        await self.pokemon_repo.save_pokemon_instance(pokemon)

    async def create_pokemon_instance(self, race_id: int, level: int = 1, is_wild: bool = False, 
                                     custom_moves: List[int] = None, nickname: str = None,
                                     original_trainer_id: str = None) -> Pokemon:
        """
        创建一个新的宝可梦实例。
        
        Args:
            race_id (int): 宝可梦种族ID
            level (int, optional): 宝可梦等级，默认为1
            is_wild (bool, optional): 是否为野生宝可梦，默认为False
            custom_moves (List[int], optional): 自定义技能ID列表，默认为None
            nickname (str, optional): 宝可梦昵称，默认为None
            original_trainer_id (str, optional): 原始训练师ID，默认为None
            
        Returns:
            Pokemon: 创建的宝可梦实例
        """
        try:
            # 获取宝可梦种族数据
            race_data = await self.metadata_repo.get_pokemon_race(race_id)
            if not race_data:
                raise RaceNotFoundException(f"宝可梦种族ID {race_id} 不存在")
            
            # 创建宝可梦实例
            pokemon_instance = await pokemon_factory.create_pokemon(
                race_data=race_data,
                level=level,
                moves=custom_moves,
                is_wild=is_wild,
                nickname=nickname,
                original_trainer_id=original_trainer_id
            )
            
            # 保存宝可梦实例到数据库
            saved_instance = await self.pokemon_repo.save_pokemon_instance(pokemon_instance)
            
            logger.info(f"创建了新的宝可梦实例：{saved_instance.name}，ID：{saved_instance.instance_id}")
            
            return saved_instance
        
        except RaceNotFoundException as e:
            logger.error(f"创建宝可梦实例失败：{e}")
            raise
        except Exception as e:
            logger.error(f"创建宝可梦实例时发生错误：{e}", exc_info=True)
            raise PokemonCreationException(f"创建宝可梦实例失败：{e}")

    async def check_for_wild_encounter(self, location_id: str) -> bool:
        """
        Checks if a wild pokemon encounter occurs at the given location.
        """
        return await self.encounter_logic.check_encounter(location_id)

    async def get_wild_encounter_details(self, location_id: str) -> Optional[Tuple[int, int]]:
        """
        Gets the details (race_id, level) of a wild pokemon encounter for a location.
        Should only be called if check_for_wild_encounter returned True.
        """
        return await self.encounter_logic.get_wild_pokemon_details(location_id)

    async def attempt_catch_pokemon(self, player: Player, pokemon_instance_id: int, pokeball_item_id: int) -> Tuple[bool, str]:
        """
        Attempts to catch a specific wild pokemon instance using a pokeball.
        Returns a tuple: (success: bool, message: str).
        """
        logger.debug(f"Player {player.player_id} attempting to catch pokemon instance {pokemon_instance_id} with pokeball {pokeball_item_id}")

        # 1. Get pokemon instance details
        pokemon_instance = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
        if not pokemon_instance:
            logger.error(f"Attempted to catch non-existent pokemon instance: {pokemon_instance_id}")
            return (False, "尝试捕获的宝可梦不存在。") # Should not happen if flow is correct

        # 2. Consume the pokeball
        try:
            await self.item_service.remove_item_from_player(player.player_id, pokeball_item_id, quantity=1)
            logger.debug(f"Consumed pokeball {pokeball_item_id} from player {player.player_id}.")
        except InsufficientItemException:
            logger.warning(f"Player {player.player_id} attempted to use pokeball {pokeball_item_id} but does not have enough.")
            # Attempt to get item name for better message, but fallback if not found
            try:
                item_data = await self.item_service.get_item_data(pokeball_item_id)
                item_name = item_data.name
            except ItemNotFoundException:
                item_name = f"ID为 {pokeball_item_id} 的道具"
            return (False, f"你没有足够的 {item_name}。")
        except ItemNotFoundException:
             logger.error(f"Attempted to use non-existent pokeball {pokeball_item_id} by player {player.player_id}.")
             return (False, f"ID为 {pokeball_item_id} 的道具不存在。")
        except Exception as e:
            logger.error(f"Error consuming item {pokeball_item_id} for player {player.player_id}: {e}", exc_info=True)
            return (False, "消耗道具时发生错误。")

        # 3. 执行详细的捕获率计算
        try:
            # 获取宝可梦当前状态
            pokemon_hp_percent = pokemon_instance.current_hp / pokemon_instance.max_hp
            has_status_effect = any(effect.affects_catch_rate for effect in pokemon_instance.status_effects)
            
            # 获取精灵球数据
            pokeball_data = await self.item_service.get_item_data(pokeball_item_id)
            pokeball_modifier = pokeball_data.catch_rate_modifier if hasattr(pokeball_data, 'catch_rate_modifier') else 1.0
            
            # 获取宝可梦种族的基础捕获率
            race_data = await self.metadata_repo.get_race_by_id(pokemon_instance.race_id)
            base_catch_rate = race_data.base_catch_rate if hasattr(race_data, 'base_catch_rate') else 45  # 默认值
            
            # 调用公式计算捕获率
            catch_success_rate = formulas.calculate_catch_rate(
                base_catch_rate=base_catch_rate,
                hp_percent=pokemon_hp_percent,
                pokeball_modifier=pokeball_modifier,
                status_effect_modifier=1.5 if has_status_effect else 1.0,
                level=pokemon_instance.level
            )
            
            logger.debug(f"详细捕获率计算：基础捕获率={base_catch_rate}, HP百分比={pokemon_hp_percent}, "
                        f"球修正={pokeball_modifier}, 状态修正={1.5 if has_status_effect else 1.0}, "
                        f"最终捕获率={catch_success_rate}")
        except Exception as e:
            # 如果详细计算失败，回退到简单计算
            logger.error(f"详细捕获率计算失败，回退到简单计算: {e}", exc_info=True)
            catch_success_rate = catch_logic.calculate_catch_rate(pokemon_instance.level, pokeball_item_id)
        
        if random.random() < catch_success_rate:
            # Catch successful
            logger.info(f"Player {player.player_id} successfully caught pokemon instance {pokemon_instance_id}.")

            # 4. Add pokemon to player's collection (box)
            player.box_pokemon_ids.append(pokemon_instance_id)
            pokemon_instance.is_in_party = False # Ensure it's marked as not in party
            await self.player_repo.save_player(player)
            await self.pokemon_repo.save_pokemon_instance(pokemon_instance)

            # Get pokemon race name for the success message
            try:
                race_data = await self.metadata_repo.get_race_by_id(pokemon_instance.race_id)
                pokemon_name = race_data.name if race_data else f"未知宝可梦 (ID: {pokemon_instance.race_id})"
            except RaceNotFoundException:
                 pokemon_name = f"未知宝可梦 (ID: {pokemon_instance.race_id})"

            return (True, f"恭喜！你成功捕获了野生的 {pokemon_name} (等级 {pokemon_instance.level})！它已被送往你的宝可梦盒子。")
        else:
            # Catch failed
            logger.info(f"Player {player.player_id}'s attempt to catch pokemon instance {pokemon_instance_id} failed.")
            
            # 决定宝可梦是否逃跑
            flee_chance = 0.3  # 基础逃跑概率
            # 考虑宝可梦等级和当前HP影响逃跑概率
            flee_chance += (pokemon_instance.level / 100) * 0.2  # 等级越高逃跑概率越高，最多增加0.2
            flee_chance -= (pokemon_instance.current_hp / pokemon_instance.max_hp) * 0.1  # HP越少逃跑概率越低，最多减少0.1
            
            # 检查宝可梦状态效果对逃跑的影响
            for effect in pokemon_instance.status_effects:
                if hasattr(effect, 'affects_flee_rate'):
                    flee_chance *= effect.affects_flee_rate
            
            # 决定是否逃跑
            pokemon_flees = random.random() < flee_chance
            
            if pokemon_flees:
                # 宝可梦逃跑，需要从战斗中移除
                logger.info(f"Wild pokemon {pokemon_instance_id} fled after failed catch attempt.")
                
                # 通知前端宝可梦逃跑（可能需要通过事件系统）
                # 这里假设有一个事件系统可以发布事件
                wild_pokemon_event = WildPokemonFledEvent(
                    pokemon_instance_id=pokemon_instance_id,
                    message="野生宝可梦逃走了！"
                )
                if hasattr(self, "event_publisher") and self.event_publisher:
                    await self.event_publisher.publish_event(wild_pokemon_event)
                
                # 如果需要，在这里清理相关战斗状态
                
                return (False, "可惜！宝可梦挣脱了精灵球，迅速逃走了！")
            else:
                # 宝可梦没有逃跑，可以继续尝试捕捉
                return (False, "宝可梦挣脱了精灵球！它看起来还想继续战斗。")

    async def move_pokemon_to_box(self, player_id: str, pokemon_instance_id: int) -> Player:
        """
        将宝可梦从玩家的队伍移动到盒子。
        如果宝可梦不在队伍中，则抛出PokemonNotInCollectionException异常。
        返回更新后的Player对象。
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"玩家 {player_id} 不存在。")

        if pokemon_instance_id not in player.party_pokemon_ids:
            raise PokemonNotInCollectionException(f"宝可梦实例 {pokemon_instance_id} 不在玩家 {player_id} 的队伍中。")

        # 从队伍中移除宝可梦
        player.party_pokemon_ids.remove(pokemon_instance_id)
        # 添加到盒子中
        player.box_pokemon_ids.append(pokemon_instance_id)
        
        # 保存更新后的玩家数据
        await self.player_repo.save_player(player)
        
        logger.info(f"将宝可梦 {pokemon_instance_id} 从玩家 {player_id} 的队伍移动到盒子")
        
        return player

    async def move_pokemon_to_party(self, player_id: str, pokemon_instance_id: int) -> Player:
        """
        将宝可梦从玩家的盒子移动到队伍。
        如果宝可梦不在盒子中，则抛出PokemonNotInCollectionException异常。
        如果玩家的队伍已满，则抛出PartyFullException异常。
        返回更新后的Player对象。
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"玩家 {player_id} 不存在。")

        if pokemon_instance_id not in player.box_pokemon_ids:
            raise PokemonNotInCollectionException(f"宝可梦实例 {pokemon_instance_id} 不在玩家 {player_id} 的盒子中。")

        # 检查队伍是否已满
        from backend.config.settings import PARTY_SIZE_LIMIT
        party_limit = PARTY_SIZE_LIMIT  # 从配置中获取队伍上限
        if len(player.party_pokemon_ids) >= party_limit:
            raise PartyFullException(f"玩家 {player_id} 的队伍已满。")

        # 从盒子中移除宝可梦
        player.box_pokemon_ids.remove(pokemon_instance_id)
        # 添加到队伍中
        player.party_pokemon_ids.append(pokemon_instance_id)
        
        # 保存更新后的玩家数据
        await self.player_repo.save_player(player)
        
        logger.info(f"将宝可梦 {pokemon_instance_id} 从玩家 {player_id} 的盒子移动到队伍")
        
        return player

    async def sort_party(self, player_id: str, ordered_pokemon_ids: List[int]) -> str:
        """
        Sorts the player's party according to the provided list of Pokemon instance IDs.

        Args:
            player_id: The ID of the player.
            ordered_pokemon_ids: A list of Pokemon instance IDs representing the desired order.

        Returns:
            A message indicating the result of the operation.

        Raises:
            PlayerNotFoundException: If the player is not found.
            InvalidPartyOrderException: If the provided list does not match the current party.
        """
        player = await self.player_repo.get_player(player_id)
        if not player:
            raise PlayerNotFoundException(f"Player {player_id} not found.")

        # Validate that the provided list contains the same Pokemon instances as the current party
        current_party_ids_set = set(player.party_pokemon_ids)
        ordered_ids_set = set(ordered_pokemon_ids)

        if current_party_ids_set != ordered_ids_set or len(current_party_ids_set) != len(ordered_pokemon_ids):
            raise InvalidPartyOrderException("Provided list of Pokemon IDs does not match the current party.")

        # Update the player's party with the new order
        player.party_pokemon_ids = ordered_pokemon_ids
        await self.player_repo.save_player(player)

        logger.info(f"Player {player_id}'s party sorted to order: {ordered_pokemon_ids}")
        return "队伍排序成功！"

    async def heal_pokemon(self, pokemon_instance_id: int, amount: Optional[int] = None, 
                         full_heal: bool = False, heal_pp: bool = False) -> Tuple[bool, str, Optional[Pokemon]]:
        """
        治疗宝可梦的HP和/或PP。
        
        Args:
            pokemon_instance_id (int): 宝可梦实例ID
            amount (Optional[int]): 治疗的HP数量，如果为None则根据full_heal参数决定
            full_heal (bool): 是否完全恢复，True为恢复全部HP和清除状态
            heal_pp (bool): 是否恢复技能PP
            
        Returns:
            Tuple[bool, str, Optional[Pokemon]]: 包含操作是否成功的布尔值、描述结果的消息和更新后的宝可梦实例
        """
        try:
            # 获取宝可梦实例
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
            if not pokemon:
                raise PokemonNotFoundException(f"宝可梦实例 {pokemon_instance_id} 不存在")
            
            messages = []
            
            # 处理HP恢复
            if full_heal or amount is not None:
                old_hp = pokemon.current_hp
                
                if full_heal:
                    pokemon.current_hp = pokemon.max_hp
                    healed_amount = pokemon.max_hp - old_hp
                else:
                    pokemon.current_hp = min(pokemon.current_hp + amount, pokemon.max_hp)
                    healed_amount = pokemon.current_hp - old_hp
                    
                if healed_amount > 0:
                    messages.append(f"{pokemon.nickname or pokemon.name} 恢复了 {healed_amount} 点HP")
                    
                    # 创建治疗事件
                    heal_event = HealEvent(
                        target_instance_id=pokemon_instance_id,
                        target_name=pokemon.nickname or pokemon.name,
                        amount_healed=healed_amount,
                        current_hp=pokemon.current_hp,
                        max_hp=pokemon.max_hp,
                        source="service",
                        message=f"{pokemon.nickname or pokemon.name} 恢复了 {healed_amount} 点HP"
                    )
                    
                    # 如果有EventPublisher，发布治疗事件
                    if hasattr(self, "event_publisher") and self.event_publisher:
                        await self.event_publisher.publish_event(heal_event)
                
            # 处理状态恢复
            if full_heal and pokemon.status_effects:
                pokemon.status_effects = []
                messages.append(f"{pokemon.nickname or pokemon.name} 的所有状态效果已清除")
                
            # 处理PP恢复
            if heal_pp:
                pp_restored = False
                for skill in pokemon.skills:
                    if skill.current_pp < skill.max_pp:
                        old_pp = skill.current_pp
                        skill.current_pp = skill.max_pp
                        pp_restored = True
                        messages.append(f"{pokemon.nickname or pokemon.name} 的技能 {skill.name} 恢复了 {skill.max_pp - old_pp} 点PP")
                        
                if not pp_restored:
                    messages.append(f"{pokemon.nickname or pokemon.name} 的技能PP已满")
                    
            # 如果没有任何操作执行
            if not messages:
                return False, f"{pokemon.nickname or pokemon.name} 无需恢复", pokemon
            
            # 保存更新后的宝可梦
            await self.pokemon_repo.save_pokemon_instance(pokemon)
            
            result_message = "，".join(messages)
            logger.info(f"宝可梦 {pokemon.name}(ID:{pokemon_instance_id}) 已恢复: {result_message}")
            
            return True, result_message, pokemon
            
        except PokemonNotFoundException as e:
            logger.error(f"治疗宝可梦失败: {e}")
            raise
        except Exception as e:
            logger.error(f"治疗宝可梦时发生错误: {e}", exc_info=True)
            return False, f"治疗时发生错误: {str(e)}", None

    async def clean_orphaned_pokemon_ids(self) -> Tuple[int, List[str]]:
        """
        清理所有标记为孤立的宝可梦实例ID。
        这个方法可以被定时任务或管理员命令调用。
        
        Returns:
            Tuple[int, List[str]]: 清理的ID数量和详细日志
        """
        logs = []
        cleaned_count = 0
        
        try:
            # 获取所有标记为孤立的Pokemon ID
            orphaned_ids = await self.pokemon_repo.get_orphaned_pokemon_ids()
            
            if not orphaned_ids:
                logs.append("没有发现孤立的宝可梦ID")
                logger.info("没有孤立的宝可梦ID需要清理。")
                return 0, logs
            
            logs.append(f"发现 {len(orphaned_ids)} 个孤立的宝可梦ID")
            
            # 获取所有玩家数据进行清理
            all_players = await self.player_repo.get_all_players()
            updated_players = []
            
            for player in all_players:
                player_updated = False
                
                # 检查并清理队伍中的孤立ID
                original_party_count = len(player.party_pokemon_ids)
                player.party_pokemon_ids = [pid for pid in player.party_pokemon_ids if pid not in orphaned_ids]
                party_cleaned = original_party_count - len(player.party_pokemon_ids)
                
                # 检查并清理盒子中的孤立ID
                original_box_count = len(player.box_pokemon_ids)
                player.box_pokemon_ids = [pid for pid in player.box_pokemon_ids if pid not in orphaned_ids]
                box_cleaned = original_box_count - len(player.box_pokemon_ids)
                
                if party_cleaned > 0 or box_cleaned > 0:
                    player_updated = True
                    updated_players.append(player)
                    log_msg = f"玩家 {player.player_id}: 清理队伍 {party_cleaned} 个, 盒子 {box_cleaned} 个孤立ID"
                    logs.append(log_msg)
                    logger.info(log_msg)
            
            # 批量保存更新的玩家数据
            for player in updated_players:
                await self.player_repo.save_player(player)
            
            # 从数据库中删除孤立的Pokemon实例
            for orphaned_id in orphaned_ids:
                try:
                    await self.pokemon_repo.delete_pokemon_instance(orphaned_id)
                    cleaned_count += 1
                    logs.append(f"删除孤立宝可梦实例: {orphaned_id}")
                except Exception as e:
                    error_msg = f"删除孤立宝可梦实例 {orphaned_id} 失败: {e}"
                    logs.append(error_msg)
                    logger.error(error_msg, exc_info=True)
            
            # 记录清理结果
            summary_msg = f"清理完成: 删除 {cleaned_count} 个孤立宝可梦实例, 更新 {len(updated_players)} 个玩家数据"
            logs.append(summary_msg)
            logger.info(summary_msg)
            
            return cleaned_count, logs
            
        except Exception as e:
            error_msg = f"清理孤立宝可梦ID时发生错误: {e}"
            logs.append(error_msg)
            logger.error(error_msg, exc_info=True)
            return cleaned_count, logs


    async def evolve_pokemon(self, pokemon_instance_id: int, evolution_id: int) -> Tuple[bool, str, Optional[Pokemon]]:
        """
        执行宝可梦进化。
        
        Args:
            pokemon_instance_id (int): 要进化的宝可梦实例ID
            evolution_id (int): 进化目标种族ID
            
        Returns:
            Tuple[bool, str, Optional[Pokemon]]: 包含操作是否成功的布尔值、描述结果的消息和进化后的宝可梦实例
        """
        try:
            # 获取宝可梦实例
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
            if not pokemon:
                raise PokemonNotFoundException(f"宝可梦实例 {pokemon_instance_id} 不存在")
            
            # 获取进化目标种族数据
            evolution_race = await self.metadata_repo.get_pokemon_race(evolution_id)
            if not evolution_race:
                return False, f"无法找到进化目标种族 {evolution_id}", None
            
            # 检查是否可以进化到目标种族
            can_evolve, reason = pet_evolution.can_evolve_to(pokemon, evolution_id)
            if not can_evolve:
                return False, reason, pokemon
            
            # 执行进化
            evolved_pokemon = await pet_evolution.evolve_pokemon(pokemon, evolution_race)
            
            # 保存进化后的宝可梦
            await self.pokemon_repo.save_pokemon_instance(evolved_pokemon)
            
            # 记录进化事件
            logger.info(f"宝可梦 {pokemon.name}(ID:{pokemon_instance_id}) 成功进化为 {evolved_pokemon.name}")
            
            return True, f"{pokemon.nickname or pokemon.name}成功进化为{evolved_pokemon.name}！", evolved_pokemon
            
        except PokemonNotFoundException as e:
            logger.error(f"宝可梦进化失败: {e}")
            raise
        except Exception as e:
            logger.error(f"宝可梦进化过程中发生错误: {e}", exc_info=True)
            return False, f"进化过程中发生错误: {str(e)}", None

    async def learn_new_skill(self, pokemon_instance_id: int, skill_id: int) -> Tuple[bool, str, Optional[Pokemon]]:
        """
        让宝可梦学习新技能。
        
        Args:
            pokemon_instance_id (int): 宝可梦实例ID
            skill_id (int): 要学习的技能ID
            
        Returns:
            Tuple[bool, str, Optional[Pokemon]]: 包含操作是否成功的布尔值、描述结果的消息和更新后的宝可梦实例
            
        注意：如果宝可梦的技能已满，则会返回成功=False，同时触发一个技能替换事件。
        """
        try:
            # 获取宝可梦实例
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
            if not pokemon:
                raise PokemonNotFoundException(f"宝可梦实例 {pokemon_instance_id} 不存在")
            
            # 获取技能数据
            skill_data = await self.metadata_repo.get_skill_by_id(skill_id)
            if not skill_data:
                return False, f"技能ID {skill_id} 不存在", None
            
            # 检查是否已经学会了这个技能
            if any(skill.id == skill_id for skill in pokemon.skills):
                return False, f"{pokemon.nickname or pokemon.name}已经学会了{skill_data.name}", pokemon
            
            # 检查是否有空位学习新技能
            from backend.config.settings import MAX_POKEMON_SKILLS
            max_skills = MAX_POKEMON_SKILLS
            
            if len(pokemon.skills) < max_skills:
                # 直接学习新技能
                await pet_skill.add_skill_to_pokemon(pokemon, skill_data)
                
                # 保存更新后的宝可梦
                await self.pokemon_repo.save_pokemon_instance(pokemon)
                
                return True, f"{pokemon.nickname or pokemon.name}学会了{skill_data.name}！", pokemon
            else:
                # 技能已满，需要替换
                # 触发技能替换事件
                from backend.models.event import SkillReplacementRequiredEvent
                
                # 准备当前技能列表，用于UI显示
                current_skills = [
                    {"id": skill.id, "name": skill.name, "description": skill.description}
                    for skill in pokemon.skills
                ]
                
                event = SkillReplacementRequiredEvent(
                    pokemon_instance_id=pokemon_instance_id,
                    pokemon_name=pokemon.nickname or pokemon.name,
                    new_skill_id=skill_id,
                    new_skill_name=skill_data.name,
                    current_skills=current_skills,
                    message=f"{pokemon.nickname or pokemon.name}想学习{skill_data.name}，但已经学会了{max_skills}个技能。请选择要替换的技能。"
                )
                
                # 发布事件
                if hasattr(self, "event_publisher") and self.event_publisher:
                    await self.event_publisher.publish_event(event)
                    
                return False, f"{pokemon.nickname or pokemon.name}想学习{skill_data.name}，但技能已满。请选择一个要忘记的技能。", pokemon
                
        except PokemonNotFoundException as e:
            logger.error(f"宝可梦学习技能失败: {e}")
            raise
        except Exception as e:
            logger.error(f"宝可梦学习技能时发生错误: {e}", exc_info=True)
            return False, f"学习技能时发生错误: {str(e)}", None

    async def replace_skill(self, pokemon_instance_id: int, old_skill_id: int, new_skill_id: int) -> Tuple[bool, str, Optional[Pokemon]]:
        """
        替换宝可梦的一个技能。
        
        Args:
            pokemon_instance_id (int): 宝可梦实例ID
            old_skill_id (int): 要替换的旧技能ID
            new_skill_id (int): 要学习的新技能ID
            
        Returns:
            Tuple[bool, str, Optional[Pokemon]]: 包含操作是否成功的布尔值、描述结果的消息和更新后的宝可梦实例
        """
        try:
            # 获取宝可梦实例
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
            if not pokemon:
                raise PokemonNotFoundException(f"宝可梦实例 {pokemon_instance_id} 不存在")
            
            # 获取新技能数据
            new_skill_data = await self.metadata_repo.get_skill_by_id(new_skill_id)
            if not new_skill_data:
                return False, f"技能ID {new_skill_id} 不存在", None
            
            # 检查宝可梦是否有旧技能
            skill_index = -1
            for i, skill in enumerate(pokemon.skills):
                if skill.id == old_skill_id:
                    skill_index = i
                    break
                
            if skill_index == -1:
                return False, f"{pokemon.nickname or pokemon.name}没有该技能，无法替换", pokemon
            
            # 检查是否已经学会了新技能
            if any(skill.id == new_skill_id for skill in pokemon.skills):
                return False, f"{pokemon.nickname or pokemon.name}已经学会了{new_skill_data.name}", pokemon
            
            # 替换技能
            result = await pet_skill.replace_skill(pokemon, skill_index, new_skill_data)
            if not result:
                return False, f"替换技能失败", pokemon
            
            # 保存更新后的宝可梦
            await self.pokemon_repo.save_pokemon_instance(pokemon)
            
            old_skill_name = pokemon.skills[skill_index].name
            logger.info(f"宝可梦 {pokemon.name}(ID:{pokemon_instance_id}) 将技能 {old_skill_name} 替换为 {new_skill_data.name}")
            
            return True, f"{pokemon.nickname or pokemon.name}忘记了{old_skill_name}，学会了{new_skill_data.name}！", pokemon
            
        except PokemonNotFoundException as e:
            logger.error(f"宝可梦替换技能失败: {e}")
            raise
        except Exception as e:
            logger.error(f"宝可梦替换技能时发生错误: {e}", exc_info=True)
            return False, f"替换技能时发生错误: {str(e)}", None

    async def use_item_on_pokemon(self, player_id: str, pokemon_instance_id: int, item_id: int) -> Tuple[bool, str, Optional[Pokemon]]:
        """
        对宝可梦使用道具。
        
        Args:
            player_id (str): 玩家ID
            pokemon_instance_id (int): 宝可梦实例ID
            item_id (int): 要使用的道具ID
            
        Returns:
            Tuple[bool, str, Optional[Pokemon]]: 包含操作是否成功的布尔值、描述结果的消息和更新后的宝可梦实例
        """
        try:
            # 获取玩家数据，确认道具所有权
            player = await self.player_repo.get_player(player_id)
            if not player:
                raise PlayerNotFoundException(f"玩家 {player_id} 不存在")
            
            # 检查玩家是否拥有该道具
            if item_id not in player.items or player.items[item_id] <= 0:
                return False, "你没有该道具", None
            
            # 获取宝可梦实例
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
            if not pokemon:
                raise PokemonNotFoundException(f"宝可梦实例 {pokemon_instance_id} 不存在")
            
            # 确认宝可梦归属于该玩家
            if pokemon_instance_id not in player.party_pokemon_ids and pokemon_instance_id not in player.box_pokemon_ids:
                raise PokemonNotInCollectionException(f"宝可梦 {pokemon_instance_id} 不属于玩家 {player_id}")
            
            # 获取道具数据
            item = await self.item_service.get_item(item_id)
            
            # 应用道具效果
            result, message, updated_pokemon = await pet_equipment.apply_item_effect(item, pokemon)

            if result:
                # 道具使用成功，减少玩家库存
                player.items[item_id] -= 1
                if player.items[item_id] <= 0:
                    del player.items[item_id]
                
                # 保存更新后的数据
                await self.player_repo.save_player(player)
                if updated_pokemon:
                    await self.pokemon_repo.save_pokemon_instance(updated_pokemon)
                
                logger.info(f"玩家 {player_id} 对宝可梦 {pokemon.name}(ID:{pokemon_instance_id}) 使用了 {item.name}")
                
            return result, message, updated_pokemon
            
        except (PlayerNotFoundException, PokemonNotFoundException, PokemonNotInCollectionException) as e:
            logger.error(f"道具使用失败: {e}")
            raise
        except Exception as e:
            logger.error(f"使用道具时发生错误: {e}", exc_info=True)
            return False, f"使用道具时发生错误: {str(e)}", None

    async def check_evolution(self, pokemon_instance_id: int, item_id: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
        """
        检查宝可梦是否满足进化条件。
        
        Args:
            pokemon_instance_id (int): 宝可梦实例ID
            item_id (Optional[int]): 如果使用进化道具，则提供道具ID
            
        Returns:
            Tuple[bool, str, Optional[int]]: 包含是否可以进化的布尔值、说明消息和可进化的目标种族ID（如果可以进化）
        """
        try:
            # 获取宝可梦实例
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
            if not pokemon:
                raise PokemonNotFoundException(f"宝可梦实例 {pokemon_instance_id} 不存在")
            
            # 获取道具数据（如果提供）
            item = None
            if item_id:
                item = await self.item_service.get_item(item_id)
            
            # 检查进化条件
            from backend.core.pet import pet_evolution
            evolution_target_id = await pet_evolution.check_evolution_conditions(pokemon, item)
            
            if evolution_target_id:
                # 获取进化目标种族数据
                evolution_race = await self.metadata_repo.get_pokemon_race(evolution_target_id)
                if not evolution_race:
                    return False, f"无法找到进化目标种族 {evolution_target_id}", None
                
                return True, f"{pokemon.nickname or pokemon.name}可以进化为{evolution_race.name}！", evolution_target_id
            else:
                return False, f"{pokemon.nickname or pokemon.name}现在无法进化。", None
            
        except PokemonNotFoundException as e:
            logger.error(f"检查宝可梦进化条件失败: {e}")
            raise
        except Exception as e:
            logger.error(f"检查宝可梦进化条件时发生错误: {e}", exc_info=True)
            return False, f"检查进化条件时发生错误: {str(e)}", None

    async def get_pokemon_status(self, pokemon_instance_id: int) -> Tuple[Dict[str, Any], str]:
        """
        获取宝可梦的详细状态信息。
        
        Args:
            pokemon_instance_id (int): 宝可梦实例ID
            
        Returns:
            Tuple[Dict[str, Any], str]: 包含宝可梦状态信息的字典和说明消息
        """
        try:
            # 获取宝可梦实例
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
            if not pokemon:
                raise PokemonNotFoundException(f"宝可梦实例 {pokemon_instance_id} 不存在")
            
            # 获取种族数据
            race = await self.metadata_repo.get_pokemon_race(pokemon.race_id)
            
            # 计算宝可梦的各项属性比例
            hp_percentage = round((pokemon.current_hp / pokemon.max_hp) * 100) if pokemon.max_hp > 0 else 0
            exp_to_next_level = self._calculate_exp_to_next_level(pokemon.level, pokemon.exp)
            exp_percentage = round((pokemon.exp / exp_to_next_level) * 100) if exp_to_next_level > 0 else 100
            
            # 获取宝可梦技能详情
            skills = []
            for skill in pokemon.skills:
                skill_data = await self.metadata_repo.get_skill_by_id(skill.id)
                if skill_data:
                    skills.append({
                        "id": skill.id,
                        "name": skill.name,
                        "pp": skill.current_pp,
                        "max_pp": skill.max_pp,
                        "type": skill_data.type,
                        "power": skill_data.power,
                        "accuracy": skill_data.accuracy,
                        "description": skill_data.description
                    })
            
            # 检查该宝可梦是否可以进化
            can_evolve, _, evolution_target = await self.check_evolution(pokemon_instance_id)
            
            # 构建状态信息
            status_info = {
                "instance_id": pokemon.instance_id,
                "name": pokemon.name,
                "nickname": pokemon.nickname,
                "level": pokemon.level,
                "types": race.types if race else [],
                "hp": pokemon.current_hp,
                "max_hp": pokemon.max_hp,
                "hp_percentage": hp_percentage,
                "exp": pokemon.exp,
                "exp_to_next_level": exp_to_next_level,
                "exp_percentage": exp_percentage,
                "stats": {
                    "attack": pokemon.attack,
                    "defense": pokemon.defense,
                    "sp_attack": pokemon.sp_attack,
                    "sp_defense": pokemon.sp_defense,
                    "speed": pokemon.speed
                },
                "skills": skills,
                "status_effects": [effect.to_dict() for effect in pokemon.status_effects] if pokemon.status_effects else [],
                "can_evolve": can_evolve,
                "evolution_target_id": evolution_target if can_evolve else None,
                "original_trainer_id": pokemon.original_trainer_id
            }
            
            return status_info, f"获取到{pokemon.nickname or pokemon.name}的状态信息"
            
        except PokemonNotFoundException as e:
            logger.error(f"获取宝可梦状态失败: {e}")
            raise
        except Exception as e:
            logger.error(f"获取宝可梦状态时发生错误: {e}", exc_info=True)
            raise e
        
    def _calculate_exp_to_next_level(self, current_level: int, current_exp: int) -> int:
        """计算升级所需经验值"""
        return pet_grow.calculate_exp_to_next_level(current_level, current_exp)

    async def gain_experience(self, pokemon_instance_id: int, exp_amount: int) -> Tuple[Pokemon, List[str], List[Any]]:
        """
        为宝可梦添加经验值，处理可能的升级和学习技能事件。
        
        Args:
            pokemon_instance_id (int): 宝可梦实例ID
            exp_amount (int): 获得的经验值数量
            
        Returns:
            Tuple[Pokemon, List[str], List[Any]]: 包含更新后的宝可梦实例、消息列表和事件列表
        """
        try:
            # 获取宝可梦实例
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
            if not pokemon:
                raise PokemonNotFoundException(f"宝可梦实例 {pokemon_instance_id} 不存在")
            
            # 使用Pokemon模型的add_exp方法处理经验获取和升级
            messages, events = await pokemon.add_exp(exp_amount, self.metadata_repo)
            
            # 保存更新后的宝可梦
            await self.pokemon_repo.save_pokemon_instance(pokemon)
            
            logger.info(f"宝可梦 {pokemon.name}(ID:{pokemon_instance_id}) 获得了 {exp_amount} 点经验值")
            
            # 如果有EventPublisher，发布相关事件
            if hasattr(self, "event_publisher") and self.event_publisher:
                for event in events:
                    await self.event_publisher.publish_event(event)
                
            return pokemon, messages, events
            
        except PokemonNotFoundException as e:
            logger.error(f"宝可梦获取经验失败: {e}")
            raise
        except Exception as e:
            logger.error(f"宝可梦获取经验时发生错误: {e}", exc_info=True)
            raise e

    async def change_status(self, pokemon_instance_id: int, status_effect_id: Optional[int] = None, 
                          remove_status: bool = False) -> Tuple[bool, str, Optional[Pokemon]]:
        """
        改变宝可梦的状态效果（添加或移除）。
        
        Args:
            pokemon_instance_id (int): 宝可梦实例ID
            status_effect_id (Optional[int]): 要添加的状态效果ID，如果是移除则可为None
            remove_status (bool): 是否移除状态，True为移除，False为添加
            
        Returns:
            Tuple[bool, str, Optional[Pokemon]]: 包含操作是否成功的布尔值、描述结果的消息和更新后的宝可梦实例
        """
        try:
            # 获取宝可梦实例
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
            if not pokemon:
                raise PokemonNotFoundException(f"宝可梦实例 {pokemon_instance_id} 不存在")
            
            if remove_status:
                # 移除所有状态效果
                if status_effect_id is None:
                    old_status = [effect.name for effect in pokemon.status_effects] if pokemon.status_effects else []
                    pokemon.status_effects = []
                    status_message = f"已清除 {pokemon.nickname or pokemon.name} 的所有状态效果"
                else:
                    # 移除特定状态效果
                    old_status = []
                    new_status_effects = []
                    status_removed = False
                    
                    for effect in pokemon.status_effects:
                        if effect.effect_id == status_effect_id:
                            old_status.append(effect.name)
                            status_removed = True
                        else:
                            new_status_effects.append(effect)
                            
                    pokemon.status_effects = new_status_effects
                    
                    if status_removed:
                        status_effect = await self.metadata_repo.get_status_effect_by_id(status_effect_id)
                        status_name = status_effect.name if status_effect else f"状态效果 {status_effect_id}"
                        status_message = f"已移除 {pokemon.nickname or pokemon.name} 的 {status_name} 状态"
                    else:
                        status_message = f"{pokemon.nickname or pokemon.name} 没有该状态效果"
            else:
                # 添加状态效果
                if status_effect_id is None:
                    return False, f"需要提供状态效果ID来添加状态", pokemon
                    
                # 获取状态效果数据
                status_effect = await self.metadata_repo.get_status_effect_by_id(status_effect_id)
                if not status_effect:
                    return False, f"状态效果ID {status_effect_id} 不存在", pokemon
                    
                # 检查是否已有该状态
                if any(effect.effect_id == status_effect_id for effect in pokemon.status_effects):
                    return False, f"{pokemon.nickname or pokemon.name} 已经有 {status_effect.name} 状态", pokemon
                    
                # 添加状态效果
                pokemon.status_effects.append(status_effect)
                status_message = f"{pokemon.nickname or pokemon.name} 获得了 {status_effect.name} 状态"
                
            # 保存更新后的宝可梦
            await self.pokemon_repo.save_pokemon_instance(pokemon)
            
            logger.info(f"宝可梦 {pokemon.name}(ID:{pokemon_instance_id}) 状态已更改: {status_message}")
            
            return True, status_message, pokemon
            
        except PokemonNotFoundException as e:
            logger.error(f"更改宝可梦状态失败: {e}")
            raise
        except Exception as e:
            logger.error(f"更改宝可梦状态时发生错误: {e}", exc_info=True)
            return False, f"更改状态时发生错误: {str(e)}", None

    async def check_and_process_evolution(self, pokemon_instance_id: int, 
                                        item_id: Optional[int] = None) -> Tuple[bool, str, Optional[Pokemon]]:
        """
        检查并处理宝可梦的进化。
        
        Args:
            pokemon_instance_id (int): 宝可梦实例ID
            item_id (Optional[int]): 如果使用进化道具，则提供道具ID
            
        Returns:
            Tuple[bool, str, Optional[Pokemon]]: 包含操作是否成功的布尔值、描述结果的消息和进化后的宝可梦实例
        """
        try:
            # 获取宝可梦实例
            pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
            if not pokemon:
                raise PokemonNotFoundException(f"宝可梦实例 {pokemon_instance_id} 不存在")
            
            # 获取道具数据（如果提供）
            item = None
            if item_id:
                item = await self.item_service.get_item(item_id)
            
            # 处理进化
            evolution_event = await self._process_evolution(pokemon, item)
            
            if evolution_event:
                # 进化成功
                # 重新获取更新后的宝可梦
                pokemon = await self.pokemon_repo.get_pokemon_instance(pokemon_instance_id)
                return True, evolution_event.message, pokemon
            else:
                # 进化失败或不满足条件
                return False, "宝可梦无法进化或不满足进化条件", pokemon
            
        except Exception as e:
            logger.error(f"处理宝可梦进化时出错: {e}", exc_info=True)
            return False, f"处理进化时发生错误: {str(e)}", None

    async def _process_evolution(self, pokemon: Pokemon, item: Optional[Item] = None) -> Optional[PokemonEvolvedEvent]:
        """处理宝可梦进化的内部方法"""
        try:
            # 检查是否可以进化
            from backend.core.pet import pet_evolution
            evolution_target_id = await pet_evolution.check_evolution_conditions(pokemon, item)
            if not evolution_target_id:
                return None
            
            # 获取当前种族和目标种族数据
            current_race = await self.metadata_repo.get_race_by_id(pokemon.species_id)
            evolution_target = await self.metadata_repo.get_race_by_id(evolution_target_id)
            if not current_race or not evolution_target:
                logger.error(f"无法获取种族数据: current_id={pokemon.species_id}, target_id={evolution_target_id}")
                return None
            
            # 获取可学习的技能
            available_skills = await self.metadata_repo.get_skills_for_race(evolution_target_id)
            
            # 记录旧数据用于事件
            old_race_id = pokemon.species_id
            old_name = current_race.name
            old_nickname = pokemon.nickname or old_name
            
            # 执行进化
            pokemon, evolution_messages = await pet_evolution.evolve_pokemon(pokemon, current_race, evolution_target, available_skills)
            
            # 保存更新后的宝可梦
            await self.pokemon_repo.save_pokemon_instance(pokemon)
            
            # 创建进化事件
            event = PokemonEvolvedEvent(
                pokemon_instance_id=pokemon.instance_id,
                player_id=pokemon.player_id,
                old_race_id=old_race_id,
                new_race_id=evolution_target_id,
                old_name=old_nickname,
                new_name=pokemon.nickname or evolution_target.name,
                message=f"恭喜！你的 {old_nickname} 进化成了 {pokemon.nickname or evolution_target.name}！"
            )
            
            logger.info(f"宝可梦进化成功: {old_nickname} -> {pokemon.nickname or evolution_target.name}")
            return event
            
        except Exception as e:
            logger.error(f"处理宝可梦进化时发生错误: {e}", exc_info=True)
            return None

