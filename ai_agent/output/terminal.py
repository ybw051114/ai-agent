"""
终端输出处理器实现。
"""
import asyncio
from typing import Any, Dict, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style
from rich.syntax import Syntax

from .base import BaseOutput, register_output

@register_output("terminal")
class TerminalOutput(BaseOutput):
    """终端输出处理器，使用rich库实现富文本显示。"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化终端输出处理器。
        
        Args:
            config: 配置字典，可以包含以下选项：
                - color_system: 颜色系统 (例如 "auto", "standard", "256", "truecolor")
                - width: 输出宽度
                - style: 样式配置
        """
        super().__init__(config)
        self.console = Console(**config if config else {})
        self.default_style = Style(color="cyan")
        
    def render(self, content: str) -> None:
        """
        渲染内容到终端。
        
        支持自动检测并格式化Markdown和代码块。
        
        Args:
            content: 要输出的内容
        """
        # 检测内容是否为Markdown格式
        if self._is_markdown(content):
            # 渲染Markdown
            markdown = Markdown(content)
            self.console.print(Panel(markdown, border_style="blue"))
        else:
            # 检测是否包含代码块
            if "```" in content:
                parts = self._split_code_blocks(content)
                for part in parts:
                    if part.startswith("```") and part.endswith("```"):
                        # 提取语言和代码
                        lines = part.split("\n")
                        lang = lines[0][3:].strip() or "text"
                        code = "\n".join(lines[1:-1])
                        # 渲染代码块
                        syntax = Syntax(code, lang, theme="monokai")
                        self.console.print(Panel(syntax, border_style="green"))
                    else:
                        self.console.print(part, style=self.default_style)
            else:
                # 普通文本
                self.console.print(content, style=self.default_style)
    
    async def render_stream(self, content_stream) -> None:
        """
        流式渲染内容到终端。
        
        Args:
            content_stream: 内容流迭代器
        """
        buffer = ""
        async for chunk in content_stream:
            # 如果接收到完整的代码块标记，先输出之前的内容
            if "```" in chunk:
                if buffer:
                    self.console.print(buffer, style=self.default_style, end="")
                    buffer = ""
                self.console.print(chunk, style=self.default_style, end="")
            else:
                # 累积普通文本
                buffer += chunk
                # 在完整的单词处输出
                if buffer.endswith((" ", "\n", ".", "!", "?")):
                    self.console.print(buffer, style=self.default_style, end="")
                    buffer = ""
            
            # 确保内容立即显示
            self.console.flush()
            
            # 添加小延迟以实现流畅的打印效果
            await asyncio.sleep(0.01)
            
        # 输出剩余的缓冲内容
        if buffer:
            self.console.print(buffer, style=self.default_style)
    
    def _is_markdown(self, content: str) -> bool:
        """
        检查内容是否为Markdown格式。
        
        Args:
            content: 要检查的内容
            
        Returns:
            bool: 是否为Markdown格式
        """
        markdown_indicators = [
            "##",  # 标题
            "*",   # 强调或列表
            "_",   # 强调
            "`",   # 代码
            ">",   # 引用
            "-",   # 列表或分隔线
            "[",   # 链接
            "!["   # 图片
        ]
        return any(indicator in content for indicator in markdown_indicators)
    
    def _split_code_blocks(self, content: str) -> list:
        """
        将内容分割为代码块和普通文本。
        
        Args:
            content: 要分割的内容
            
        Returns:
            list: 分割后的内容列表
        """
        parts = []
        current = []
        in_code_block = False
        
        for line in content.split("\n"):
            if line.startswith("```"):
                if in_code_block:
                    current.append(line)
                    parts.append("\n".join(current))
                    current = []
                else:
                    if current:
                        parts.append("\n".join(current))
                        current = []
                    current.append(line)
                in_code_block = not in_code_block
            else:
                current.append(line)
        
        if current:
            parts.append("\n".join(current))
            
        return parts
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效。
        
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        if self.config:
            valid_color_systems = {"auto", "standard", "256", "truecolor", None}
            if "color_system" in self.config:
                print(self.config["color_system"])
                if self.config["color_system"] not in valid_color_systems:
                    return False
                
            if "width" in self.config:
                if not isinstance(self.config["width"], (int, type(None))):
                    return False
                
        return True
