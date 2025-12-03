# 异步工具调用问题修复

## 问题描述

运行 Agent 时出现错误：

```
NotImplementedError: StructuredTool does not support sync invocation.
```

## 问题原因

**MCP 工具是异步的**：从 `langchain_mcp_adapters` 获取的 MCP 工具是 `StructuredTool` 类型，它们只支持异步调用（`ainvoke`），不支持同步调用（`invoke`）。

**代码使用了同步方法**：代码中使用了 `agent.stream()`（同步方法），当 Agent 尝试调用 MCP 工具时，会失败。

## 解决方案

### 方案1：使用异步方法（推荐）

将同步调用改为异步调用：

**修改前：**
```python
# ❌ 同步调用（不支持 MCP 工具）
for token, metadata in agent.stream(
    {'messages': question},
    config,
    stream_mode="messages"
):
    print(f"{token.content}", end="")
```

**修改后：**
```python
# ✅ 异步调用（支持 MCP 工具）
async def run_agent():
    async for token in agent.astream(
        {'messages': [{"role": "user", "content": question}]},
        config,
        stream_mode="messages"
    ):
        if hasattr(token, 'content'):
            print(f"{token.content}", end="", flush=True)

# 运行
asyncio.run(run_agent())
```

### 方案2：使用 ainvoke（非流式）

如果不需要流式输出：

```python
async def run_agent():
    result = await agent.ainvoke(
        {'messages': [{"role": "user", "content": question}]},
        config
    )
    for msg in result['messages']:
        msg.pretty_print()

asyncio.run(run_agent())
```

## 关键点

### 1. MCP 工具的特性

- MCP 工具是 `StructuredTool` 类型
- 只实现了 `_arun()`（异步），没有实现 `_run()`（同步）
- 必须使用异步方法调用

### 2. Agent 方法对比

| 方法 | 类型 | 支持 MCP 工具 | 使用场景 |
|------|------|--------------|---------|
| `agent.invoke()` | 同步 | ❌ | 简单调用，无 MCP 工具 |
| `agent.stream()` | 同步 | ❌ | 流式输出，无 MCP 工具 |
| `agent.ainvoke()` | 异步 | ✅ | 完整响应，有 MCP 工具 |
| `agent.astream()` | 异步 | ✅ | 流式输出，有 MCP 工具 |

### 3. 消息格式

**注意消息格式：**
```python
# ❌ 错误格式
{'messages': question}  # question 是字符串

# ✅ 正确格式
{'messages': [{"role": "user", "content": question}]}  # 消息列表
```

## 完整示例

```python
import asyncio
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

# 创建 Agent（包含 MCP 工具）
agent = create_agent(
    model=model,
    tools=all_tools,  # 包含 MCP 工具
    system_prompt="...",
    checkpointer=InMemorySaver(),
)

async def main():
    """主函数"""
    question = "我的集群有什么问题？"
    
    # 方式1：流式输出
    async for token in agent.astream(
        {'messages': [{"role": "user", "content": question}]},
        {"configurable": {"thread_id": "1"}},
        stream_mode="messages"
    ):
        if hasattr(token, 'content'):
            print(token.content, end="", flush=True)
    
    # 方式2：完整响应
    # result = await agent.ainvoke(
    #     {'messages': [{"role": "user", "content": question}]},
    #     {"configurable": {"thread_id": "1"}}
    # )
    # for msg in result['messages']:
    #     msg.pretty_print()

if __name__ == "__main__":
    asyncio.run(main())
```

## 验证修复

运行修复后的代码：

```bash
python3 app/core/agent.py
```

应该能够正常工作，Agent 可以成功调用 MCP 工具。

## 总结

- ✅ **问题**：MCP 工具只支持异步调用
- ✅ **解决**：使用 `agent.astream()` 或 `agent.ainvoke()` 代替同步方法
- ✅ **注意**：确保消息格式正确，使用 `asyncio.run()` 运行异步函数

