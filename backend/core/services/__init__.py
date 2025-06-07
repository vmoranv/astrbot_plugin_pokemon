# Import services here
from .player_service import PlayerService
from .pokemon_service import PokemonService
from .item_service import ItemService
from .map_service import MapService
from .dialog_service import DialogService
from .metadata_service import MetadataService
from .battle_service import BattleService

# 提供一个获取服务实例的工厂函数，可以避免循环依赖问题
def get_service(service_class):
    """获取服务实例，处理依赖注入"""
    if service_class == PlayerService:
        return PlayerService()
    elif service_class == PokemonService:
        return PokemonService()
    elif service_class == ItemService:
        return ItemService()
    elif service_class == MapService:
        return MapService()
    elif service_class == DialogService:
        return DialogService()
    elif service_class == MetadataService:
        return MetadataService()
    elif service_class == BattleService:
        return BattleService()
    else:
        raise ValueError(f"Unknown service class: {service_class}")
