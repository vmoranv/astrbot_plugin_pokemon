import logging
import random
from typing import List, Dict, Any, Optional, Tuple, Union

from backend.models.pokemon import Pokemon
from backend.models.player import Player
from backend.models.battle import Battle
from backend.models.map import Map, MapLocation
from backend.core.battle.battle_logic import BattleLogic
from backend.core.battle.encounter_logic import EncounterLogic
from backend.core.pet.pet_catch import calculate_catch_success
from backend.models.event import (
    BattleEvent, LevelUpEvent, StatChangeEvent, EvolutionEvent, 
    SkillLearnedEvent, BattleMessageEvent, ExperienceGainedEvent,
    SkillForgottenEvent, SkillReplacementRequiredEvent # 新增导入
)
from backend.core.pet.evolution_handler import EvolutionHandler
from backend.core.pokemon_factory import PokemonFactory
from backend.data_access.metadata_loader import MetadataRepository
from backend.models.skill import Skill
from backend.models.item import Item

logger = logging.getLogger(__name__)

class GameLogic:
    """
    游戏逻辑协调器。负责编排高级游戏流程，如战斗、捕捉、遭遇等，
    通过协调不同的逻辑组件和服务来完成复杂流程。
    """
    
    def __init__(self, metadata_repo: MetadataRepository, pokemon_factory: PokemonFactory):
        """
        初始化游戏逻辑协调器。
        
        Args:
            metadata_repo: 元数据仓库
            pokemon_factory: 宝可梦工厂
        """
        self._metadata_repo = metadata_repo
        self._pokemon_factory = pokemon_factory
        self._encounter_logic = EncounterLogic(metadata_repo)
        self._evolution_handler = EvolutionHandler(metadata_repo, pokemon_factory)
    
    async def process_movement(self, player: Player, direction: str) -> Dict[str, Any]:
        """
        处理玩家在地图上的移动。
        
        Args:
            player: 玩家对象
            direction: 移动方向（"north", "south", "east", "west"）
            
        Returns:
            包含移动结果的字典，如：
            {
                "success": True/False,
                "message": "移动成功/失败的消息",
                "encounter": 遭遇信息（如果发生遭遇）,
                "new_location": 新位置信息
            }
        """
        # 模拟移动逻辑
        # 实际实现需要检查地图边界、障碍物等
        # 此处为简化示例
        
        result = {
            "success": False,
            "message": "",
            "encounter": None,
            "new_location": None
        }
        
        # 获取当前位置
        current_location = player.current_location
        if not current_location:
            result["message"] = "玩家位置信息丢失"
            return result
        
        # 计算新位置（简化示例，实际需要考虑地图边界和障碍物）
        new_x, new_y = current_location.x, current_location.y
        
        if direction == "north":
            new_y -= 1
        elif direction == "south":
            new_y += 1
        elif direction == "east":
            new_x += 1
        elif direction == "west":
            new_x -= 1
        else:
            result["message"] = f"未知方向: {direction}"
            return result
        
        # 检查新位置是否有效
        # 此处应该检查地图边界和障碍物
        # 简化示例，假设0-999范围内均有效
        
        if 0 <= new_x < 1000 and 0 <= new_y < 1000:
            # 更新玩家位置
            player.current_location.x = new_x
            player.current_location.y = new_y
            
            result["success"] = True
            result["message"] = f"已移动到 ({new_x}, {new_y})"
            result["new_location"] = {"x": new_x, "y": new_y}
            
            # 检查是否触发野生宝可梦遭遇
            # 假设当前地图区域为玩家所在区域
            encounter_result = self._encounter_logic.check_wild_encounter(
                map_id=player.current_location.map_id,
                x=new_x,
                y=new_y,
                player_level=self._get_player_highest_pokemon_level(player)
            )
            
            if encounter_result["encounter"]:
                result["encounter"] = encounter_result
                result["message"] += f"。遇到了野生的{encounter_result['pokemon'].name}！"
        else:
            result["message"] = "无法移动到该位置（超出地图范围）"
        
        return result
    
    def _get_player_highest_pokemon_level(self, player: Player) -> int:
        """
        获取玩家宝可梦中的最高等级。
        
        Args:
            player: 玩家对象
            
        Returns:
            玩家宝可梦的最高等级，如果没有宝可梦则返回1
        """
        if not player.pokemon:
            return 1
        
        return max(pokemon.level for pokemon in player.pokemon)
    
    async def attempt_catch_pokemon(self, player: Player, target_pokemon: Pokemon, ball_type: str) -> Dict[str, Any]:
        """
        尝试捕捉宝可梦。
        
        Args:
            player: 尝试捕捉的玩家
            target_pokemon: 目标宝可梦
            ball_type: 使用的精灵球类型
            
        Returns:
            包含捕捉结果的字典，如：
            {
                "success": True/False,
                "message": "捕捉成功/失败的消息",
                "shake_count": 摇晃次数,
                "caught_pokemon": 如果成功，则包含捕获的宝可梦
            }
        """
        # 检查玩家是否有该类型的精灵球
        # 这部分逻辑会在service层处理，这里假设已经验证过
        
        result = {
            "success": False,
            "message": "",
            "shake_count": 0,
            "caught_pokemon": None
        }
        
        # 计算捕捉成功率和摇晃次数
        catch_result = calculate_catch_success(
            pokemon=target_pokemon,
            ball_type=ball_type,
            status_bonus=self._get_status_catch_bonus(target_pokemon)
        )
        
        result["shake_count"] = catch_result["shake_count"]
        
        if catch_result["success"]:
            # 捕捉成功
            result["success"] = True
            result["message"] = f"成功捕获了{target_pokemon.name}！"
            result["caught_pokemon"] = target_pokemon
            
            # 设置捕获者信息
            target_pokemon.original_trainer_id = player.player_id
            target_pokemon.nickname = target_pokemon.name  # 默认使用宝可梦的名称作为昵称
        else:
            # 捕捉失败
            result["message"] = f"{target_pokemon.name}挣脱了出来！"
        
        return result
    
    def _get_status_catch_bonus(self, pokemon: Pokemon) -> float:
        """
        根据宝可梦的状态效果计算捕捉加成。
        
        Args:
            pokemon: 目标宝可梦
            
        Returns:
            状态效果提供的捕捉加成倍率
        """
        if not pokemon.major_status:
            return 1.0
        
        # 不同状态提供不同的捕捉加成
        status_bonuses = {
            "sleep": 2.5,
            "frozen": 2.5,
            "paralysis": 1.5,
            "poison": 1.5,
            "burn": 1.5,
            "toxic": 1.5
        }
        
        return status_bonuses.get(pokemon.major_status.effect_logic_key, 1.0)

    async def _grant_experience_and_level_up(
        self, 
        pokemon: Pokemon, 
        exp_gained: int,
        battle_participants_count: int = 1 # 新增参数，用于经验分配
    ) -> List[Union[ExperienceGainedEvent, LevelUpEvent, EvolutionEvent, SkillLearnedEvent, BattleMessageEvent]]: # 添加 EvolutionEvent 到返回类型
        """
        给予宝可梦经验值并处理升级。
        现在也处理进化检查。
        """
        events = []
        if pokemon.current_hp <= 0: # 濒死的宝可梦不获得经验
            return events

        # 经验值调整 (例如，如果宝可梦等级远高于对手，经验减少 - 此处未实现)
        actual_exp_gained = exp_gained
        
        # 如果是交换来的宝可梦，经验值可能有加成 (例如 * 1.5)
        # if pokemon.is_traded:
        # actual_exp_gained = int(actual_exp_gained * 1.5)

        pokemon.current_exp += actual_exp_gained
        logger.info(f"{pokemon.nickname} 获得了 {actual_exp_gained} 点经验值。当前总经验: {pokemon.current_exp}")
        events.append(ExperienceGainedEvent(
            pokemon_id=pokemon.pokemon_id,
            exp_gained=actual_exp_gained,
            current_exp=pokemon.current_exp,
            exp_to_next_level=pokemon.exp_to_next_level() # 假设 Pokemon 模型有此方法
        ))

        leveled_up = False
        while pokemon.current_exp >= pokemon.exp_to_next_level() and pokemon.level < 100: # 等级上限100
            pokemon.current_exp -= pokemon.exp_to_next_level() # 减去升级所需经验
            old_level = pokemon.level
            pokemon.level += 1
            leveled_up = True
            logger.info(f"{pokemon.nickname} 等级提升! {old_level} -> {pokemon.level}")
            
            # 记录旧属性用于 LevelUpEvent
            old_stats = pokemon.stats.copy()
            
            pokemon.recalculate_stats() # 升级后重新计算属性
            
            # HP特殊处理：升级增加的HP会同时增加当前HP和最大HP
            hp_increase = pokemon.get_stat("hp") - old_stats.get("hp", pokemon.get_stat("hp"))
            if hp_increase > 0:
                pokemon.current_hp += hp_increase
            pokemon.current_hp = min(pokemon.current_hp, pokemon.get_stat("hp")) #确保不超过最大HP


            events.append(LevelUpEvent(
                pokemon_id=pokemon.pokemon_id,
                old_level=old_level,
                new_level=pokemon.level,
                old_stats=old_stats,
                new_stats=pokemon.stats.copy(),
                message=f"{pokemon.nickname} 等级提升到了 {pokemon.level}！"
            ))

            # 升级后立即检查进化
            if leveled_up: # 只有在实际升级后才检查进化
                evolution_event = await self._evolution_handler.check_and_process_evolution(pokemon)
                if evolution_event:
                    events.append(evolution_event)

                    logger.info(f"宝可梦 {pokemon.name} 进化完成，检查等级 {pokemon.level} 是否有可学习的技能。")
                    skills_learned_after_evolution = await self._check_learnable_skills(pokemon) # pokemon 对象已被修改为进化后的形态
                    if skills_learned_after_evolution:
                        events.extend(skills_learned_after_evolution)
                        logger.info(f"{pokemon.name} 在进化后学会了 {len(skills_learned_after_evolution)} 个新技能。")
                    pass # 宝可梦对象已被 EvolutionHandler 修改

        if not leveled_up and pokemon.level < 100: # 如果没有升级，但仍未满级
             logger.debug(f"{pokemon.nickname} 还需要 {pokemon.exp_to_next_level() - pokemon.current_exp} 点经验升级。")


        return events

    async def _check_learnable_skills(self, pokemon: Pokemon) -> List[Union[SkillLearnedEvent, BattleMessageEvent]]:
        """
        检查宝可梦是否能学习新技能。
        
        Args:
            pokemon: 目标宝可梦
            
        Returns:
            包含技能学习事件的列表
        """
        # 从元数据获取该宝可梦种族在当前等级及以下可以学习的所有技能
        # 注意：这里需要考虑宝可梦当前的 race_id
        learnset = await self._metadata_repo.get_learnset_for_pokemon_at_level(pokemon.race_id, pokemon.level)
        if not learnset:
            return []

        current_skill_ids = {skill.skill_id for skill in pokemon.skills}
        
        events = []
        for skill_data in learnset:
            # skill_data 应该是一个包含技能信息的字典，例如 {'skill_id': 1, 'name': '撞击', 'learn_level': 1, 'learn_method': 'level-up'}
            # 我们只关心通过 'level-up' 学习的技能
            if skill_data.get("learn_method") == "level-up" and skill_data.get("learn_level") == pokemon.level:
                skill_id_to_learn = skill_data["skill_id"]
                
                if skill_id_to_learn not in current_skill_ids:
                    skill_to_learn_obj = await self._metadata_repo.get_skill_by_id(skill_id_to_learn)
                    if skill_to_learn_obj:
                        # 尝试学习技能
                        # learn_skill 应该处理技能已满的情况 (返回 False 或抛出异常)
                        # 目前简化处理，直接添加，或者如果技能已满则跳过
                        if len(pokemon.skills) < 5: 
                            pokemon.skills.append(skill_to_learn_obj)
                            # 更新宝可梦的技能列表后，可能需要持久化。Service层会处理。
                            message = f"{pokemon.nickname} 学会了 {skill_to_learn_obj.name}！"
                            logger.info(message)
                            events.append(SkillLearnedEvent(
                                pokemon_id=pokemon.pokemon_id,
                                skill_id=skill_to_learn_obj.skill_id,
                                skill_name=skill_to_learn_obj.name,
                                message=message
                            ))
                            # 如果技能已满，需要有替换逻辑，目前跳过
                        else:
                            message = f"{pokemon.nickname} 想学习 {skill_to_learn_obj.name}，但技能已满！"
                            logger.info(message)
                            # 可以考虑为技能已满创建一个不同的事件或消息
                            events.append(BattleMessageEvent(message=message)) # 使用 BattleMessageEvent 临时提示
                    else:
                        logger.warning(f"无法找到技能 ID {skill_id_to_learn} 的数据，宝可梦 {pokemon.nickname} 无法学习。")
        return events

    async def _process_level_up_for_pokemon(self, pokemon: Pokemon, levels_gained: int) -> List[BattleEvent]:
        events: List[BattleEvent] = []
        original_level = pokemon.level - levels_gained
        # ... (省略了等级提升和属性重新计算的逻辑) ...

        # 检查是否有新技能学习
        # 假设 get_learnable_skills_at_level 返回的是技能ID列表
        # 并且元数据中技能是按推荐顺序排列的（如果一个等级能学多个）
        learnset = await self._metadata_repo.get_pokemon_learnset(pokemon.race_id)
        if learnset:
            for level_learned in range(original_level + 1, pokemon.level + 1):
                skills_to_learn_ids = learnset.get(str(level_learned), []) # learnset 的 key 可能是字符串
                
                for skill_id_to_learn in skills_to_learn_ids:
                    skill_to_learn_obj = await self._metadata_repo.get_skill_data(skill_id_to_learn)
                    if skill_to_learn_obj:
                        # 检查是否已经学会该技能
                        if any(s.skill_id == skill_to_learn_obj.skill_id for s in pokemon.skills):
                            logger.debug(f"{pokemon.nickname} 已经学会了 {skill_to_learn_obj.name}，跳过。")
                            continue

                        if len(pokemon.skills) < 4:
                            pokemon.skills.append(skill_to_learn_obj)
                            message = f"{pokemon.nickname} 学会了 {skill_to_learn_obj.name}！"
                            logger.info(message)
                            events.append(SkillLearnedEvent(
                                pokemon_id=pokemon.pokemon_id,
                                skill_id=skill_to_learn_obj.skill_id,
                                skill_name=skill_to_learn_obj.name,
                                message=message
                            ))
                        else:
                            # 技能已满，自动替换第一个技能
                            forgotten_skill = pokemon.skills.pop(0) # 移除第一个技能
                            
                            events.append(SkillForgottenEvent(
                                pokemon_id=pokemon.pokemon_id,
                                forgotten_skill_id=forgotten_skill.skill_id,
                                forgotten_skill_name=forgotten_skill.name,
                                message=f"{pokemon.nickname} 忘记了 {forgotten_skill.name}..."
                            ))
                            logger.info(f"{pokemon.nickname} 忘记了 {forgotten_skill.name} 以学习新技能。")

                            pokemon.skills.append(skill_to_learn_obj) # 添加新技能
                            message = f"...然后学会了 {skill_to_learn_obj.name}！"
                            logger.info(f"{pokemon.nickname} 学会了 {skill_to_learn_obj.name}。")
                            events.append(SkillLearnedEvent(
                                pokemon_id=pokemon.pokemon_id,
                                skill_id=skill_to_learn_obj.skill_id,
                                skill_name=skill_to_learn_obj.name,
                                message=message
                            ))
                    else:
                        logger.warning(f"无法找到技能 ID {skill_id_to_learn} 的数据，宝可梦 {pokemon.nickname} 无法学习。")
        return events

    async def process_time_based_events(self, player: Player) -> List[Dict[str, Any]]:
        """
        处理基于时间的事件，如宝可梦状态恢复、特殊事件触发等。
        
        Args:
            player: 玩家对象
            
        Returns:
            List[Dict[str, Any]]: 事件处理结果列表
        """
        events = []
        
        # 处理宝可梦状态恢复
        for pokemon_id in player.party_pokemon_ids:
            # 这里需要通过服务层获取宝可梦实例，这是一个示例逻辑
            # 实际实现需要在service层中调用此方法并传入完整的宝可梦对象
            # 或通过传递pokemon_repo让游戏逻辑层获取宝可梦对象
            pokemon = None  # 在实际实现中，这里会通过repo获取到宝可梦实例
            
            if pokemon and pokemon.status_effects:
                # 检查状态效果是否应该恢复
                for status in pokemon.status_effects[:]:  # 使用切片创建副本进行迭代
                    if status.is_time_based and status.should_recover():
                        recover_messages = pokemon.remove_status_effect(status.status_id)
                        events.append({
                            "type": "status_recovered",
                            "pokemon_instance_id": pokemon_id,
                            "status_name": status.name,
                            "messages": recover_messages
                        })
        
        # 处理特殊时间事件（如季节变化、节日活动等）
        # 这部分逻辑在实际游戏中根据需求实现
        
        return events

    async def check_evolution_eligibility(self, pokemon: Pokemon, trigger_type: str = "level_up", 
                                        item: Optional[Item] = None) -> Optional[Dict[str, Any]]:
        """
        检查宝可梦是否满足进化条件。
        
        Args:
            pokemon: 宝可梦对象
            trigger_type: 触发类型，如"level_up"、"trade"、"item"等
            item: 如果触发类型为"item"，则提供使用的道具
            
        Returns:
            Optional[Dict[str, Any]]: 如果满足进化条件，返回进化信息；否则返回None
        """
        # 使用进化处理器检查进化条件
        evolution_event = await self._evolution_handler.check_evolution_eligibility(
            pokemon, trigger_type, item
        )
        
        if evolution_event:
            return {
                "can_evolve": True,
                "pokemon_instance_id": pokemon.instance_id,
                "current_species_id": pokemon.race.race_id if pokemon.race else None,
                "evolution_species_id": evolution_event.evolution_species_id,
                "evolution_name": evolution_event.evolution_name,
                "trigger_type": trigger_type
            }
        
        return None

    async def handle_skill_learning(self, pokemon: Pokemon, level: int) -> List[Dict[str, Any]]:
        """
        处理宝可梦在特定等级可能学习的技能。
        
        Args:
            pokemon: 宝可梦对象
            level: 当前等级
            
        Returns:
            List[Dict[str, Any]]: 技能学习相关事件列表
        """
        events = []
        
        # 获取该宝可梦种族在当前等级可学习的技能
        if not pokemon.race:
            logger.warning(f"无法处理技能学习：宝可梦 {pokemon.nickname} 缺少种族信息")
            return []
        
        learnable_skills = await self._metadata_repo.get_skills_learnable_at_level(
            pokemon.race.race_id, level
        )
        
        for skill_data in learnable_skills:
            skill_id = skill_data.get("skill_id")
            skill_name = skill_data.get("name", "未知技能")
            
            # 检查宝可梦是否已经有这个技能
            if any(s.skill_id == skill_id for s in pokemon.skills):
                logger.debug(f"宝可梦 {pokemon.nickname} 已经学会了技能 {skill_name}")
                continue
            
            # 检查技能槽位
            if len(pokemon.skills) < 4:
                # 直接学习技能
                skill = await self._metadata_repo.get_skill(skill_id)
                if skill:
                    pokemon.skills.append(skill)
                    events.append({
                        "type": "skill_learned",
                        "pokemon_instance_id": pokemon.instance_id,
                        "pokemon_name": pokemon.nickname,
                        "skill_id": skill_id,
                        "skill_name": skill_name,
                        "message": f"{pokemon.nickname} 学会了 {skill_name}！"
                    })
            else:
                # 需要替换技能，创建一个需要玩家决定的事件
                current_skills = [
                    {"skill_id": s.skill_id, "name": s.name, "pp": s.max_pp, "description": s.description}
                    for s in pokemon.skills
                ]
                
                events.append({
                    "type": "skill_replacement_required",
                    "pokemon_instance_id": pokemon.instance_id,
                    "pokemon_name": pokemon.nickname,
                    "new_skill_id": skill_id,
                    "new_skill_name": skill_name,
                    "current_skills": current_skills,
                    "message": f"{pokemon.nickname} 想学习 {skill_name}，但已经学会了4个技能。请选择要忘记的技能。"
                })
        
        return events
