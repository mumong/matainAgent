# Agent 流式输出过滤

## 问题

使用 `stream_mode="messages"` 时，输出包含大量元数据信息，难以阅读：

```
(ToolMessage(content='', name='kubectl_get', ...), {'thread_id': '1', ...})
(AIMessage(content='让我查看...', ...), {'thread_id': '1', ...})
```

## 解决方案

修改代码，只输出 **AIMessage 的 content**，过滤其他信息。

## 代码修改

### 修改前

```python
async for token in agent.astream(..., stream_mode="messages"):
    if hasattr(token, 'content'):
        print(f"{token.content}", end="", flush=True)
    else:
        print(f"{token}", end="", flush=True)
```

**问题：**
- 会输出所有消息类型（ToolMessage、AIMessage 等）
- 会输出元数据信息
- 输出混乱，难以阅读

### 修改后

```python
async for chunk in agent.astream(..., stream_mode="messages"):
    # stream_mode="messages" 返回 (message, metadata) 元组
    message = None
    
    # 处理不同的返回格式
    if isinstance(chunk, tuple) and len(chunk) >= 1:
        message = chunk[0]  # 提取消息对象
    elif isinstance(chunk, (AIMessage, HumanMessage, SystemMessage)):
        message = chunk  # 直接是消息对象
    
    # 只输出 AIMessage 的 content
    if isinstance(message, AIMessage) and message.content:
        if isinstance(message.content, str):
            print(message.content, end="", flush=True)
        elif isinstance(message.content, list):
            # 处理列表格式的 content
            for item in message.content:
                if isinstance(item, str):
                    print(item, end="", flush=True)
                elif isinstance(item, dict) and "text" in item:
                    print(item["text"], end="", flush=True)
```

**效果：**
- ✅ 只输出 AIMessage 的文本内容
- ✅ 忽略 ToolMessage、元数据等
- ✅ 输出清晰易读

## Stream Mode 说明

LangGraph 支持多种 `stream_mode`：

| stream_mode | 说明 | 返回格式 |
|------------|------|---------|
| `"messages"` | 逐 token 输出消息 | `(message, metadata)` 元组 |
| `"values"` | 输出完整状态 | 字典（包含所有消息） |
| `"updates"` | 输出状态更新 | 字典（只包含更新的部分） |
| `"checkpoints"` | 输出检查点 | 检查点对象 |

### 为什么使用 "messages"？

- ✅ 实时流式输出，逐 token 显示
- ✅ 适合交互式对话
- ✅ 可以看到 Agent 的思考过程

### 其他模式示例

```python
# 方式1：完整响应（非流式）
result = await agent.ainvoke(
    {'messages': [{"role": "user", "content": question}]},
    config
)
print(result['messages'][-1].content)

# 方式2：流式输出完整状态
async for state in agent.astream(..., stream_mode="values"):
    last_message = state['messages'][-1]
    if isinstance(last_message, AIMessage):
        print(last_message.content, end="", flush=True)
```

## 注意事项

### MCP 服务器输出

MCP 服务器的标准输出（如 "Starting Kubernetes MCP server..."）会直接打印到控制台，不在 Agent 流式输出中。这是正常的，表示 MCP 服务器正在运行。

如果需要隐藏这些信息，可以：

1. **重定向 MCP 服务器输出**（在 MCP 配置中）
2. **使用日志级别控制**（如果 MCP 服务器支持）

### Content 格式

不同模型可能返回不同格式的 content：

- **字符串**：`"Hello, world!"`
- **列表（字符串）**：`["Hello", ", ", "world", "!"]`
- **列表（字典）**：`[{"type": "text", "text": "Hello, world!"}]`

代码已经处理了这些情况。

## 验证

运行修改后的代码：

```bash
python3 app/core/agent.py
```

现在应该只看到清晰的 AI 回复内容，没有元数据干扰。

