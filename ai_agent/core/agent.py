"""
AI代理的核心实现。
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncGenerator

from ..output.base import BaseOutput, OutputManager
from ..plugins.base import BasePlugin, PluginManager
from ..providers.base import BaseProvider, ProviderError

class Agent:
    """AI代理核心类，负责协调各个组件的工作。"""
    
    def __init__(
        self,
        provider: BaseProvider,
        plugin_manager: Optional[PluginManager] = None,
        output_manager: Optional[OutputManager] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化AI代理。
        
        Args:
            provider: AI提供商实例
            plugin_manager: 插件管理器实例
            output_manager: 输出管理器实例
            config: 配置字典
        """
        self.provider = provider
        self.plugin_manager = plugin_manager or PluginManager()
        self.output_manager = output_manager or OutputManager()
        self.config = config or {}
        self.conversation = []  # 用于保存对话历史
        self.start_time = datetime.now()  # 会话开始时间
        self.summary = None  # 对话总结
        
    async def process(self, input_text: str, output_name: Optional[str] = None) -> str:
        """
        处理输入并生成回答。
        
        Args:
            input_text: 用户输入的文本
            output_name: 指定使用的输出处理器名称
        """
        # 1. 应用所有插件的预处理
        processed_input = self._apply_pre_process(input_text)
        
        try:
            # 2. 调用AI提供商生成回答（使用当前历史）
            response = await self.provider.generate_response(processed_input, self.conversation)
            
            # 3. 更新对话历史
            self.conversation.append({"role": "user", "content": processed_input})
            
            # 3. 应用所有插件的后处理
            processed_output = self._apply_post_process(response)
            self.conversation.append({"role": "assistant", "content": processed_output})
            
            # 4. 输出结果
            outputs = []
            if isinstance(self.config.get("output"), list):
                outputs = [self.output_manager.get_output(name) for name in self.config["output"]]
            else:
                outputs = [self.output_manager.get_output(output_name)]
            
            for output in outputs:
                await output.render(processed_output)
            
            return processed_output
            
        except Exception as e:
            # 处理错误并通过当前输出处理器显示
            error_message = f"处理失败: {str(e)}"
            output = self.output_manager.get_output(output_name)
            await output.render(error_message)
            raise
    
    async def process_stream(
        self,
        input_text: str,
        output_name: Optional[str] = None
    ) -> str:
        """
        流式处理输入并生成回答。
        
        Args:
            input_text: 用户输入的文本
            output_name: 指定使用的输出处理器名称
            
        Returns:
            str: 处理后的完整响应文本
        """
        # 1. 应用所有插件的预处理
        processed_input = self._apply_pre_process(input_text)

        try:
            # 2. 获取所有输出处理器
            outputs = []
            if isinstance(self.config.get("output"), list):
                outputs = [self.output_manager.get_output(name) for name in self.config["output"]]
            else:
                outputs = [self.output_manager.get_output(output_name)]
            
            # 3. 流式生成并处理回答（使用当前历史）
            response_stream = self.provider.stream_response(processed_input, self.conversation)
            
            # 4. 流式输出并收集完整文本
            text_parts = []
            chunks = []
            
            # 更新对话历史
            self.conversation.append({"role": "user", "content": processed_input})
            
            # 复制流内容以供后续使用
            async for chunk in response_stream:
                text_parts.append(chunk)
                chunks.append(chunk)
            
            # 创建独立的流生成器
            async def create_stream():
                for chunk in chunks:
                    await asyncio.sleep(0.01)  # 模拟真实流式传输
                    yield chunk
            
            # 为每个输出处理器创建独立的流
            stream_tasks = []
            for output in outputs:
                stream = create_stream()
                task = asyncio.create_task(output.render_stream(stream))
                stream_tasks.append(task)
            
            # 等待所有输出处理完成
            await asyncio.gather(*stream_tasks)

            # 返回完整响应文本并更新对话历史
            final_text = "".join(text_parts).strip()
            self.conversation.append({"role": "assistant", "content": final_text})
            
            return final_text
            
        except Exception as e:
            # 处理错误并通过当前输出处理器显示
            error_message = f"处理失败: {str(e)}"
            output = self.output_manager.get_output(output_name)
            await output.render(error_message)
            raise
            
    async def _chunk_to_stream(self, text: str) -> AsyncGenerator[str, None]:
        """
        将文本转换为流式输出。
        
        Args:
            text: 要输出的文本
            
        Yields:
            str: 每个输出片段
        """
        # 按空格或标点分割文本
        buffer = ""
        for char in text:
            buffer += char
            if char in (" ", "\n", ".", "!", "?"):
                yield buffer
                buffer = ""
        if buffer:  # 输出剩余内容
            yield buffer
    
    def _apply_pre_process(self, input_text: str) -> str:
        """
        应用所有插件的预处理。
        
        Args:
            input_text: 原始输入文本
            
        Returns:
            str: 处理后的文本
        """
        current_text = input_text
        for plugin in self._get_sorted_plugins():
            try:
                current_text = plugin.pre_process(current_text)
            except Exception as e:
                # 记录错误但继续处理
                print(f"插件 {plugin.__class__.__name__} 预处理失败: {e}")
        return current_text
    
    def _apply_post_process(self, output_text: str) -> str:
        """
        应用所有插件的后处理。
        
        Args:
            output_text: AI生成的原始回答
            
        Returns:
            str: 处理后的文本
        """
        current_text = output_text
        for plugin in self._get_sorted_plugins():
            try:
                current_text = plugin.post_process(current_text)
            except Exception as e:
                # 记录错误但继续处理
                print(f"插件 {plugin.__class__.__name__} 后处理失败: {e}")
        return current_text
    
    def _get_sorted_plugins(self) -> List[BasePlugin]:
        """
        获取按优先级排序的插件列表。
        
        Returns:
            List[BasePlugin]: 排序后的插件列表
        """
        plugins = list(self.plugin_manager.list_plugins().values())
        return sorted(plugins, key=lambda x: x.priority)
    
    def add_plugin(self, plugin: BasePlugin) -> None:
        """
        添加一个新插件。
        
        Args:
            plugin: 插件实例
        """
        self.plugin_manager.register(plugin.__class__.__name__, plugin)
    
    def add_output(self, output: BaseOutput, name: Optional[str] = None,
                  default: bool = False) -> None:
        """
        添加一个新的输出处理器。
        
        Args:
            output: 输出处理器实例
            name: 输出处理器名称
            default: 是否设为默认输出处理器
        """
        name = name or output.__class__.__name__
        self.output_manager.register(name, output, default)

    async def _generate_summary(self) -> str:
        """生成对话总结。"""
        if not self.conversation:
            return "空对话"
            
        # 构建总结提示
        prompt = "请用一句话总结这个对话的主题以作为标题（10字以内）："
            
        try:
            # 获取流式响应并收集所有文本
            response_stream = self.provider.stream_response(prompt, self.conversation)
            text_parts = []
            async for chunk in response_stream:
                text_parts.append(chunk)
                
            # 合并所有文本并保存
            self.summary = "".join(text_parts).strip()
            return self.summary
        except Exception as e:
            print(f"生成总结失败：{e}")
            return "未总结对话"

    def _save_conversation(self) -> str:
        """保存对话历史到文件。"""
        if not self.conversation:
            return
            
        # 创建保存目录
        save_dir = os.path.expanduser("~/ai-agent/conversations")
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件名
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        summary = self.summary or "未总结对话"
        file_name = f"{summary}_{date_str}.md"
        file_path = os.path.join(save_dir, file_name)
        
        # 生成Markdown内容
        content = [
            f"# {summary}",
            f"开始时间：{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 对话内容",
            ""
        ]
        
        # 添加对话记录
        for msg in self.conversation:
            role_name = "用户" if msg["role"] == "user" else "助手"
            content.append(f"**{role_name}**: {msg['content']}\n")
        
        # 保存文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        
        return file_path

class AgentBuilder:
    """AI代理构建器，用于简化Agent实例的创建过程。"""
    
    def __init__(self):
        """初始化构建器。"""
        self.provider: Optional[BaseProvider] = None
        self.plugin_manager = PluginManager()
        self.output_manager = OutputManager()
        self.config: Dict[str, Any] = {}
    
    def with_provider(self, provider: BaseProvider) -> 'AgentBuilder':
        """
        设置AI提供商。
        
        Args:
            provider: AI提供商实例
            
        Returns:
            AgentBuilder: 构建器实例
        """
        self.provider = provider
        return self
    
    def with_plugin(self, plugin: BasePlugin) -> 'AgentBuilder':
        """
        添加插件。
        
        Args:
            plugin: 插件实例
            
        Returns:
            AgentBuilder: 构建器实例
        """
        self.plugin_manager.register(plugin.__class__.__name__, plugin)
        return self
    
    def with_output(self, output: BaseOutput, name: Optional[str] = None,
                   default: bool = False) -> 'AgentBuilder':
        """
        添加输出处理器。
        
        Args:
            output: 输出处理器实例
            name: 输出处理器名称
            default: 是否设为默认输出处理器
            
        Returns:
            AgentBuilder: 构建器实例
        """
        name = name or output.__class__.__name__
        self.output_manager.register(name, output, default)
        return self
    
    def with_config(self, config: Dict[str, Any]) -> 'AgentBuilder':
        """
        设置配置。
        
        Args:
            config: 配置字典
            
        Returns:
            AgentBuilder: 构建器实例
        """
        self.config.update(config)
        return self
    
    def build(self) -> Agent:
        """
        构建Agent实例。
        
        Returns:
            Agent: 构建的Agent实例
            
        Raises:
            ValueError: 当必需的组件未设置时抛出
        """
        if not self.provider:
            raise ValueError("必须设置AI提供商")
        
        return Agent(
            provider=self.provider,
            plugin_manager=self.plugin_manager,
            output_manager=self.output_manager,
            config=self.config
        )
