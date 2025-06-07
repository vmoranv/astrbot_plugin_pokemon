from typing import List, Dict, Any, Optional, Tuple
from backend.models.item import Item, ItemEffectType
from backend.models.pokemon import Pokemon
from backend.models.player import Player
from backend.models.event import HealEvent, StatusCuredEvent, CaptureSuccessEvent, BattleMessageEvent
from backend.data_access.repositories.item_repository import ItemRepository
from backend.data_access.repositories.player_repository import PlayerRepository
from backend.data_access.repositories.pokemon_repository import PokemonRepository
from backend.utils.exceptions import ItemNotFoundException, PlayerNotFoundException, PokemonNotFoundException, InvalidOperationException
from backend.utils.logger import get_logger
# from backend.core.pet import pet_item # Example core dependency
from backend.core.services.player_service import PlayerService
from backend.core.services.pokemon_service import PokemonService

logger = get_logger(__name__)

class ItemService:
    """Service for Item related business logic."""

    def __init__(self, item_repo: Optional[ItemRepository] = None, 
                 player_repo: Optional[PlayerRepository] = None, 
                 pokemon_repo: Optional[PokemonRepository] = None):
        self.item_repo = item_repo or ItemRepository()
        self.player_repo = player_repo or PlayerRepository()
        self.pokemon_repo = pokemon_repo or PokemonRepository()
        self.player_service = PlayerService()
        self.pokemon_service = PokemonService()

    async def get_item(self, item_id: int) -> Optional[Item]:
        """
        Retrieves item metadata. Raises ItemNotFoundException if not found.
        """
        try:
            item = await self.item_repo.get_item(item_id)
            return item
        except ItemNotFoundException as e:
            logger.error(f"获取道具失败: {e}")
            return None

    async def get_player_items(self, player_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the quantity of a specific item a player has.
        """
        try:
            # 获取玩家背包中的道具数量
            player_items = await self.item_repo.get_player_items(player_id)
            
            # 获取每个道具的详细信息
            result = []
            for player_item in player_items:
                item_id = player_item["item_id"]
                quantity = player_item["quantity"]
                
                item = await self.item_repo.get_item(item_id)
                if item:
                    result.append({
                        "item_id": item.item_id,
                        "name": item.name,
                        "description": item.description,
                        "effect_type": item.effect_type,
                        "use_target": item.use_target,
                        "price": item.price,
                        "quantity": quantity
                    })
            
            return result
        except Exception as e:
            logger.error(f"获取玩家道具列表失败: {e}", exc_info=True)
            return []

    async def add_item_to_player(self, player_id: str, item_id: int, quantity: int = 1) -> bool:
        """
        Adds a specified quantity of an item to a player's inventory.
        Returns the updated Player object.
        """
        try:
            # 检查道具是否存在
            item = await self.item_repo.get_item(item_id)
            if not item:
                logger.error(f"道具 {item_id} 不存在")
                return False
                
            # 检查玩家是否存在
            player = await self.player_repo.get_player_by_id(player_id)
            if not player:
                logger.error(f"玩家 {player_id} 不存在")
                return False
                
            # 添加道具到玩家背包
            success = await self.item_repo.add_player_item(player_id, item_id, quantity)
            if success:
                logger.info(f"向玩家 {player_id} 添加了 {quantity} 个 {item.name}")
            return success
        except Exception as e:
            logger.error(f"向玩家添加道具失败: {e}", exc_info=True)
            return False

    async def remove_item_from_player(self, player_id: str, item_id: int, quantity: int = 1) -> Player:
        """
        Removes a specified quantity of an item from a player's inventory.
        Raises InsufficientItemException if the player does not have enough items.
        Returns the updated Player object.
        """
        if quantity <= 0:
            logger.warning(f"Attempted to remove non-positive quantity ({quantity}) of item {item_id} from player {player_id}.")
            return await self.player_service.get_player(player_id)

        player = await self.player_service.get_player(player_id)
        current_quantity = player.items.get(item_id, 0)

        if current_quantity < quantity:
            logger.warning(f"Player {player_id} attempted to remove {quantity} of item {item_id} but only has {current_quantity}.")
            raise InvalidOperationException(f"Player {player_id} does not have enough of item {item_id}.")

        player.items[item_id] -= quantity
        if player.items[item_id] <= 0:
            del player.items[item_id]

        await self.player_service.save_player(player)
        logger.info(f"Removed {quantity} of item {item_id} from player {player_id}. Remaining quantity: {player.items.get(item_id, 0)}")
        return player

    async def use_item(self, player_id: str, item_id: int, target_id: Optional[int] = None, battle_id: Optional[str] = None) -> Tuple[bool, str, List[Any]]:
        """
        Uses an item from the player's inventory.
        target_id could be a pokemon_id, player_id, or map_id depending on item type.
        Returns a message describing the result.
        """
        try:
            # 检查玩家是否存在
            player = await self.player_repo.get_player_by_id(player_id)
            if not player:
                raise PlayerNotFoundException(f"玩家 {player_id} 不存在")
                
            # 检查道具是否存在且玩家拥有
            item = await self.item_repo.get_item(item_id)
            if not item:
                raise ItemNotFoundException(f"道具 {item_id} 不存在")
                
            # 检查玩家是否拥有该道具
            player_items = await self.item_repo.get_player_items(player_id)
            item_entry = next((pi for pi in player_items if pi["item_id"] == item_id), None)
            if not item_entry or item_entry["quantity"] <= 0:
                raise InvalidOperationException(f"玩家 {player_id} 没有道具 {item.name}")
                
            # 根据道具类型和目标处理不同的效果
            events = []
            result_message = ""
            success = False
            
            if item.effect_type == ItemEffectType.HEAL_HP.value:
                # 治疗HP的道具
                if target_id is None:
                    raise InvalidOperationException("使用治疗道具需要指定目标宝可梦")
                    
                pokemon = await self.pokemon_repo.get_pokemon_instance(target_id)
                if not pokemon:
                    raise PokemonNotFoundException(f"宝可梦 {target_id} 不存在")
                    
                # 检查宝可梦是否属于该玩家
                if target_id not in player.party_pokemon_ids and target_id not in player.box_pokemon_ids:
                    raise InvalidOperationException(f"宝可梦 {pokemon.name} 不属于玩家 {player.name}")
                    
                # 应用治疗效果
                old_hp = pokemon.current_hp
                heal_amount = self._get_heal_amount(item, pokemon)
                pokemon.current_hp = min(pokemon.current_hp + heal_amount, pokemon.max_hp)
                healed = pokemon.current_hp - old_hp
                
                # 保存宝可梦状态
                await self.pokemon_repo.save_pokemon_instance(pokemon)
                
                # 创建治疗事件
                if healed > 0:
                    result_message = f"{pokemon.nickname or pokemon.name} 恢复了 {healed} 点HP！"
                    events.append(HealEvent(
                        target_instance_id=pokemon.instance_id,
                        target_name=pokemon.nickname or pokemon.name,
                        amount_healed=healed,
                        current_hp=pokemon.current_hp,
                        max_hp=pokemon.max_hp,
                        source="item",
                        message=result_message
                    ))
                    success = True
                else:
                    result_message = f"{pokemon.nickname or pokemon.name} 的HP已满！"
                    events.append(BattleMessageEvent(message=result_message))
                    success = False
                    
            elif item.effect_type == ItemEffectType.HEAL_PP.value:
                # 恢复PP的道具
                if target_id is None:
                    raise InvalidOperationException("使用PP恢复道具需要指定目标宝可梦")
                    
                pokemon = await self.pokemon_repo.get_pokemon_instance(target_id)
                if not pokemon:
                    raise PokemonNotFoundException(f"宝可梦 {target_id} 不存在")
                    
                # 检查宝可梦是否属于该玩家
                if target_id not in player.party_pokemon_ids and target_id not in player.box_pokemon_ids:
                    raise InvalidOperationException(f"宝可梦 {pokemon.name} 不属于玩家 {player.name}")
                    
                # 应用PP恢复效果
                pp_messages = pokemon.restore_pp()
                
                # 保存宝可梦状态
                await self.pokemon_repo.save_pokemon_instance(pokemon)
                
                if pp_messages:
                    result_message = pp_messages[0]
                    events.append(BattleMessageEvent(message=result_message))
                    success = True
                else:
                    result_message = f"{pokemon.nickname or pokemon.name} 的所有技能PP已满！"
                    events.append(BattleMessageEvent(message=result_message))
                    success = False
                    
            elif item.effect_type == ItemEffectType.CURE_STATUS.value:
                # 治疗状态的道具
                if target_id is None:
                    raise InvalidOperationException("使用状态治疗道具需要指定目标宝可梦")
                    
                pokemon = await self.pokemon_repo.get_pokemon_instance(target_id)
                if not pokemon:
                    raise PokemonNotFoundException(f"宝可梦 {target_id} 不存在")
                    
                # 检查宝可梦是否属于该玩家
                if target_id not in player.party_pokemon_ids and target_id not in player.box_pokemon_ids:
                    raise InvalidOperationException(f"宝可梦 {pokemon.name} 不属于玩家 {player.name}")
                    
                # 应用状态治疗效果
                if not pokemon.status_effects:
                    result_message = f"{pokemon.nickname or pokemon.name} 没有任何状态效果！"
                    events.append(BattleMessageEvent(message=result_message))
                    success = False
                else:
                    # 清除状态效果
                    status_messages = pokemon.clear_all_status_effects()
                    
                    # 保存宝可梦状态
                    await self.pokemon_repo.save_pokemon_instance(pokemon)
                    
                    if status_messages:
                        result_message = status_messages[0]
                        events.append(StatusCuredEvent(
                            target_instance_id=pokemon.instance_id,
                            target_name=pokemon.nickname or pokemon.name,
                            message=result_message
                        ))
                        success = True
                    else:
                        result_message = f"{pokemon.nickname or pokemon.name} 没有任何状态效果！"
                        events.append(BattleMessageEvent(message=result_message))
                        success = False
            
            # 其他道具类型的处理可以继续添加...
            
            # 如果道具使用成功，减少道具数量
            if success:
                await self.item_repo.remove_player_item(player_id, item_id, 1)
                logger.info(f"玩家 {player_id} 使用了道具 {item.name}")
                
            return success, result_message, events
            
        except (PlayerNotFoundException, ItemNotFoundException, PokemonNotFoundException, InvalidOperationException) as e:
            logger.error(f"使用道具失败: {e}")
            return False, str(e), []
        except Exception as e:
            logger.error(f"使用道具时发生错误: {e}", exc_info=True)
            return False, f"使用道具时发生错误: {str(e)}", []

    def _get_heal_amount(self, item: Item, pokemon: Pokemon) -> int:
        """
        Calculates the healing amount based on the item and the pokemon.
        
        Args:
            item: The item object
            pokemon: The pokemon object
            
        Returns:
            int: The healing amount
        """
        # 这里可以根据不同的道具实现不同的治疗量计算
        # 例如，普通药水恢复20点，高级药水恢复50点，全满药恢复全部HP等
        if item.use_effect == "potion":
            return 20
        elif item.use_effect == "super_potion":
            return 50
        elif item.use_effect == "hyper_potion":
            return 200
        elif item.use_effect == "max_potion":
            return pokemon.max_hp - pokemon.current_hp
        else:
            return 20  # 默认治疗量

    def use_item_on_pokemon(self, player_id: str, item_id: int, pokemon_id: int) -> Tuple[bool, str, Optional[Any]]:
        # 在方法内部导入，避免循环依赖
        from backend.core.services.pokemon_service import PokemonService
        pokemon_service = PokemonService()
        # 方法实现...

    # Add other item related business logic methods (e.g., buy_item, sell_item, get_player_inventory)
