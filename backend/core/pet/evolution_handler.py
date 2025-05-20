from typing import Optional, Dict, Any

from backend.models.pokemon import Pokemon
from backend.models.events import EvolutionEvent, BattleMessageEvent
from backend.models.item import Item
from backend.data_access.metadata_loader import MetadataRepository
from backend.core.pokemon_factory import PokemonFactory
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class EvolutionHandler:
    """
    处理宝可梦进化逻辑。
    """

    def __init__(self, metadata_repo: MetadataRepository, pokemon_factory: PokemonFactory):
        self._metadata_repo = metadata_repo
        self._pokemon_factory = pokemon_factory

    async def check_and_process_evolution(self, pokemon: Pokemon, item_used: Optional[Item] = None) -> Optional[EvolutionEvent]:
        """
        检查宝可梦是否满足进化条件，如果满足则处理进化。
        现在也考虑道具进化。
        如果发生进化，则返回 EvolutionEvent，否则返回 None。
        一次调用此方法最多只会处理一次进化。
        """
        logger.debug(f"检查宝可梦 {pokemon.nickname} (ID: {pokemon.pokemon_id}, Race ID: {pokemon.race_id}, Level: {pokemon.level}) 是否可以进化 (道具: {item_used.name if item_used else '无'})。")

        evolution_data = await self._metadata_repo.get_evolution_data_for_pokemon(pokemon.race_id)
        if not evolution_data:
            logger.debug(f"宝可梦 Race ID {pokemon.race_id} 没有找到进化路径。")
            return None

        original_name = pokemon.name # 在获取进化数据后记录，以防万一宝可梦对象在过程中被修改名称
        original_race_id = pokemon.race_id

        for evo_method in evolution_data.get("methods", []):
            evolved_race_id: Optional[int] = None
            evolution_triggered_by: str = "" # 用于日志和可能的未来扩展

            # 1. 检查道具进化 (如果提供了道具)
            if item_used:
                if evo_method.get("method") == "use_item" and evo_method.get("item_id") == item_used.item_id:
                    # 检查等级限制 (如果有)
                    min_level = evo_method.get("min_level")
                    if min_level is not None and pokemon.level < min_level:
                        logger.debug(f"道具 {item_used.name} 进化需要等级 {min_level}, 当前等级 {pokemon.level} 不足。")
                        continue # 检查下一个进化方法

                    evolved_race_id = evo_method.get("evolves_to_id")
                    evolution_triggered_by = f"item {item_used.name}"
                    logger.info(f"宝可梦 {original_name} (Race ID: {original_race_id}) 通过使用道具 {item_used.name} 满足进化条件，目标 Race ID: {evolved_race_id}。")
                    # 找到道具进化，直接跳出循环处理进化
                    break 
                else:
                    # 如果提供了道具，但当前进化方法不是该道具，则跳过此方法
                    # 确保道具进化优先于其他同级条件（如等级）
                    continue 
            
            # 2. 检查等级进化 (如果没有使用道具，或者道具不匹配任何道具进化方法)
            elif evo_method.get("method") == "level_up": # 注意这里用 elif，确保道具进化优先
                required_level = evo_method.get("level")
                # 当前仅基于等级进化
                if required_level is not None and pokemon.level >= required_level:
                    # 这里是等级进化
                    evolved_race_id = evo_method.get("evolves_to_id")
                    evolution_triggered_by = f"level {pokemon.level}"
                    logger.info(f"宝可梦 {original_name} (Race ID: {original_race_id}) 达到等级 {pokemon.level} (要求: {required_level}) 满足进化条件，目标 Race ID: {evolved_race_id}。")
                    # 找到等级进化，直接跳出循环处理进化
                    break # 找到第一个满足的等级进化就跳出

            # 其他进化方法可以按需在此处以 elif 的形式添加
            # 例如:
            # elif evo_method.get("method") == "trade":
            #     # ... trade logic ...
            #     pass

        # 如果通过循环找到了一个有效的进化路径
        if evolved_race_id:
            try:
                evolved_species_data = await self._metadata_repo.get_pokemon_species_data(evolved_race_id)
                if not evolved_species_data:
                    logger.error(f"无法获取进化目标 Race ID {evolved_race_id} 的物种数据。")
                    return None

                # 更新宝可梦实例的属性
                # 假设 Pokemon 类有这些属性或通过 PokemonFactory 更新
                pokemon.race_id = evolved_race_id
                # 如果进化后名称通常会改变（例如，小火龙 -> 火恐龙），则更新
                # 如果希望保留昵称，则不应更改 pokemon.nickname
                # 官方游戏中，进化后默认名称会变为新形态的名称，除非之前有昵称
                # 我们这里假设 name 存储的是物种名，nickname 是玩家自定义的
                new_species_name = evolved_species_data.get("name", f"RaceID_{evolved_race_id}")
                pokemon.name = new_species_name # 更新为新物种的名称

                pokemon.type1 = evolved_species_data.get("type1")
                pokemon.type2 = evolved_species_data.get("type2")
                
                # 更新基础属性
                base_stats_data = evolved_species_data.get("base_stats", {})
                pokemon.base_hp = base_stats_data.get("hp", pokemon.base_hp)
                pokemon.base_attack = base_stats_data.get("attack", pokemon.base_attack)
                pokemon.base_defense = base_stats_data.get("defense", pokemon.base_defense)
                pokemon.base_special_attack = base_stats_data.get("special_attack", pokemon.base_special_attack)
                pokemon.base_special_defense = base_stats_data.get("special_defense", pokemon.base_special_defense)
                pokemon.base_speed = base_stats_data.get("speed", pokemon.base_speed)

                # 重新计算当前属性
                # 确保 Pokemon 类有 recalculate_stats 方法，或者通过 PokemonFactory 更新
                if hasattr(pokemon, 'recalculate_stats') and callable(pokemon.recalculate_stats):
                    # 假设它能自己处理或者不需要参数
                    pokemon.recalculate_stats()
                else:
                    # 或者通过 PokemonFactory 更新 (如果 PokemonFactory 有这样的同步方法)
                    # self._pokemon_factory.update_pokemon_stats_on_evolution_sync(pokemon)
                    logger.warning(f"宝可梦 {pokemon.name} 缺少 recalculate_stats 方法或 PokemonFactory 无相应同步更新方法。")


                # 进化后HP全满 (常见游戏设定)
                # 假设 Pokemon 类有 get_stat 方法
                if hasattr(pokemon, 'get_stat') and callable(pokemon.get_stat) and hasattr(pokemon, 'current_hp'):
                     pokemon.current_hp = pokemon.get_stat("hp")
                else:
                    logger.warning(f"无法为宝可梦 {pokemon.name} 设置进化后的HP。")


                logger.info(f"宝可梦 {original_name} (Race ID: {original_race_id}) 通过 {evolution_triggered_by} 进化为了 {pokemon.name} (Race ID: {pokemon.race_id})!")

                return EvolutionEvent(
                    pokemon_id=pokemon.pokemon_id,
                    original_race_id=original_race_id,
                    evolved_race_id=pokemon.race_id,
                    original_name=original_name,
                    evolved_name=pokemon.name, # 使用更新后的 pokemon.name
                    message=f"{original_name} 进化成了 {pokemon.name}！"
                )
            except Exception as e:
                logger.error(f"处理宝可梦 {original_name} (Race ID: {original_race_id}) 进化为 Race ID {evolved_race_id} 时发生错误: {e}", exc_info=True)
                return None # 进化过程中发生错误

        logger.debug(f"宝可梦 {pokemon.nickname} (Race ID: {original_race_id}) 当前未满足任何进化条件 (道具: {item_used.name if item_used else '无'})。")
        return None 