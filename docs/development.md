# AI Agent 开发文档

## 项目结构概述

AI Agent 是一个模块化的AI应用框架，主要由以下几个核心组件组成：

- 核心代理 (Agent)
- AI提供商 (Providers)
- 插件系统 (Plugins)
- 输出处理 (Output)

## 核心组件详解

### 1. Agent (ai_agent/core/agent.py)

Agent是整个框架的核心类，负责协调各个组件的工作。

#### 主要类：

##### Agent
- 功能：协调AI提供商、插件和输出处理器的工作
- 主要方法：
  - `process(input_text: str)`: 处理输入并生成回答
  - `process_stream(input_text: str)`: 流式处理输入并生成回答
  - `_apply_pre_process(input_text: str)`: 应用插件预处理
  - `_apply_post_process(output_text: str)`: 应用插件后处理

##### AgentBuilder
- 功能：简化Agent实例的创建过程
- 主要方法：
  - `with_provider()`: 设置AI提供商
  - `with_plugin()`: 添加插件
  - `with_output()`: 添加输出处理器
  - `with_config()`: 设置配置
  - `build()`: 构建Agent实例

### 2. Providers (ai_agent/providers/base.py)

AI提供商负责与具体的AI服务进行交互。

#### 主要类：

##### BaseProvider
- 功能：定义AI提供商的基础接口
- 抽象方法：
  - `generate_response(prompt: str)`: 生成对问题的回答
  - `stream_response(prompt: str)`: 流式生成回答

主要特点：
- 支持同步和异步响应
- 提供错误处理机制
- 支持配置验证

### 3. Plugins (ai_agent/plugins/base.py)

插件系统允许对输入输出进行自定义处理。

#### 主要类：

##### BasePlugin
- 功能：定义插件的基础接口
- 主要方法：
  - `pre_process(input_text: str)`: 输入预处理
  - `post_process(output_text: str)`: 输出后处理
  - `priority`: 插件优先级

##### PluginManager
- 功能：管理插件的注册和执行
- 主要方法：
  - `register(name: str, plugin: BasePlugin)`: 注册插件
  - `unregister(name: str)`: 注销插件
  - `get_plugin(name: str)`: 获取插件
  - `list_plugins()`: 列出所有插件

### 4. Output (ai_agent/output/base.py)

输出处理器负责处理和展示AI的响应。

#### 主要类：

##### BaseOutput
- 功能：定义输出处理器的基础接口
- 抽象方法：
  - `render(content: str)`: 渲染内容
  - `render_stream(content_stream)`: 流式渲染内容

##### OutputManager
- 功能：管理多个输出处理器
- 主要方法：
  - `register(name: str, output: BaseOutput)`: 注册输出处理器
  - `unregister(name: str)`: 注销输出处理器
  - `get_output(name: str)`: 获取输出处理器
  - `set_default(name: str)`: 设置默认输出处理器

## 工作流程

1. 用户输入通过Agent的process或process_stream方法进入系统
2. 输入经过已注册插件的pre_process处理
3. 处理后的输入传给AI提供商生成回答
4. 回答经过已注册插件的post_process处理
5. 最终结果通过输出处理器展示给用户

## 扩展开发

### 添加新的AI提供商

1. 继承BaseProvider类
2. 实现generate_response和stream_response方法
3. 使用@register_provider装饰器注册

### 开发新插件

1. 继承BasePlugin类
2. 实现pre_process和/或post_process方法
3. 设置优先级（可选）
4. 使用@register_plugin装饰器注册

### 创建新的输出处理器

1. 继承BaseOutput类
2. 实现render和render_stream方法
3. 使用@register_output装饰器注册

## 最佳实践

1. 错误处理：使用专门的异常类（ProviderError、PluginError、OutputError）
2. 配置管理：所有组件都支持配置字典
3. 插件优先级：合理设置以确保正确的处理顺序
4. 异步支持：所有IO操作都应该是异步的
