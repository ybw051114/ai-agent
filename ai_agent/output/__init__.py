"""
输出处理模块。
"""
from .base import BaseOutput, OutputManager, OutputError, register_output
from .terminal import TerminalOutput

__all__ = [
    "BaseOutput",
    "OutputManager",
    "OutputError",
    "register_output",
    "TerminalOutput",
]
