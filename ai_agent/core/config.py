"""
配置管理模块。
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

@dataclass
class Config:
    """配置类，存储所有配置项。"""
    
    provider: str = "openai"
    plugins: list = None
    output: str = "terminal"
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = True
    
    def __post_init__(self):
        """初始化后处理。"""
        self.plugins = self.plugins or []

class ConfigManager:
    """配置管理器，负责加载和管理配置。"""
    
    DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/ai-agent/config.toml")
    
    def __init__(self):
        """初始化配置管理器。"""
        self.config = Config()
        
    def load_config(self, config_path: Optional[str] = None) -> None:
        """
        加载配置。
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 1. 加载环境变量
        load_dotenv()
        
        # 2. 设置基础配置
        self._load_env_vars()
        
        # 3. 加载配置文件
        if config_path:
            self._load_config_file(config_path)
        elif os.path.exists(self.DEFAULT_CONFIG_PATH):
            self._load_config_file(self.DEFAULT_CONFIG_PATH)
    
    def _load_env_vars(self) -> None:
        """从环境变量加载配置。"""
        # API密钥
        if api_key := os.getenv("OPENAI_API_KEY"):
            self.config.api_key = api_key
        
        # 提供商
        if provider := os.getenv("AI_AGENT_PROVIDER"):
            self.config.provider = provider
            
        # 模型
        if model := os.getenv("AI_AGENT_MODEL"):
            self.config.model = model
            
        # 插件
        if plugins := os.getenv("AI_AGENT_PLUGINS"):
            self.config.plugins = plugins.split(",")
            
        # 输出方式
        if output := os.getenv("AI_AGENT_OUTPUT"):
            self.config.output = output
            
        # 温度
        if temp := os.getenv("AI_AGENT_TEMPERATURE"):
            try:
                self.config.temperature = float(temp)
            except ValueError:
                pass
                
        # 最大token数
        if max_tokens := os.getenv("AI_AGENT_MAX_TOKENS"):
            try:
                self.config.max_tokens = int(max_tokens)
            except ValueError:
                pass
                
        # 是否流式输出
        if stream := os.getenv("AI_AGENT_STREAM"):
            self.config.stream = stream.lower() in ("true", "1", "yes")
    
    def _load_config_file(self, config_path: str) -> None:
        """
        从文件加载配置。
        
        Args:
            config_path: 配置文件路径
        """
        import tomli
        print(config_path)
        
        try:
            with open(config_path, "rb") as f:
                file_config = tomli.load(f)
            
            # 更新配置
            for key, value in file_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    
    def get_provider_config(self) -> Dict[str, Any]:
        """
        获取AI提供商相关的配置。
        
        Returns:
            Dict[str, Any]: 提供商配置字典
        """
        return {
            "api_key": self.config.api_key,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": self.config.stream
        }
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        保存配置到文件。
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        import tomli_w
        
        path = Path(config_path or self.DEFAULT_CONFIG_PATH)
        
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 将配置转换为字典
        config_dict = {
            key: value
            for key, value in self.config.__dict__.items()
            if not key.startswith("_")
        }
        
        # 保存配置
        try:
            with open(path, "wb") as f:
                tomli_w.dump(config_dict, f)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

# 全局配置管理器实例
config_manager = ConfigManager()
