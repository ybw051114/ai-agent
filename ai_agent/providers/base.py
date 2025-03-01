"""
AI提供商的基础接口定义。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseProvider(ABC):
    """AI提供商的基础接口类。
    
    所有的AI提供商实现都需要继承这个基类，并实现其抽象方法。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化AI提供商。
        
        Args:
            config: 可选的配置字典，包含provider特定的配置项
        """
        self.config = config or {}

    @abstractmethod
    async def generate_response(self, prompt: str, conversation: Optional[List[Dict]] = None) -> str:
        """
        生成对问题的回答。
        
        Args:
            prompt: 输入的问题或提示
            conversation: 可选的历史对话记录
            
        Returns:
            str: AI生成的回答
            
        Raises:
            ProviderError: 当调用AI服务出错时抛出
        """
        pass

    @abstractmethod
    async def stream_response(self, prompt: str, conversation: Optional[List[Dict]] = None):
        """
        流式生成回答。
        
        Args:
            prompt: 输入的问题或提示
            conversation: 可选的历史对话记录
            
        Yields:
            str: AI生成的部分回答
            
        Raises:
            ProviderError: 当调用AI服务出错时抛出
        """
        pass
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效。
        
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        return True


class ProviderError(Exception):
    """AI提供商相关的异常类。"""
    
    def __init__(self, message: str, provider_name: str):
        """
        初始化异常。
        
        Args:
            message: 错误信息
            provider_name: 发生错误的提供商名称
        """
        self.provider_name = provider_name
        super().__init__(f"[{provider_name}] {message}")


def register_provider(name: str):
    """
    提供商注册装饰器。
    
    Args:
        name: 提供商名称
        
    Returns:
        装饰器函数
    """
    def decorator(cls):
        if not issubclass(cls, BaseProvider):
            raise TypeError(f"Class {cls.__name__} must inherit from BaseProvider")
        cls.provider_name = name
        return cls
    return decorator
