"""
翻译插件示例实现。
"""
from typing import Any, Dict, Optional

from ..plugins.base import BasePlugin, register_plugin

@register_plugin("translator")
class TranslatorPlugin(BasePlugin):
    """翻译插件，用于在AI处理前后进行文本翻译。"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化翻译插件。
        
        Args:
            config: 配置字典，可以包含：
                - source_lang: 源语言
                - target_lang: 目标语言
        """
        super().__init__(config)
        self.source_lang = self.config.get("source_lang", "auto")
        self.target_lang = self.config.get("target_lang", "en")
        
    @property
    def priority(self) -> int:
        """
        获取插件优先级。翻译应该是最先和最后执行的操作之一。
        
        Returns:
            int: 优先级值
        """
        return 0
    
    def pre_process(self, input_text: str) -> str:
        """
        在AI处理之前将输入翻译为目标语言。
        
        Args:
            input_text: 用户输入的原始文本
            
        Returns:
            str: 翻译后的文本
        """
        # 这里我们使用一个简单的标记来模拟翻译
        # 在实际应用中，你应该使用真实的翻译服务
        if self.source_lang != "en" and self.target_lang == "en":
            return f"[Translated to English]: {input_text}"
        return input_text
    
    def post_process(self, output_text: str) -> str:
        """
        在AI处理之后将回答翻译为源语言。
        
        Args:
            output_text: AI生成的原始回答
            
        Returns:
            str: 翻译后的文本
        """
        # 这里我们使用一个简单的标记来模拟翻译
        # 在实际应用中，你应该使用真实的翻译服务
        if self.source_lang != "en" and self.target_lang == "en":
            return f"[Translated back to {self.source_lang}]: {output_text}"
        return output_text
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效。
        
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        valid_languages = {"auto", "en", "zh", "ja", "ko", "es", "fr", "de"}
        
        if "source_lang" in self.config:
            if self.config["source_lang"] not in valid_languages:
                return False
                
        if "target_lang" in self.config:
            if self.config["target_lang"] not in valid_languages:
                return False
                
        return True

# 单元测试
def test_translator_plugin():
    """测试翻译插件的功能。"""
    # 创建插件实例
    plugin = TranslatorPlugin({
        "source_lang": "zh",
        "target_lang": "en"
    })
    
    # 测试预处理
    input_text = "你好，世界！"
    processed = plugin.pre_process(input_text)
    assert "[Translated to English]" in processed
    
    # 测试后处理
    output_text = "Hello, World!"
    processed = plugin.post_process(output_text)
    assert "[Translated back to zh]" in processed
    
    # 测试配置验证
    assert plugin.validate_config()
    
    # 测试无效配置
    invalid_plugin = TranslatorPlugin({
        "source_lang": "invalid",
        "target_lang": "en"
    })
    assert not invalid_plugin.validate_config()

if __name__ == "__main__":
    test_translator_plugin()
    print("翻译插件测试通过！")
