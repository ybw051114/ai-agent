"""
AI代理核心功能的单元测试。
"""
import asyncio
import pytest
from typing import AsyncGenerator, Optional

from ai_agent.core.agent import Agent, AgentBuilder
from ai_agent.providers.base import BaseProvider
from ai_agent.plugins.base import BasePlugin
from ai_agent.output import BaseOutput
from ai_agent.core.config import Config

class MockProvider(BaseProvider):
    """模拟的AI提供商。"""
    
    def __init__(self, response="Mock response"):
        super().__init__()
        self.response = response
        self.last_prompt = None
        
    async def generate_response(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response
        
    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        self.last_prompt = prompt
        yield "Hello "  # 第一个chunk
        yield "World"   # 第二个chunk

class MockPlugin(BasePlugin):
    """模拟的插件。"""
    
    def pre_process(self, input_text: str) -> str:
        return f"[Pre] {input_text}"
        
    def post_process(self, output_text: str) -> str:
        return f"[Post] {output_text}"

class MockOutput(BaseOutput):
    """模拟的输出处理器。"""
    
    def __init__(self):
        super().__init__()
        self.last_output = None
        self.stream_output = []
        
    async def render(self, content: str) -> None:
        self.last_output = content
        
    async def render_stream(self, content_stream) -> None:
        async for chunk in content_stream:
            self.stream_output.append(chunk)
            self.last_output = chunk

@pytest.fixture
def mock_provider():
    """提供模拟的AI提供商。"""
    return MockProvider("Hello, World!")

@pytest.fixture
def mock_plugin():
    """提供模拟的插件。"""
    return MockPlugin()

@pytest.fixture
def mock_output():
    """提供模拟的输出处理器。"""
    return MockOutput()

@pytest.mark.asyncio
async def test_agent_basic_processing(mock_provider, mock_output):
    """测试代理的基本处理功能。"""
    agent = Agent(mock_provider)
    agent.add_output(mock_output, default=True)
    
    result = await agent.process("Test input")
    
    assert mock_provider.last_prompt == "Test input"
    assert mock_output.last_output == result == "Hello, World!"

@pytest.mark.asyncio
async def test_agent_with_plugin(mock_provider, mock_plugin, mock_output):
    """测试带插件的代理处理。"""
    agent = Agent(mock_provider)
    agent.add_plugin(mock_plugin)
    agent.add_output(mock_output, default=True)
    
    result = await agent.process("Test input")
    
    assert mock_provider.last_prompt == "[Pre] Test input"
    assert mock_output.last_output == result == "[Post] Hello, World!"

@pytest.mark.asyncio
async def test_agent_stream_processing(mock_provider, mock_output):
    """测试代理的流式处理。"""
    agent = Agent(mock_provider)
    agent.add_output(mock_output, default=True)
    
    result = await agent.process_stream("Test input")
    
    assert mock_provider.last_prompt == "Test input"
    assert result == "Hello World"  # 完整输出
    assert mock_output.last_output == "World"  # 最后一个chunk
    assert mock_output.stream_output == ["Hello ", "World"]  # 流式输出记录

@pytest.mark.asyncio
async def test_agent_stream_with_plugin(mock_provider, mock_plugin, mock_output):
    """测试带插件的流式处理。"""
    agent = Agent(mock_provider)
    agent.add_plugin(mock_plugin)
    agent.add_output(mock_output, default=True)
    
    result = await agent.process_stream("Test input")
    
    assert mock_provider.last_prompt == "[Pre] Test input"
    assert result == "Hello World"  # 完整输出（插件后处理前）
    assert mock_output.stream_output == ["Hello ", "World"]  # 流式输出记录

def test_agent_builder():
    """测试代理构建器。"""
    provider = MockProvider()
    plugin = MockPlugin()
    output = MockOutput()
    
    # 测试基本构建
    builder = AgentBuilder()
    builder.with_provider(provider)
    builder.with_plugin(plugin)
    builder.with_output(output)
    
    agent = builder.build()
    
    assert agent.provider is provider
    assert plugin.__class__.__name__ in agent.plugin_manager.list_plugins()
    assert output.__class__.__name__ in agent.output_manager._outputs
    
    # 测试缺少提供商时的错误
    builder = AgentBuilder()
    with pytest.raises(ValueError):
        builder.build()
    
    # 测试配置
    config = {"test_key": "test_value"}
    builder = AgentBuilder()
    builder.with_provider(provider)
    builder.with_config(config)
    
    agent = builder.build()
    assert agent.config["test_key"] == "test_value"

@pytest.mark.asyncio
async def test_agent_error_handling(mock_output):
    """测试代理的错误处理。"""
    class ErrorProvider(BaseProvider):
        async def generate_response(self, prompt: str) -> str:
            raise Exception("Test error")
            
        async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
            raise Exception("Test error")
    
    agent = Agent(ErrorProvider())
    agent.add_output(mock_output, default=True)
    
    # 测试普通处理中的错误
    with pytest.raises(Exception):
        await agent.process("Test input")
    
    # 测试流式处理中的错误
    with pytest.raises(Exception):
        await agent.process_stream("Test input")

def test_agent_plugin_priority():
    """测试代理的插件优先级处理。"""
    class HighPriorityPlugin(MockPlugin):
        @property
        def priority(self) -> int:
            return 0
            
    class LowPriorityPlugin(MockPlugin):
        @property
        def priority(self) -> int:
            return 100
    
    agent = Agent(MockProvider())
    high = HighPriorityPlugin()
    low = LowPriorityPlugin()
    
    agent.add_plugin(low)
    agent.add_plugin(high)
    
    plugins = agent._get_sorted_plugins()
    assert plugins[0] is high
    assert plugins[1] is low

if __name__ == "__main__":
    pytest.main([__file__])
