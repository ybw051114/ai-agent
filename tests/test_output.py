"""
输出处理模块的单元测试。
"""
import asyncio
import pytest
from io import StringIO
from typing import AsyncGenerator

from ai_agent.output import BaseOutput, OutputManager, OutputError, register_output
from ai_agent.output.terminal import TerminalOutput

# 创建测试用输出处理器
@register_output("test")
class TestOutput(BaseOutput):
    """测试用输出处理器。"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = StringIO()
        
    def render(self, content: str) -> None:
        self.output.write(content)
        
    async def render_stream(self, content_stream) -> None:
        async for chunk in content_stream:
            self.output.write(chunk)
            
    def get_output(self) -> str:
        return self.output.getvalue()

async def mock_stream() -> AsyncGenerator[str, None]:
    """模拟内容流。"""
    for text in ["Hello", ", ", "World", "!"]:
        yield text
        await asyncio.sleep(0.01)

def test_output_registration():
    """测试输出处理器注册。"""
    manager = OutputManager()
    output = TestOutput()
    
    # 测试注册
    manager.register("test", output)
    assert manager.get_output("test") is output
    
    # 测试默认输出
    default_output = manager.get_output()
    assert default_output is output
    
    # 测试重复注册
    with pytest.raises(ValueError):
        manager.register("test", output)
    
    # 测试注销默认输出
    with pytest.raises(ValueError):
        manager.unregister("test")
    
    # 测试获取不存在的输出
    with pytest.raises(KeyError):
        manager.get_output("nonexistent")

def test_output_default_setting():
    """测试默认输出设置。"""
    manager = OutputManager()
    output1 = TestOutput()
    output2 = TestOutput()
    
    manager.register("test1", output1)
    manager.register("test2", output2)
    
    # 测试设置默认输出
    manager.set_default("test2")
    assert manager.get_output() is output2
    
    # 测试设置不存在的默认输出
    with pytest.raises(KeyError):
        manager.set_default("nonexistent")

@pytest.mark.asyncio
async def test_output_rendering():
    """测试输出渲染。"""
    output = TestOutput()
    
    # 测试普通渲染
    output.render("Hello World!")
    assert output.get_output() == "Hello World!"
    
    # 测试流式渲染
    output = TestOutput()  # 重置输出
    await output.render_stream(mock_stream())
    assert output.get_output() == "Hello, World!"

def test_terminal_output():
    """测试终端输出处理器。"""
    output = TerminalOutput()
    
    # 测试基本功能
    assert output.validate_config()
    
    # 测试有效配置
    valid_configs = [
        {"color_system": "auto", "width": 80},
        {"color_system": "standard"},
        {"color_system": "256"},
        {"color_system": "truecolor"}
    ]
    for config in valid_configs:
        output = TerminalOutput(config)
        assert output.validate_config(), f"配置应该有效: {config}"
    
    # 测试无效配置
    invalid_configs = [
        {"color_system": "invalid"},
        {"width": "not_a_number"},
        {"color_system": 123},  # 应该是字符串
    ]
    for config in invalid_configs:
        output = TerminalOutput()
        output.config = config  # 直接设置config以避免Console初始化错误
        assert not output.validate_config(), f"无效配置应该使validate_config返回False: {config}"

def test_output_error():
    """测试输出错误处理。"""
    error = OutputError("Test error", "test_output")
    assert str(error) == "[test_output] Test error"
    assert error.output_name == "test_output"

def test_register_output_decorator():
    """测试输出处理器注册装饰器。"""
    # 测试装饰非BaseOutput子类
    with pytest.raises(TypeError):
        @register_output("invalid")
        class InvalidOutput:
            pass
    
    # 测试正确的装饰器使用
    @register_output("valid")
    class ValidOutput(BaseOutput):
        def render(self, content: str) -> None:
            pass
            
        async def render_stream(self, content_stream) -> None:
            pass
    
    assert hasattr(ValidOutput, "output_name")
    assert ValidOutput.output_name == "valid"

def test_markdown_rendering():
    """测试Markdown渲染支持。"""
    output = TestOutput()
    
    # 测试Markdown文本
    markdown_text = """
    # Title
    
    - List item 1
    - List item 2
    
    ```python
    print("Hello World!")
    ```
    """
    
    output.render(markdown_text)
    rendered = output.get_output()
    
    assert rendered == markdown_text
    assert "# Title" in rendered
    assert "```python" in rendered

if __name__ == "__main__":
    pytest.main([__file__])
