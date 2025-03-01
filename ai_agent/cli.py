"""
命令行接口实现。
"""
import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
import os

from .core.agent import AgentBuilder
from .core.config import config_manager
from .output.terminal import TerminalOutput
from .providers.openai import OpenAIProvider
from .providers.deepseek import DeepSeekProvider
from .providers.sustech import SustechProvider
from .providers.ark import ArkProvider

console = Console()

def print_error(message: str) -> None:
    """打印错误信息。"""
    console.print(f"[red]错误:[/red] {message}")

def print_warning(message: str) -> None:
    """打印警告信息。"""
    console.print(f"[yellow]警告:[/yellow] {message}")

def validate_model(provider: str, model: str) -> bool:
    """
    验证模型是否被提供商支持。
    
    Args:
        provider: 提供商名称
        model: 模型名称
        
    Returns:
        bool: 模型有效返回True，否则返回False
    """
    provider_models = {
        "openai": ["gpt-3.5-turbo", "gpt-4"],
        "deepseek": ["deepseek-chat", "deepseek-coder"],
        "sustech": ["deepseek-r1-250120"],
        "ark": ["claude-2.1"]
    }
    if model == "ark":
        return True
    
    return model in provider_models.get(provider, [])

def setup_agent(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    plugins: Optional[str] = None,
    output: Optional[str] = None,
    config_path: Optional[str] = None,
) -> AgentBuilder:
    """
    设置AI代理。
    
    Args:
        provider: AI提供商名称
        model: 模型名称
        plugins: 插件列表，逗号分隔
        output: 输出处理器名称
        config_path: 配置文件路径
        
    Returns:
        AgentBuilder: 代理构建器实例
    """
    # 1. 加载配置
    config_manager.load_config(config_path)
    
    # 2. 命令行参数覆盖配置文件
    if provider:
        if provider not in ["openai", "deepseek", "sustech", "ark"]:
            print_error(f"不支持的AI提供商：{provider}")
            sys.exit(1)
        config_manager.config.provider = provider
        
    if model:
        if not validate_model(config_manager.config.provider, model):
            print_error(f"提供商 {config_manager.config.provider} 不支持模型：{model}")
            print_warning("可用模型：")
            provider_models = {
                "openai": ["gpt-3.5-turbo", "gpt-4"],
                "deepseek": ["deepseek-chat", "deepseek-coder"],
                "sustech": ["deepseek-r1-250120"],
                "ark": ["claude-2.1"]
            }
            for m in provider_models.get(config_manager.config.provider, []):
                print_warning(f"  - {m}")
            sys.exit(1)
        config_manager.config.model = model
        
    if plugins:
        config_manager.config.plugins = plugins.split(",")
    if output:
        config_manager.config.output = output
        
    # 3. 验证必要的配置
    if not config_manager.config.api_key:
        provider = config_manager.config.provider
        env_var = {
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "sustech": "SUSTECH_API_KEY",
            "ark": "ARK_API_KEY"
        }.get(provider, "API_KEY")
        print_error(f"未设置API密钥。请设置{env_var}环境变量或在配置文件中指定。")
        sys.exit(1)
    
    # 4. 初始化代理构建器
    builder = AgentBuilder()
    
    # 5. 设置AI提供商
    provider_map = {
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "sustech": SustechProvider,
        "ark": ArkProvider
    }
    
    provider_class = provider_map.get(config_manager.config.provider)
    if provider_class:
        provider = provider_class(config_manager.get_provider_config())
        builder.with_provider(provider)
    else:
        print_error(f"不支持的AI提供商：{config_manager.config.provider}")
        sys.exit(1)
    
    # 6. 设置输出处理器
    output = TerminalOutput()
    builder.with_output(output, "terminal", default=True)
    
    # 7. 加载插件
    for plugin_name in config_manager.config.plugins:
        try:
            # 动态导入插件模块
            module = __import__(f"ai_agent.plugins.{plugin_name}", fromlist=["Plugin"])
            plugin = module.Plugin()
            builder.with_plugin(plugin)
        except ImportError:
            print_warning(f"找不到插件：{plugin_name}")
        except Exception as e:
            print_warning(f"加载插件 {plugin_name} 失败：{e}")
    
    return builder

@click.group()
@click.version_option()
def cli():
    """AI代理命令行工具。"""
    pass

@cli.command()
@click.argument("prompt", required=False)
@click.option("-p", "--provider", help="AI提供商 (支持: openai, deepseek, sustech, ark)")
@click.option("-m", "--model", help="模型名称 (openai: gpt-3.5-turbo等, deepseek: deepseek-chat等, sustech: deepseek-r1-250120, ark: claude-2.1)")
@click.option("--plugins", help="要使用的插件，逗号分隔")
@click.option("-o", "--output", help="输出处理器")
@click.option("--config", help="配置文件路径")
@click.option("--no-stream", is_flag=True, help="禁用流式输出")
def chat(
    prompt: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    plugins: Optional[str],
    output: Optional[str],
    config: Optional[str],
    no_stream: bool,
):
    """与AI代理聊天。"""
    # 1. 设置代理
    builder = setup_agent(provider, model, plugins, output, config)
    if no_stream:
        config_manager.config.stream = False
    
    # 2. 构建代理
    agent = builder.build()
    
    async def run_chat():
        # 3. 处理输入
        if prompt:
            # 单次对话模式
            if config_manager.config.stream:
                await agent.process_stream(prompt)
            else:
                await agent.process(prompt)
        else:
            # 交互式模式
            console.print("[blue]欢迎使用AI代理。输入'exit'或按Ctrl+C退出。[/blue]")
            while True:
                try:
                    # 创建历史记录文件
                    history_file = os.path.expanduser("~/.ai_agent_history")
                    
                    # 创建prompt session
                    session = PromptSession(
                        history=FileHistory(history_file),
                        auto_suggest=AutoSuggestFromHistory(),
                        enable_history_search=True,
                        complete_while_typing=True,
                    )
                    
                    # 获取用户输入
                    user_input = await session.prompt_async(">>> ")
                    if user_input.strip().lower() in ("exit", "quit"):
                        break
                        
                    # 处理用户输入
                    if config_manager.config.stream:
                        await agent.process_stream(user_input)
                    else:
                        await agent.process(user_input)
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print_error(str(e))

    # 4. 运行事件循环
    try:
        asyncio.run(run_chat())
    except KeyboardInterrupt:
        console.print("\n[blue]再见！[/blue]")
    except Exception as e:
        print_error(f"发生错误：{e}")
        sys.exit(1)
    finally:
        if agent:
            try:
                if not prompt:
                    # 生成总结并保存对话
                    if hasattr(agent, '_generate_summary'):
                        asyncio.run(agent._generate_summary())
                    if hasattr(agent, '_save_conversation'):
                        save_path = agent._save_conversation()
                        if save_path:
                            console.print(f"\n[green]对话已保存到：{save_path}[/green]")
                # # 生成总结并保存对话
                # if prompt:
                #     if hasattr(agent, '_generate_summary'):
                #         asyncio.run(agent._generate_summary())
                # else:
                #     # 保存对话
                #     if hasattr(agent, '_save_conversation_stream')
                # if hasattr(agent, '_save_conversation'):
                #     save_path = agent._save_conversation()
                #     if save_path:
                #         console.print(f"\n[green]对话已保存到：{save_path}[/green]")
            except Exception as e:
                print_error(f"保存对话失败：{e}")

@cli.command()
@click.option("--config", help="配置文件路径")
def config(config: Optional[str]):
    """查看或编辑配置。"""
    if config:
        # 保存配置到指定位置
        config_manager.save_config(config)
        console.print(f"[green]配置已保存到：{config}[/green]")
    else:
        # 显示当前配置
        console.print("当前配置：")
        for key, value in config_manager.config.__dict__.items():
            if not key.startswith("_"):
                console.print(f"  {key}: {value}")

def main():
    """主入口函数。"""
    cli()

if __name__ == "__main__":
    main()
