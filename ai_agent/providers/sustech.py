"""
南科大API提供商实现。
"""
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp
from .base import BaseProvider, ProviderError, register_provider

@register_provider("sustech")
class SustechProvider(BaseProvider):
    """南科大API提供商实现。"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化南科大API提供商。
        
        Args:
            config: 配置字典，必须包含：
                - api_key: API密钥
                可选包含：
                - base_url: API基础URL，默认为https://chat.sustech.edu.cn/api
                - model: 模型名称，默认为deepseek-r1-250120
                - temperature: 温度参数，默认为0.7
                - max_tokens: 最大token数，默认为2000
        """
        super().__init__(config)
        
        if not self.config.get("api_key"):
            raise ProviderError("未设置API密钥", "sustech")
            
        # 设置默认配置
        self.config.setdefault("base_url", "https://chat.sustech.edu.cn/api")
        self.config.setdefault("model", "deepseek-r1-250120")
        self.config.setdefault("temperature", 0.7)
        self.config.setdefault("max_tokens", 2000)
        
        # 设置会话配置
        self.session = None
        
    async def _ensure_session(self):
        """确保aiohttp会话已创建。"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.config['api_key']}"}
            )
    
    async def _cleanup_session(self):
        """清理aiohttp会话。"""
        if self.session and not self.session.closed:
            await self.session.close()
            
    async def generate_response(self, prompt: str, conversation: Optional[List[Dict]] = None) -> str:
        """
        生成回答。
        
        Args:
            prompt: 输入的问题或提示
            conversation: 可选的历史对话记录
            
        Returns:
            str: 生成的回答
            
        Raises:
            ProviderError: 当调用API出错时抛出
        """
        try:
            await self._ensure_session()
            try:
                messages = []
                if conversation:
                    messages.extend(conversation)
                messages.append({
                    "role": "user",
                    "content": prompt
                })
                
                async with self.session.post(
                    f"{self.config['base_url']}/chat/completions",
                    json={
                        "model": self.config["model"],
                        "messages": messages,
                        "temperature": self.config["temperature"],
                        "max_tokens": self.config["max_tokens"],
                        "stream": False
                    }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(
                            f"API请求失败: HTTP {response.status} - {error_text}",
                            "sustech"
                        )
                        
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
            finally:
                await self._cleanup_session()
                
        except aiohttp.ClientError as e:
            raise ProviderError(f"HTTP请求错误: {str(e)}", "sustech")
        except Exception as e:
            raise ProviderError(f"生成回答失败: {str(e)}", "sustech")
            
    async def stream_response(self, prompt: str, conversation: Optional[List[Dict]] = None) -> AsyncGenerator[str, None]:
        """
        流式生成回答。
        
        Args:
            prompt: 输入的问题或提示
            conversation: 可选的历史对话记录
            
        Yields:
            str: 生成的部分回答
            
        Raises:
            ProviderError: 当调用API出错时抛出
        """
        try:
            await self._ensure_session()
            try:
                messages = []
                if conversation:
                    messages.extend(conversation)
                messages.append({
                    "role": "user",
                    "content": prompt
                })
                
                async with self.session.post(
                    f"{self.config['base_url']}/chat/completions",
                    json={
                        "model": self.config["model"],
                        "messages": messages,
                        "temperature": self.config["temperature"],
                        "max_tokens": self.config["max_tokens"],
                        "stream": True
                    }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(
                            f"API请求失败: HTTP {response.status} - {error_text}",
                            "sustech"
                        )
                        
                    async for line in response.content:
                        line = line.strip()
                        if not line or line == b"data: [DONE]":
                            continue
                            
                        try:
                            data = json.loads(line.decode("utf-8").replace("data: ", ""))
                            if content := data["choices"][0]["delta"].get("content"):
                                yield content
                        except Exception as e:
                            raise ProviderError(f"解析响应失败: {str(e)}", "sustech")
            finally:
                await self._cleanup_session()
                
        except aiohttp.ClientError as e:
            raise ProviderError(f"HTTP请求错误: {str(e)}", "sustech")
        except Exception as e:
            raise ProviderError(f"流式生成失败: {str(e)}", "sustech")
            
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
                
        return True
        
    async def __aenter__(self):
        """进入异步上下文。"""
        await self._ensure_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出异步上下文。"""
        await self._cleanup_session()

async def verify_api_key(api_key: str, base_url: str = "https://chat.sustech.edu.cn/api") -> bool:
    """
    测试API密钥是否有效。
    
    Args:
        api_key: 要测试的API密钥
        base_url: API基础URL
        
    Returns:
        bool: 密钥有效返回True，否则返回False
    """
    async with aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {api_key}"}
    ) as session:
        try:
            async with session.post(
                f"{base_url}/chat/completions",
                json={
                    "model": "deepseek-r1-250120",
                    "messages": [{
                        "role": "user",
                        "content": "Hello"
                    }],
                    "max_tokens": 5
                }
            ) as response:
                return response.status == 200
        except Exception:
            return False
