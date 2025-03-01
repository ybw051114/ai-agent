"""
Provider相关测试。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_agent.providers.deepseek import DeepSeekProvider, test_api_key
from ai_agent.providers.base import ProviderError

@pytest.fixture
def deepseek_config():
    """DeepSeek provider配置fixture"""
    return {
        "api_key": "test_key",
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 100
    }

@pytest.fixture
def deepseek_provider(deepseek_config):
    """DeepSeek provider实例fixture"""
    return DeepSeekProvider(deepseek_config)

@pytest.mark.asyncio
async def test_deepseek_init(deepseek_config):
    """测试DeepSeek provider初始化"""
    provider = DeepSeekProvider(deepseek_config)
    assert provider.config["api_key"] == "test_key"
    assert provider.config["model"] == "deepseek-chat"
    assert provider.config["temperature"] == 0.7
    assert provider.config["max_tokens"] == 100

@pytest.mark.asyncio
async def test_deepseek_init_no_api_key():
    """测试没有API密钥时初始化失败"""
    with pytest.raises(ProviderError) as exc_info:
        DeepSeekProvider({})
    assert "未设置API密钥" in str(exc_info.value)

@pytest.mark.asyncio
async def test_generate_response(deepseek_provider):
    """测试生成回答"""
    mock_response = {
        "choices": [{
            "message": {
                "content": "Hello!"
            }
        }]
    }
    
    conversation = [
        {"role": "user", "content": "Hi there"},
        {"role": "assistant", "content": "Hello! How can I help?"}
    ]
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 200
        mock_context.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
        mock_post.return_value = mock_context
        
        # 测试无历史对话的情况
        response = await deepseek_provider.generate_response("Hi")
        assert response == "Hello!"
        
        # 测试有历史对话的情况
        response = await deepseek_provider.generate_response("Hi", conversation)
        assert response == "Hello!"

@pytest.mark.asyncio
async def test_generate_response_api_error(deepseek_provider):
    """测试API错误时生成回答失败"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 400
        mock_context.__aenter__.return_value.text = AsyncMock(return_value="API Error")
        mock_post.return_value = mock_context
        
        with pytest.raises(ProviderError) as exc_info:
            await deepseek_provider.generate_response("Hi")
        assert "API调用失败" in str(exc_info.value)

@pytest.mark.asyncio
async def test_stream_response(deepseek_provider):
    """测试流式生成回答"""
    mock_chunks = [
        b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
        b'data: {"choices":[{"delta":{"content":" World"}}]}\n',
        b'data: [DONE]\n'
    ]
    
    conversation = [
        {"role": "user", "content": "Hi there"},
        {"role": "assistant", "content": "Hello! How can I help?"}
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
    
    # 测试无历史对话的情况
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = MockResponse(mock_chunks)
        mock_post.return_value = mock_context
        
        chunks = []
        async for chunk in deepseek_provider.stream_response("Hi"):
            chunks.append(chunk)
        assert len(chunks) == 2
        assert chunks[0] == "Hello"
        assert chunks[1] == " World"
        
    # 测试有历史对话的情况
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = MockResponse(mock_chunks)
        mock_post.return_value = mock_context
        
        chunks = []
        async for chunk in deepseek_provider.stream_response("Hi", conversation):
            chunks.append(chunk)
        assert len(chunks) == 2
        assert chunks[0] == "Hello"
        assert chunks[1] == " World"

@pytest.mark.asyncio
async def test_stream_response_api_error(deepseek_provider):
    """测试API错误时流式生成失败"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 400
        mock_context.__aenter__.return_value.text = AsyncMock(return_value="API Error")
        mock_post.return_value = mock_context
        
        with pytest.raises(ProviderError) as exc_info:
            async for _ in deepseek_provider.stream_response("Hi"):
                pass
        assert "API调用失败" in str(exc_info.value)

def test_validate_config(deepseek_provider):
    """测试配置验证"""
    assert deepseek_provider.validate_config() is True
    
    # 测试无效配置
    invalid_configs = [
        {"api_key": "test", "temperature": 2.0},  # temperature超出范围
        {"api_key": "test", "temperature": "0.7"},  # temperature类型错误
        {"api_key": "test", "max_tokens": 0},  # max_tokens无效
        {"api_key": "test", "max_tokens": "100"},  # max_tokens类型错误
        {"api_key": "test", "stream": "true"},  # stream类型错误
    ]
    
    for config in invalid_configs:
        provider = DeepSeekProvider(config)
        assert provider.validate_config() is False

@pytest.fixture
def api_key():
    """API密钥fixture"""
    return "test_key"

@pytest.mark.asyncio
async def test_api_key_test(api_key):
    """测试API密钥验证"""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 200
        mock_context.__aenter__.return_value.json = AsyncMock(return_value={"choices": [{"message": {"content": "Hello"}}]})
        mock_post.return_value = mock_context
        assert await test_api_key("test_key") is True

        # 测试无效密钥
        mock_context.__aenter__.return_value.status = 401
        mock_context.__aenter__.return_value.text = AsyncMock(return_value="Invalid API key")
        assert await test_api_key("invalid_key") is False
