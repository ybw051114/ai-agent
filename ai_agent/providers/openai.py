"""
OpenAI提供商实现。
"""
import asyncio
from typing import Any, AsyncGenerator, Dict, Optional

from openai import AsyncOpenAI, APIError
import aiohttp

from .base import BaseProvider, ProviderError, register_provider

@register_provider("openai")
class OpenAIProvider(BaseProvider):
    """OpenAI API提供商实现。"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化OpenAI提供商。
        
        Args:
            config: 配置字典，必须包含：
                - api_key: OpenAI API密钥
                可选包含：
                - model: 模型名称
                - temperature: 温度参数
                - max_tokens: 最大token数
                - stream: 是否使用流式响应
        """
        super().__init__(config)
        
        if not self.config.get("api_key"):
            raise ProviderError("未设置API密钥", "openai")
            
        # 设置默认配置
        self.config.setdefault("model", "gpt-3.5-turbo")
        self.config.setdefault("temperature", 0.7)
        self.config.setdefault("max_tokens", 2000)
        self.config.setdefault("stream", True)
        
        # 初始化API客户端
        self.client = AsyncOpenAI(api_key=self.config["api_key"])
        
    async def generate_response(self, prompt: str) -> str:
        """
        生成回答。
        
        Args:
            prompt: 输入的问题或提示
            
        Returns:
            str: 生成的回答
            
        Raises:
            ProviderError: 当调用API出错时抛出
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.config["model"],
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                stream=False  # 非流式请求
            )
            
            return response.choices[0].message.content
            
        except APIError as e:
            raise ProviderError(str(e), "openai")
        except Exception as e:
            raise ProviderError(f"生成回答失败: {str(e)}", "openai")
            
    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        流式生成回答。
        
        Args:
            prompt: 输入的问题或提示
            
        Yields:
            str: 生成的部分回答
            
        Raises:
            ProviderError: 当调用API出错时抛出
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.config["model"],
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                stream=True  # 流式请求
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except APIError as e:
            raise ProviderError(str(e), "openai")
        except Exception as e:
            raise ProviderError(f"流式生成失败: {str(e)}", "openai")
            
    def validate_config(self) -> bool:
        """
        验证配置是否有效。
        
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        required_fields = ["api_key"]
        if not all(field in self.config for field in required_fields):
            return False
            
        if "temperature" in self.config:
            if not isinstance(self.config["temperature"], (int, float)):
                return False
            if not 0 <= self.config["temperature"] <= 2:
                return False
                
        if "max_tokens" in self.config:
            if not isinstance(self.config["max_tokens"], int):
                return False
            if self.config["max_tokens"] <= 0:
                return False
                
        if "stream" in self.config:
            if not isinstance(self.config["stream"], bool):
                return False
                
        return True

class OpenAIError(ProviderError):
    """OpenAI相关的错误。"""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        """
        初始化错误。
        
        Args:
            message: 错误信息
            status_code: HTTP状态码
        """
        self.status_code = status_code
        super().__init__(message, "openai")

async def test_api_key(api_key: str) -> bool:
    """
    测试API密钥是否有效。
    
    Args:
        api_key: 要测试的API密钥
        
    Returns:
        bool: 密钥有效返回True，否则返回False
    """
    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": "Hello"
            }],
            max_tokens=5
        )
        return True
    except Exception:
        return False
