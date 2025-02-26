"""
输出处理的基础接口定义。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseOutput(ABC):
    """输出处理的基础接口类。
    
    所有输出处理器都需要继承这个基类，并实现其抽象方法。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化输出处理器。
        
        Args:
            config: 可选的配置字典，包含输出处理器特定的配置项
        """
        self.config = config or {}
    
    @abstractmethod
    def render(self, content: str) -> None:
        """
        渲染内容。
        
        Args:
            content: 要输出的内容
        """
        pass
    
    @abstractmethod
    async def render_stream(self, content_stream) -> None:
        """
        流式渲染内容。
        
        Args:
            content_stream: 要输出的内容流
        """
        pass
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效。
        
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        return True

class OutputManager:
    """输出管理器，负责管理和协调不同的输出处理器。"""
    
    def __init__(self):
        """初始化输出管理器。"""
        self._outputs: Dict[str, BaseOutput] = {}
        self._default_output: Optional[str] = None
    
    def register(self, name: str, output: BaseOutput, default: bool = False) -> None:
        """
        注册一个新的输出处理器。
        
        Args:
            name: 输出处理器名称
            output: 输出处理器实例
            default: 是否设为默认输出处理器
            
        Raises:
            ValueError: 当输出处理器名称已存在时抛出
        """
        if name in self._outputs:
            raise ValueError(f"Output {name} already registered")
        
        self._outputs[name] = output
        if default or self._default_output is None:
            self._default_output = name
    
    def unregister(self, name: str) -> None:
        """
        注销一个输出处理器。
        
        Args:
            name: 输出处理器名称
            
        Raises:
            KeyError: 当输出处理器不存在时抛出
            ValueError: 当尝试注销默认输出处理器时抛出
        """
        if name not in self._outputs:
            raise KeyError(f"Output {name} not found")
        if name == self._default_output:
            raise ValueError("Cannot unregister default output")
        del self._outputs[name]
    
    def get_output(self, name: Optional[str] = None) -> BaseOutput:
        """
        获取指定名称的输出处理器。
        
        Args:
            name: 输出处理器名称，如果为None则返回默认输出处理器
            
        Returns:
            BaseOutput: 输出处理器实例
            
        Raises:
            KeyError: 当输出处理器不存在时抛出
        """
        output_name = name or self._default_output
        if not output_name or output_name not in self._outputs:
            raise KeyError(f"Output {output_name} not found")
        return self._outputs[output_name]
    
    def set_default(self, name: str) -> None:
        """
        设置默认输出处理器。
        
        Args:
            name: 输出处理器名称
            
        Raises:
            KeyError: 当输出处理器不存在时抛出
        """
        if name not in self._outputs:
            raise KeyError(f"Output {name} not found")
        self._default_output = name

class OutputError(Exception):
    """输出处理相关的异常类。"""
    
    def __init__(self, message: str, output_name: str):
        """
        初始化异常。
        
        Args:
            message: 错误信息
            output_name: 发生错误的输出处理器名称
        """
        self.output_name = output_name
        super().__init__(f"[{output_name}] {message}")

def register_output(name: str):
    """
    输出处理器注册装饰器。
    
    Args:
        name: 输出处理器名称
        
    Returns:
        装饰器函数
    """
    def decorator(cls):
        if not issubclass(cls, BaseOutput):
            raise TypeError(f"Class {cls.__name__} must inherit from BaseOutput")
        cls.output_name = name
        return cls
    return decorator
