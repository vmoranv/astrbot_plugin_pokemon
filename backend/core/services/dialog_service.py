from typing import Dict, List, Optional, Any
from backend.models.dialog import Dialog, DialogOption
from backend.models.npc import NPC
from backend.data_access.repositories.dialog_repository import DialogRepository
from backend.data_access.repositories.metadata_repository import MetadataRepository
from backend.utils.exceptions import DialogNotFoundException, NPCNotFoundException
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class DialogService:
    """对话服务，处理NPC对话和对话选项"""
    
    def __init__(self):
        self.dialog_repo = DialogRepository()
        self.metadata_repo = MetadataRepository()
        
    async def get_dialog(self, dialog_id: int) -> Dialog:
        """
        获取指定ID的对话
        
        Args:
            dialog_id: 对话ID
            
        Returns:
            对话对象
            
        Raises:
            DialogNotFoundException: 如果对话不存在
        """
        dialog = await self.dialog_repo.get_dialog(dialog_id)
        if not dialog:
            raise DialogNotFoundException(f"对话ID {dialog_id} 不存在")
        return dialog
        
    async def get_npc_dialog(self, npc_id: int, player_id: str) -> Dict[str, Any]:
        """
        获取与NPC的对话，基于玩家的状态可能返回不同的对话
        
        Args:
            npc_id: NPC的ID
            player_id: 玩家ID，用于确定对话进度和状态
            
        Returns:
            包含对话内容和选项的字典
            
        Raises:
            NPCNotFoundException: 如果NPC不存在
        """
        # 获取NPC数据
        npc = await self.metadata_repo.get_npc(npc_id)
        if not npc:
            raise NPCNotFoundException(f"NPC ID {npc_id} 不存在")
            
        # 获取玩家与该NPC的对话状态
        dialog_state = await self.dialog_repo.get_player_npc_dialog_state(player_id, npc_id)
        
        # 确定当前对话ID
        current_dialog_id = dialog_state.get('current_dialog_id') if dialog_state else npc.default_dialog_id
        
        # 获取当前对话
        try:
            dialog = await self.get_dialog(current_dialog_id)
        except DialogNotFoundException:
            # 如果当前对话不存在，使用默认对话
            dialog = await self.get_dialog(npc.default_dialog_id)
            
        # 处理动态对话内容（例如，替换玩家名称等）
        processed_text = self._process_dialog_text(dialog.text, player_id)
        
        # 处理对话选项
        options = await self._process_dialog_options(dialog.options, player_id, npc_id)
        
        return {
            "npc_id": npc_id,
            "npc_name": npc.name,
            "dialog_id": dialog.dialog_id,
            "text": processed_text,
            "options": options
        }
        
    async def select_dialog_option(self, dialog_id: int, option_id: int, player_id: str) -> Dict[str, Any]:
        """
        选择对话选项，返回下一个对话或执行相应动作
        
        Args:
            dialog_id: 当前对话ID
            option_id: 选择的选项ID
            player_id: 玩家ID
            
        Returns:
            下一个对话或动作结果
            
        Raises:
            DialogNotFoundException: 如果对话不存在
        """
        # 获取当前对话
        dialog = await self.get_dialog(dialog_id)
        
        # 找到选择的选项
        selected_option = None
        for option in dialog.options:
            if option.option_id == option_id:
                selected_option = option
                break
                
        if not selected_option:
            raise ValueError(f"选项ID {option_id} 在对话 {dialog_id} 中不存在")
            
        # 更新对话状态
        await self.dialog_repo.update_player_dialog_state(player_id, dialog_id, option_id)
        
        # 处理选项结果
        result = {}
        
        # 如果选项指向另一个对话
        if selected_option.next_dialog_id:
            next_dialog = await self.get_dialog(selected_option.next_dialog_id)
            result = {
                "type": "dialog",
                "dialog_id": next_dialog.dialog_id,
                "text": self._process_dialog_text(next_dialog.text, player_id),
                "options": await self._process_dialog_options(next_dialog.options, player_id)
            }
            
        # 如果选项触发事件或动作
        elif selected_option.action:
            result = {
                "type": "action",
                "action": selected_option.action,
                "params": selected_option.action_params
            }
            
        return result
        
    def _process_dialog_text(self, text: str, player_id: str) -> str:
        """处理对话文本，替换变量等"""
        # 这里可以实现变量替换，例如 {player_name} 替换为玩家名称
        # 简化版本，实际实现可能需要从数据库获取更多信息
        return text
        
    async def _process_dialog_options(self, options: List[DialogOption], player_id: str, npc_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """处理对话选项，根据玩家状态过滤选项"""
        # 简化版本，实际实现可能需要检查条件等
        processed_options = []
        
        for option in options:
            # 检查是否满足条件显示选项
            if self._check_option_condition(option, player_id):
                processed_options.append({
                    "option_id": option.option_id,
                    "text": option.text
                })
                
        return processed_options
        
    def _check_option_condition(self, option: DialogOption, player_id: str) -> bool:
        """检查对话选项条件"""
        # 简化版本，实际实现可能需要检查任务状态、物品拥有情况等
        return True
