"""
火山引擎 Ark API 提供商实现。
"""
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp

from .base import BaseProvider, ProviderError, register_provider

@register_provider("ark")
class ArkProvider(BaseProvider):
    """火山引擎 Ark API 提供商实现。"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Ark 提供商。
        
        Args:
            config: 配置字典，必须包含：
                - api_key: Ark API密钥
                可选包含：
                - model: 模型名称
                - temperature: 温度参数
                - max_tokens: 最大token数
        """
        super().__init__(config)
        
        # 验证 API 密钥
        if not self.config.get("api_key"):
            raise ProviderError("未设置API密钥", "ark")
            
        # 设置默认配置
        self.config.setdefault("model", "claude-2.1")
        self.config.setdefault("temperature", 0.7)
        self.config.setdefault("max_tokens", 2000)
        
        # 初始化session配置
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
        self.headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
            
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
        messages = []
        if conversation:
            messages.extend(conversation)
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        data = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": self.config["temperature"],
            "max_tokens": self.config["max_tokens"],
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(f"API调用失败: {error_text}", "ark")
                        
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                    
        except aiohttp.ClientError as e:
            raise ProviderError(f"网络请求失败: {str(e)}", "ark")
        except Exception as e:
            raise ProviderError(f"生成回答失败: {str(e)}", "ark")
            
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
        messages = []
        if conversation:
            messages.extend(conversation)
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        data = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": self.config["temperature"],
            "max_tokens": self.config["max_tokens"],
            "stream": True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(f"API调用失败: {error_text}", "ark")
                        
                    # 处理流式响应
                    async for line in response.content:
                        try:
                            text = line.decode().strip()
                            if text.startswith("data: "):
                                json_str = text[6:]  # 跳过 "data: "
                                if json_str == "[DONE]":
                                    break

                                chunk = json.loads(json_str)
                                if content := chunk["choices"][0]["delta"].get("content"):
                                    yield content
                        except json.JSONDecodeError:
                            continue  # 跳过无效的JSON行
                                
        except aiohttp.ClientError as e:
            raise ProviderError(f"网络请求失败: {str(e)}", "ark")
        except Exception as e:
            raise ProviderError(f"流式生成失败: {str(e)}", "ark")
            
    def validate_config(self) -> bool:
        """
        验证配置是否有效。
        
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        # 检查必需的配置项
        if "api_key" not in self.config:
            return False
            
        # 验证温度参数
        if "temperature" in self.config:
            if not isinstance(self.config["temperature"], (int, float)):
                return False
            if not 0 <= self.config["temperature"] <= 2:
                return False
                
        # 验证最大token数
        if "max_tokens" in self.config:
            if not isinstance(self.config["max_tokens"], int):
                return False
            if self.config["max_tokens"] <= 0:
                return False
                
        return True

async def test_api_key(api_key: str) -> bool:
    """
    测试API密钥是否有效。
    
    Args:
        api_key: 要测试的API密钥
        
    Returns:
        bool: 密钥有效返回True，否则返回False
    """
    provider = ArkProvider({"api_key": api_key})
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{provider.base_url}/chat/completions",
                headers=provider.headers,
                json={
                    "model": provider.config["model"],
                    "messages": [{
                        "role": "user",
                        "content": "Hello"
                    }],
                    "max_tokens": 5,
                    "stream": False
                }
            ) as response:
                return response.status == 200
    except Exception:
        return False
