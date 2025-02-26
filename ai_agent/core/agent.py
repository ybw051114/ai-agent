"""
AI代理的核心实现。
"""
from typing import Any, Dict, List, Optional, Type

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
            # 2. 调用AI提供商生成回答
            response = await self.provider.generate_response(processed_input)
            
            # 3. 应用所有插件的后处理
            processed_output = self._apply_post_process(response)
            
            # 4. 输出结果
            output = self.output_manager.get_output(output_name)
            output.render(processed_output)
            
            return processed_output
            
        except Exception as e:
            # 处理错误并通过当前输出处理器显示
            error_message = f"处理失败: {str(e)}"
            self.output_manager.get_output(output_name).render(error_message)
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
        """
        # 1. 应用所有插件的预处理
        processed_input = self._apply_pre_process(input_text)

        
        try:
            # 2. 获取输出处理器
            output = self.output_manager.get_output(output_name)
            
            # 3. 流式生成并处理回答
            response_stream = self.provider.stream_response(processed_input)
            
            # 4. 流式输出并收集完整文本
            final_text = ""
            buffer = []
            async for chunk in response_stream:
                final_text += chunk
                buffer.append(chunk)
                if chunk.endswith((" ", "\n", ".", "!", "?")):
                    output.render("".join(buffer))
                    buffer = []
            
            # 输出剩余内容
            if buffer:
                output.render("".join(buffer))
                
            return final_text
            
        except Exception as e:
            # 处理错误并通过当前输出处理器显示
            error_message = f"处理失败: {str(e)}"
            self.output_manager.get_output(output_name).render(error_message)
            raise
    
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
