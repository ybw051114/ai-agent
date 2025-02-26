"""
AI代理包。

提供了一个可扩展的命令行AI代理系统，支持多种AI提供商、插件系统和自定义输出处理。
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from .core.agent import Agent, AgentBuilder
from .core.config import Config, ConfigManager, config_manager
from .providers.base import BaseProvider, ProviderError
from .plugins.base import BasePlugin, PluginManager
from .output.base import BaseOutput, OutputManager

__all__ = [
    "Agent",
    "AgentBuilder",
    "Config",
    "ConfigManager",
    "config_manager",
    "BaseProvider",
    "ProviderError",
    "BasePlugin",
    "PluginManager",
    "BaseOutput",
    "OutputManager",
]
