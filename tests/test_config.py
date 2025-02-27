"""
配置管理模块的单元测试。
"""
import os
import pytest
from ai_agent.core.config import Config, ConfigManager

def test_config_defaults():
    """测试配置默认值。"""
    config = Config()
    assert config.provider == "openai"
    assert config.plugins == []
    assert config.output == ["terminal", "conversation"]
    assert config.model == "gpt-3.5-turbo"
    assert config.temperature == 0.7
    assert config.max_tokens == 2000
    assert config.stream is True

def test_config_custom_values():
    """测试自定义配置值。"""
    config = Config()
    config.provider = "custom"
    config.model = "gpt-4"
    config.temperature = 0.5
    
    assert config.provider == "custom"
    assert config.model == "gpt-4"
    assert config.temperature == 0.5

def test_config_manager_env_vars(monkeypatch):
    """测试从环境变量加载配置。"""
    # 设置测试环境变量
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AI_AGENT_PROVIDER", "custom")
    monkeypatch.setenv("AI_AGENT_MODEL", "gpt-4")
    monkeypatch.setenv("AI_AGENT_PLUGINS", "plugin1,plugin2")
    
    # 创建新的配置管理器并加载配置
    manager = ConfigManager()
    manager.load_config()
    
    assert manager.config.api_key == "test-key"
    assert manager.config.provider == "custom"
    assert manager.config.model == "gpt-4"
    assert manager.config.plugins == ["plugin1", "plugin2"]

def test_provider_config():
    """测试获取提供商配置。"""
    manager = ConfigManager()
    manager.config.api_key = "test-key"
    manager.config.model = "gpt-4"
    manager.config.temperature = 0.5
    
    provider_config = manager.get_provider_config()
    
    assert provider_config["api_key"] == "test-key"
    assert provider_config["model"] == "gpt-4"
    assert provider_config["temperature"] == 0.5
    assert "max_tokens" in provider_config
    assert "stream" in provider_config

def test_config_save_load(tmp_path):
    """测试配置的保存和加载。"""
    # 创建配置
    manager = ConfigManager()
    manager.config.api_key = "test-key"
    manager.config.provider = "custom"
    manager.config.model = "gpt-4"
    
    # 保存配置
    config_path = tmp_path / "test_config.toml"
    manager.save_config(str(config_path))
    
    # 创建新的管理器并加载配置
    new_manager = ConfigManager()
    new_manager.load_config(str(config_path))
    
    # 验证配置是否正确加载
    assert new_manager.config.api_key == "test-key"
    assert new_manager.config.provider == "custom"
    assert new_manager.config.model == "gpt-4"

if __name__ == "__main__":
    pytest.main([__file__])
