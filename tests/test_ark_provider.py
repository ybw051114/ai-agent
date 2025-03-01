"""
火山引擎 Ark Provider 的测试模块。
"""
import asyncio
import json
from typing import AsyncGenerator, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from ai_agent.providers.ark import ArkProvider
from ai_agent.providers.base import ProviderError

@pytest.fixture
def provider():
    """创建一个测试用的provider实例。"""
    return ArkProvider({
        "api_key": "test-key",
        "model": "test-model",
        "temperature": 0.5,
        "max_tokens": 100
    })

@pytest.fixture
def mock_response():
    """模拟API响应。"""
    mock = MagicMock()
    mock.status = 200
    return mock

@pytest.fixture
def error_response():
    """模拟错误响应。"""
    mock = MagicMock()
    mock.status = 400
    mock.text = AsyncMock(return_value="API错误")
    return mock

def test_init_with_valid_config():
    """测试使用有效配置初始化。"""
    provider = ArkProvider({
        "api_key": "test-key",
        "model": "test-model",
        "temperature": 0.5
    })
    assert provider.config["api_key"] == "test-key"
    assert provider.config["model"] == "test-model"
    assert provider.config["temperature"] == 0.5
    assert provider.headers["Authorization"] == "Bearer test-key"

def test_init_without_api_key():
    """测试没有API密钥时的初始化。"""
    with pytest.raises(ProviderError) as exc_info:
        ArkProvider({})
    assert "未设置API密钥" in str(exc_info.value)

def test_validate_config_with_valid_config():
    """测试有效配置的验证。"""
    provider = ArkProvider({
        "api_key": "test-key",
        "temperature": 0.5,
        "max_tokens": 100
    })
    assert provider.validate_config() is True

def test_validate_config_with_invalid_temperature():
    """测试无效温度参数的验证。"""
    provider = ArkProvider({
        "api_key": "test-key",
        "temperature": 3.0  # 超出有效范围
    })
    assert provider.validate_config() is False

def test_validate_config_with_invalid_max_tokens():
    """测试无效最大token数的验证。"""
    provider = ArkProvider({
        "api_key": "test-key",
        "max_tokens": -1  # 无效值
    })
    assert provider.validate_config() is False

@pytest.mark.asyncio
async def test_generate_response_success(provider, mock_response):
    """测试成功生成响应。"""
    test_response = {
        "choices": [{
            "message": {
                "content": "test response"
            }
        }]
    }
    mock_response.json = AsyncMock(return_value=test_response)
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response
        response = await provider.generate_response("test prompt")
        
    assert response == "test response"
    
@pytest.mark.asyncio
async def test_generate_response_api_error(provider, error_response):
    """测试API错误时的响应生成。"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = error_response
        with pytest.raises(ProviderError) as exc_info:
            await provider.generate_response("test prompt")
            
    assert "API调用失败" in str(exc_info.value)

@pytest.mark.asyncio
async def test_generate_response_network_error(provider):
    """测试网络错误时的响应生成。"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.side_effect = aiohttp.ClientError("网络错误")
        with pytest.raises(ProviderError) as exc_info:
            await provider.generate_response("test prompt")
            
    assert "网络请求失败" in str(exc_info.value)

@pytest.mark.asyncio
async def test_stream_response_success(provider, mock_response):
    """测试成功的流式响应。"""
    # 模拟流式响应的内容
    chunks = [
        b'data: {"choices":[{"delta":{"content":"test"}}]}\n',
        b'data: {"choices":[{"delta":{"content":"response"}}]}\n',
        b'data: [DONE]\n'
    ]
    mock_response.content = AsyncMock()
    mock_response.content.__aiter__.return_value = [chunk for chunk in chunks]
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response
        responses = []
        async for chunk in provider.stream_response("test prompt"):
            responses.append(chunk)
            
    assert responses == ["test", "response"]

@pytest.mark.asyncio
async def test_stream_response_api_error(provider, error_response):
    """测试流式响应时的API错误。"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = error_response
        with pytest.raises(ProviderError) as exc_info:
            async for _ in provider.stream_response("test prompt"):
                pass
                
    assert "API调用失败" in str(exc_info.value)

@pytest.mark.asyncio
async def test_stream_response_network_error(provider):
    """测试流式响应时的网络错误。"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.side_effect = aiohttp.ClientError("网络错误")
        with pytest.raises(ProviderError) as exc_info:
            async for _ in provider.stream_response("test prompt"):
                pass
                
    assert "网络请求失败" in str(exc_info.value)

@pytest.mark.asyncio
async def test_stream_response_invalid_json(provider, mock_response):
    """测试流式响应中的无效JSON处理。"""
    # 模拟包含无效JSON的响应
    chunks = [
        b'data: {"choices":[{"delta":{"content":"test"}}]}\n',
        b'data: invalid-json\n',
        b'data: {"choices":[{"delta":{"content":"response"}}]}\n',
        b'data: [DONE]\n'
    ]
    mock_response.content = AsyncMock()
    mock_response.content.__aiter__.return_value = [chunk for chunk in chunks]
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response
        responses = []
        async for chunk in provider.stream_response("test prompt"):
            responses.append(chunk)
            
    # 无效JSON被跳过，只包含有效的响应
    assert responses == ["test", "response"]
