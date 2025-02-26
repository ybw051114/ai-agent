"""
插件系统的单元测试。
"""
import pytest
from ai_agent.plugins import BasePlugin, PluginManager, PluginError, register_plugin

# 创建测试用插件
@register_plugin("test")
class TestPlugin(BasePlugin):
    """测试用插件。"""
    
    def pre_process(self, input_text: str) -> str:
        return f"[Pre-processed] {input_text}"
        
    def post_process(self, output_text: str) -> str:
        return f"[Post-processed] {output_text}"

def test_plugin_registration():
    """测试插件注册。"""
    manager = PluginManager()
    plugin = TestPlugin()
    
    # 测试注册
    manager.register("test", plugin)
    assert "test" in manager.list_plugins()
    
    # 测试重复注册
    with pytest.raises(ValueError):
        manager.register("test", plugin)
        
    # 测试获取插件
    retrieved = manager.get_plugin("test")
    assert isinstance(retrieved, TestPlugin)
    
    # 测试注销插件
    manager.unregister("test")
    assert "test" not in manager.list_plugins()
    
    # 测试获取不存在的插件
    with pytest.raises(KeyError):
        manager.get_plugin("nonexistent")

def test_plugin_processing():
    """测试插件的处理功能。"""
    plugin = TestPlugin()
    
    # 测试预处理
    input_text = "Hello"
    processed = plugin.pre_process(input_text)
    assert processed == "[Pre-processed] Hello"
    
    # 测试后处理
    output_text = "World"
    processed = plugin.post_process(output_text)
    assert processed == "[Post-processed] World"

def test_plugin_priority():
    """测试插件优先级。"""
    @register_plugin("high_priority")
    class HighPriorityPlugin(BasePlugin):
        @property
        def priority(self) -> int:
            return 0
            
    @register_plugin("low_priority")
    class LowPriorityPlugin(BasePlugin):
        @property
        def priority(self) -> int:
            return 100
    
    manager = PluginManager()
    high = HighPriorityPlugin()
    low = LowPriorityPlugin()
    
    manager.register("high", high)
    manager.register("low", low)
    
    plugins = list(manager.list_plugins().values())
    sorted_plugins = sorted(plugins, key=lambda x: x.priority)
    
    assert sorted_plugins[0] is high
    assert sorted_plugins[1] is low

def test_plugin_config():
    """测试插件配置。"""
    class ConfigurablePlugin(BasePlugin):
        def validate_config(self) -> bool:
            if not self.config:
                return True
            return "required_field" in self.config
    
    # 测试有效配置
    plugin = ConfigurablePlugin({"required_field": "value"})
    assert plugin.validate_config()
    
    # 测试无效配置
    plugin = ConfigurablePlugin({"wrong_field": "value"})
    assert not plugin.validate_config()
    
    # 测试空配置
    plugin = ConfigurablePlugin()
    assert plugin.validate_config()

def test_plugin_error():
    """测试插件错误处理。"""
    error = PluginError("Test error", "test_plugin")
    assert str(error) == "[test_plugin] Test error"
    assert error.plugin_name == "test_plugin"

def test_register_plugin_decorator():
    """测试插件注册装饰器。"""
    # 测试装饰非BasePlugin子类
    with pytest.raises(TypeError):
        @register_plugin("invalid")
        class InvalidPlugin:
            pass
    
    # 测试正确的装饰器使用
    @register_plugin("valid")
    class ValidPlugin(BasePlugin):
        pass
    
    assert hasattr(ValidPlugin, "plugin_name")
    assert ValidPlugin.plugin_name == "valid"

if __name__ == "__main__":
    pytest.main([__file__])
