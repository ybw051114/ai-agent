"""
插件系统的基础接口定义。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

class BasePlugin(ABC):
    """插件基础类。
    
    所有插件都需要继承这个基类，并根据需要实现相应的方法。
    插件可以在AI处理前后对输入输出进行处理。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化插件。
        
        Args:
            config: 可选的配置字典，包含插件特定的配置项
        """
        self.config = config or {}
        
    def pre_process(self, input_text: str) -> str:
        """
        在AI处理之前对输入进行预处理。
        
        Args:
            input_text: 用户输入的原始文本
            
        Returns:
            str: 处理后的文本
        """
        return input_text
        
    def post_process(self, output_text: str) -> str:
        """
        在AI处理之后对输出进行后处理。
        
        Args:
            output_text: AI生成的原始回答
            
        Returns:
            str: 处理后的文本
        """
        return output_text
    
    @property
    def priority(self) -> int:
        """
        插件的优先级，决定了插件的执行顺序。
        
        Returns:
            int: 优先级值，数值越小优先级越高
        """
        return 100
    
    def validate_config(self) -> bool:
        """
        验证插件配置是否有效。
        
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        return True

class PluginError(Exception):
    """插件相关的异常类。"""
    
    def __init__(self, message: str, plugin_name: str):
        """
        初始化异常。
        
        Args:
            message: 错误信息
            plugin_name: 发生错误的插件名称
        """
        self.plugin_name = plugin_name
        super().__init__(f"[{plugin_name}] {message}")

class PluginManager:
    """插件管理器，负责插件的注册和执行。"""
    
    def __init__(self):
        """初始化插件管理器。"""
        self._plugins: Dict[str, BasePlugin] = {}
        
    def register(self, name: str, plugin: BasePlugin) -> None:
        """
        注册一个新插件。
        
        Args:
            name: 插件名称
            plugin: 插件实例
            
        Raises:
            ValueError: 当插件名已存在时抛出
        """
        if name in self._plugins:
            raise ValueError(f"Plugin {name} already registered")
        self._plugins[name] = plugin
        
    def unregister(self, name: str) -> None:
        """
        注销一个插件。
        
        Args:
            name: 插件名称
            
        Raises:
            KeyError: 当插件不存在时抛出
        """
        if name not in self._plugins:
            raise KeyError(f"Plugin {name} not found")
        del self._plugins[name]
        
    def get_plugin(self, name: str) -> BasePlugin:
        """
        获取指定名称的插件。
        
        Args:
            name: 插件名称
            
        Returns:
            BasePlugin: 插件实例
            
        Raises:
            KeyError: 当插件不存在时抛出
        """
        if name not in self._plugins:
            raise KeyError(f"Plugin {name} not found")
        return self._plugins[name]
        
    def list_plugins(self) -> Dict[str, BasePlugin]:
        """
        获取所有已注册的插件。
        
        Returns:
            Dict[str, BasePlugin]: 插件名称到插件实例的映射
        """
        return dict(self._plugins)

def register_plugin(name: str):
    """
    插件注册装饰器。
    
    Args:
        name: 插件名称
        
    Returns:
        装饰器函数
    """
    def decorator(cls):
        if not issubclass(cls, BasePlugin):
            raise TypeError(f"Class {cls.__name__} must inherit from BasePlugin")
        cls.plugin_name = name
        return cls
    return decorator
