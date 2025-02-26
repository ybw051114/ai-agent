"""
插件模块。
"""
from .base import BasePlugin, PluginManager, PluginError, register_plugin
from .translator import TranslatorPlugin

__all__ = [
    "BasePlugin",
    "PluginManager",
    "PluginError",
    "register_plugin",
    "TranslatorPlugin",
]
