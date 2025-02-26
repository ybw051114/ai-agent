# AI-Agent

一个遵循Unix哲学的命令行AI代理。

## 特性

- 简单的命令行界面
- 支持多种AI提供商
- 可扩展的插件系统
- 灵活的输出处理

## 安装

```bash
pip install ai-agent
```

## 使用

```bash
# 基本使用
ai-agent "你的问题"

# 使用不同的AI提供商
ai-agent --provider openai "你的问题"
ai-agent --provider deepseek --model deepseek-chat "你的问题"

# 使用特定插件
ai-agent --plugin translator "你的问题"
```

## 配置

创建 `.env` 文件并设置以下环境变量：

```
OPENAI_API_KEY=你的OpenAI API密钥
DEEPSEEK_API_KEY=你的DeepSeek API密钥
```

或在配置文件中设置:

```toml
# AI提供商配置
provider = "deepseek"  # 可选: openai, deepseek等
api_key = "sk-1185ca8f54164a3b9db38e02088007d5"  # 你的API密钥
model = "deepseek-chat"  # 使用的模型名称

# 模型参数配置
temperature = 0.7  # 温度参数(0-1),越高越随机
max_tokens = 2000  # 单次请求最大token数
stream = true  # 是否启用流式输出

# 输出配置
output = "terminal"  # 输出方式,目前支持terminal

# 插件配置
plugins = []  # 启用的插件列表,例如 ["translator"]
```

## 开发

1. 克隆仓库
2. 安装依赖：`poetry install`
3. 运行测试：`poetry run pytest`

## 扩展开发

### 添加新的AI提供商

1. 在 `ai_agent/providers` 目录下创建新文件
2. 继承 `BaseProvider` 类并实现必要方法
3. 在配置中注册新提供商

### 创建插件

1. 在 `ai_agent/plugins` 目录下创建新文件
2. 继承 `BasePlugin` 类并实现所需的处理方法
3. 在配置中注册新插件

## 贡献

欢迎提交Pull Requests和Issues！

## 许可证

MIT
