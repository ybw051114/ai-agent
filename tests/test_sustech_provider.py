"""
南科大Provider测试。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_agent.providers.sustech import SustechProvider, verify_api_key
from ai_agent.providers.base import ProviderError

@pytest.fixture
def sustech_config():
    """Sustech provider配置fixture"""
    return {
        "api_key": "test_key",
        "model": "deepseek-r1-250120",
        "temperature": 0.7,
        "max_tokens": 100,
        "base_url": "https://chat.sustech.edu.cn/api"
    }

@pytest.fixture
def sustech_provider(sustech_config):
    """Sustech provider实例fixture"""
    return SustechProvider(sustech_config)

@pytest.mark.asyncio
async def test_sustech_init(sustech_config):
    """测试Sustech provider初始化"""
    provider = SustechProvider(sustech_config)
    assert provider.config["api_key"] == "test_key"
    assert provider.config["model"] == "deepseek-r1-250120"
    assert provider.config["temperature"] == 0.7
    assert provider.config["max_tokens"] == 100
    assert provider.config["base_url"] == "https://chat.sustech.edu.cn/api"

@pytest.mark.asyncio
async def test_sustech_init_no_api_key():
    """测试没有API密钥时初始化失败"""
    with pytest.raises(ProviderError) as exc_info:
        SustechProvider({})
    assert "未设置API密钥" in str(exc_info.value)

@pytest.mark.asyncio
async def test_generate_response(sustech_provider):
    """测试生成回答"""
    mock_response = {
        "choices": [{
            "message": {
                "content": "Hello!"
            }
        }]
    }
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 200
        mock_context.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
        mock_post.return_value = mock_context
        
        response = await sustech_provider.generate_response("Hi")
        assert response == "Hello!"

@pytest.mark.asyncio
async def test_generate_response_api_error(sustech_provider):
    """测试API错误时生成回答失败"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 400
        mock_context.__aenter__.return_value.text = AsyncMock(return_value="API Error")
        mock_post.return_value = mock_context
        
        with pytest.raises(ProviderError) as exc_info:
            await sustech_provider.generate_response("Hi")
        assert "API请求失败" in str(exc_info.value)

@pytest.mark.asyncio
async def test_stream_response(sustech_provider):
    """测试流式生成回答"""
    mock_chunks = [
        b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
        b'data: {"choices":[{"delta":{"content":" World"}}]}\n',
        b'data: [DONE]\n'
    ]

    class MockStream:
        def __init__(self, chunks):
            self.chunks = chunks
            self.index = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.index >= len(self.chunks):
                raise StopAsyncIteration
            chunk = self.chunks[self.index]
            self.index += 1
            return chunk

    class MockResponse:
        def __init__(self, chunks):
            self.content = MockStream(chunks)
            self.status = 200
            
        async def text(self):
            return "Success"
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = MockResponse(mock_chunks)
        mock_post.return_value = mock_context
        
        chunks = []
        async for chunk in sustech_provider.stream_response("Hi"):
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0] == "Hello"
        assert chunks[1] == " World"

@pytest.mark.asyncio
async def test_stream_response_api_error(sustech_provider):
    """测试API错误时流式生成失败"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 400
        mock_context.__aenter__.return_value.text = AsyncMock(return_value="API Error")
        mock_post.return_value = mock_context
        
        with pytest.raises(ProviderError) as exc_info:
            async for _ in sustech_provider.stream_response("Hi"):
                pass
        assert "API请求失败" in str(exc_info.value)

def test_validate_config(sustech_provider):
    """测试配置验证"""
    assert sustech_provider.validate_config() is True
    
    # 测试无效配置
    invalid_configs = [
        {"api_key": "test", "temperature": 2.1},  # temperature超出范围
        {"api_key": "test", "temperature": "0.7"},  # temperature类型错误
        {"api_key": "test", "max_tokens": 0},  # max_tokens无效
        {"api_key": "test", "max_tokens": "100"},  # max_tokens类型错误
    ]
    
    for config in invalid_configs:
        provider = SustechProvider(config)
        assert provider.validate_config() is False

@pytest.mark.asyncio
async def test_verify_api_key(sustech_config):
    """测试API密钥验证"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 200
        mock_post.return_value = mock_context
        assert await verify_api_key(sustech_config["api_key"]) is True

        # 测试无效密钥
        mock_context.__aenter__.return_value.status = 401
        mock_context.__aenter__.return_value.text = AsyncMock(return_value="Invalid API key")
        assert await verify_api_key("invalid_key") is False
