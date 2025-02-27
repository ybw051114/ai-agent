"""
对话保存输出处理器的单元测试。
"""
import os
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open

from ai_agent.output.conversation import ConversationOutput

def test_conversation_output_init():
    """测试ConversationOutput初始化。"""
    # 测试默认配置
    output = ConversationOutput()
    assert output.save_dir.endswith("ai-agent/conversations")
    assert output.timestamp_format == "%Y-%m-%d %H:%M:%S"
    assert output.conversation == []
    
    # 测试自定义配置
    config = {
        "save_dir": "~/custom/path",
        "timestamp_format": "%H:%M:%S"
    }
    output = ConversationOutput(config)
    assert output.save_dir.endswith("custom/path")
    assert output.timestamp_format == "%H:%M:%S"

@pytest.mark.asyncio
async def test_conversation_message_addition():
    """测试对话消息的添加逻辑。"""
    output = ConversationOutput()
    
    # 测试用户消息添加
    await output.render("用户输入")
    assert len(output.conversation) == 1
    assert output.conversation[0]["role"] == "user"
    assert output.conversation[0]["content"] == "用户输入"
    
    # 测试AI回答添加
    await output.render("AI回答")
    assert len(output.conversation) == 2
    assert output.conversation[1]["role"] == "assistant"
    assert output.conversation[1]["content"] == "AI回答"

@pytest.mark.asyncio
async def test_conversation_topic_generation():
    """测试主题生成流程。"""
    output = ConversationOutput()
    
    # 模拟一个完整的对话流程
    await output.render("用户问题")
    await output.render("AI的回答。")  # 以句号结尾触发主题生成
    
    assert len(output.conversation) == 3
    assert output.conversation[2]["role"] == "system"
    assert "你是一个专业人士" in output.conversation[2]["content"]
    
    # 模拟主题生成的回答
    await output.render("测试主题")
    assert len(output.conversation) == 0  # 确认对话被重置

@pytest.mark.asyncio
async def test_conversation_stream_handling():
    """测试流式内容处理。"""
    output = ConversationOutput()
    
    # 测试用户输入流
    async def user_stream():
        yield "Hello "
        yield "AI!"
    
    await output.render_stream(user_stream())
    
    # 验证用户消息
    assert len(output.conversation) == 1
    assert output.conversation[0]["content"] == "Hello AI!"
    assert output.conversation[0]["role"] == "user"
    
    # 测试AI回答流（带结束标点）
    async def ai_stream():
        yield "Nice to "
        yield "meet you."
    
    await output.render_stream(ai_stream())
    
    # 验证AI回答和主题生成提示
    assert len(output.conversation) == 3
    assert output.conversation[1]["content"] == "Nice to meet you."
    assert output.conversation[1]["role"] == "assistant"
    assert output.conversation[2]["role"] == "system"
    assert "你是一个专业人士" in output.conversation[2]["content"]
    
    # 测试主题回答
    async def topic_stream():
        yield "问候与打招呼"
    
    await output.render_stream(topic_stream())
    
    # 验证主题生成后的对话重置
    assert len(output.conversation) == 0  # 主题生成后会清空对话

    # 验证对话能继续新的轮次
    await output.render_stream(user_stream())
    assert len(output.conversation) == 1
    assert output.conversation[0]["role"] == "user"

@pytest.mark.asyncio
@patch("pathlib.Path.mkdir")
@patch("builtins.open", new_callable=mock_open)
async def test_conversation_saving(mock_file, mock_mkdir):
    """测试对话保存功能。"""
    output = ConversationOutput()
    
    # 模拟完整对话流程
    await output.render("用户问题")  # 添加用户问题
    await output.render("AI的回答。")  # AI回答以句号结束，触发主题生成提示
    assert output.conversation[-1]["role"] == "system"  # 验证添加了主题生成提示
    await output.render("测试主题")  # 生成的主题，触发保存
    
    # 验证调用
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_file.assert_called_once()
    
    # 验证写入的内容
    written_content = "".join([call.args[0] for call in mock_file().write.call_args_list])
    assert "# 测试主题" in written_content
    assert "用户问题" in written_content
    assert "AI的回答" in written_content
    assert "开始时间" in written_content
    assert "结束时间" in written_content
    
    # 验证对话被重置
    assert len(output.conversation) == 0

def test_validate_config():
    """测试配置验证。"""
    output = ConversationOutput()
    assert output.validate_config()
    
    # 测试各种配置组合
    configs = [
        {},
        {"save_dir": "~/custom/path"},
        {"timestamp_format": "%Y-%m-%d"},
        {"save_dir": "~/custom/path", "timestamp_format": "%Y-%m-%d"}
    ]
    
    for config in configs:
        output = ConversationOutput(config)
        assert output.validate_config()

@pytest.mark.asyncio
async def test_conversation_end_detection():
    """测试对话结束的检测逻辑。"""
    output = ConversationOutput()
    
    # 测试各种结束标记
    end_marks = ["。", ".", "!", "?", "！", "？"]
    
    for mark in end_marks:
        output = ConversationOutput()  # 重置输出
        await output.render("用户问题")
        await output.render(f"AI的回答{mark}")
        
        assert len(output.conversation) == 3
        assert output.conversation[2]["role"] == "system"
        assert "你是一个专业人士" in output.conversation[2]["content"]

if __name__ == "__main__":
    pytest.main([__file__])
