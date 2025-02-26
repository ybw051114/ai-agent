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

```yaml
provider: deepseek  # 使用 DeepSeek 作为提供商
api_key: your-api-key-here
model: deepseek-chat  # 可选，默认为 deepseek-chat
temperature: 0.7     # 可选，默认为 0.7
max_tokens: 2000     # 可选，默认为 2000
stream: true        # 可选，默认为 true
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
