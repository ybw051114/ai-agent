"""
对话保存输出处理器。
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseOutput, register_output

@register_output("conversation")
class ConversationOutput(BaseOutput):
    """对话保存输出处理器，将对话内容保存为Markdown文件。"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化对话保存输出处理器。
        
        Args:
            config: 配置字典，包含save_dir和timestamp_format等配置项
        """
        super().__init__(config)
        self.save_dir = os.path.expanduser(self.config.get("save_dir", "~/ai-agent/conversations"))
        self.timestamp_format = self.config.get("timestamp_format", "%Y-%m-%d %H:%M:%S")
        self.conversation: List[Dict[str, str]] = []
        self.start_time = datetime.now()
        
    async def render(self, content: str) -> None:
        """
        渲染并保存对话内容。
        
        Args:
            content: 对话内容
        """
        # 获取用户输入
        if not self.conversation or self.conversation[-1]["role"] == "assistant":
            self._add_message("user", content)
        else:
            # AI回答
            if self.conversation[-1]["role"] == "system":
                # 这是主题的回答
                self._save_conversation(content.strip())
                self.conversation = []  # 重置对话记录
                self.start_time = datetime.now()  # 重置开始时间
            else:
                # 普通回答，检查是否需要触发主题生成
                self._add_message("assistant", content)
                if content.strip().endswith(("。", "?", "!", ".", "！", "？")):
                    # 对话可能结束，添加主题生成提示
                    self._add_message("system", "你是一个专业人士，你觉得这次交流主题是什么，请用10个字以内概括")
    
    async def render_stream(self, content_stream) -> None:
        """
        流式渲染对话内容。
        
        Args:
            content_stream: 内容流
        """
        # 收集所有chunks
        chunks = []
        async for chunk in content_stream:
            chunks.append(chunk)
        
        # 合并为完整消息
        complete_message = "".join(chunks).strip()
        
        # 根据上下文决定消息处理方式
        if self.conversation and self.conversation[-1]["role"] == "system":
            # 这是对主题生成的回答，保存对话并重置
            self._save_conversation(complete_message)
            self.conversation = []
            self.start_time = datetime.now()
        else:
            # 普通消息处理
            if not self.conversation or self.conversation[-1]["role"] == "assistant":
                self._add_message("user", complete_message)
            else:
                self._add_message("assistant", complete_message)
                # 检查是否需要生成主题
                if complete_message.endswith(("。", ".", "!", "?", "！", "？")):
                    self._add_message("system", "你是一个专业人士，你觉得这次交流主题是什么，请用10个字以内概括")
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效。
        
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        return True

    def _add_message(self, role: str, content: str) -> None:
        """
        添加一条对话消息。
        
        Args:
            role: 消息角色（user/assistant/system）
            content: 消息内容
        """
        self.conversation.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime(self.timestamp_format)
        })
    
    def _save_conversation(self, topic: str) -> None:
        """
        将对话保存为Markdown文件。
        
        Args:
            topic: 对话主题
        """
        if not self.conversation or len(self.conversation) < 3:  # 至少需要一问一答加主题生成提示
            return
        
        # 过滤出实际对话内容，排除主题生成提示
        filtered_conversation = []
        for msg in self.conversation[:-1]:  # 排除最后的主题生成提示
            if msg["role"] != "system":  # 排除系统消息
                filtered_conversation.append(msg)
        
        # 创建保存目录
        save_dir = Path(self.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_name = f"{topic}_{date_str}.md"
        file_path = save_dir / file_name
        
        # 生成Markdown内容
        content = [
            f"# {topic}",
            f"开始时间：{self.start_time.strftime(self.timestamp_format)}",
            f"结束时间：{datetime.now().strftime(self.timestamp_format)}",
            "",
            "## 对话内容",
            ""
        ]
        
        # 添加对话记录
        for msg in filtered_conversation:
            role_name = "用户" if msg["role"] == "user" else "助手"
            content.append(f"{msg['timestamp']} **{role_name}**: {msg['content']}")
        
        # 保存文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
