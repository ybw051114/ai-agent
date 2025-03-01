"""
DeepSeek提供商实现。
"""
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp

from .base import BaseProvider, ProviderError, register_provider

@register_provider("deepseek")
class DeepSeekProvider(BaseProvider):
    """DeepSeek API提供商实现。"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化DeepSeek提供商。
        
        Args:
            config: 配置字典，必须包含：
                - api_key: DeepSeek API密钥
                可选包含：
                - model: 模型名称，默认为deepseek-chat
                - temperature: 温度参数
                - max_tokens: 最大token数
                - stream: 是否使用流式响应
        """
        super().__init__(config)
        
        if not self.config.get("api_key"):
            raise ProviderError("未设置API密钥", "deepseek")
            
        # 设置默认配置
        self.config.setdefault("model", "deepseek-chat")
        self.config.setdefault("temperature", 0.7)
        self.config.setdefault("max_tokens", 2000)
        self.config.setdefault("stream", True)
        
        # API endpoint
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
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
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        
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
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(f"API调用失败: {error_text}", "deepseek")
                        
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                    
        except aiohttp.ClientError as e:
            raise ProviderError(f"网络请求失败: {str(e)}", "deepseek")
        except Exception as e:
            raise ProviderError(f"生成回答失败: {str(e)}", "deepseek")
            
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
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        
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
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(f"API调用失败: {error_text}", "deepseek")
                        
                    async for line in response.content:
                        if not line:
                            continue
                            
                        try:
                            chunk = line.decode('utf-8').strip()
                            if not chunk.startswith('data: '):
                                continue
                                
                            chunk = chunk[6:]  # 去掉 'data: ' 前缀
                            if chunk == '[DONE]':
                                break
                                
                            chunk_data = json.loads(chunk)
                            if content := chunk_data.get('choices', [{}])[0].get('delta', {}).get('content', ''):
                                yield content
                        except Exception as e:
                            print(f"Error processing chunk: {str(e)}")
                            continue
                    
        except aiohttp.ClientError as e:
            raise ProviderError(f"网络请求失败: {str(e)}", "deepseek")
        except Exception as e:
            raise ProviderError(f"流式生成失败: {str(e)}", "deepseek")
            
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
            if not 0 <= self.config["temperature"] <= 1:
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

async def test_api_key(api_key: str) -> bool:
    """
    测试API密钥是否有效。
    
    Args:
        api_key: 要测试的API密钥
        
    Returns:
        bool: 密钥有效返回True，否则返回False
    """
    provider = DeepSeekProvider({"api_key": api_key})
    try:
        response = await provider.generate_response("Hello")
        return True
    except Exception:
        return False
