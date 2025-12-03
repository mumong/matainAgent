# RAG 中间件集成指南

## 📋 概述

本指南说明如何使用 `AgentMiddleware` 在 Agent 执行过程中智能集成 RAG 知识库，实现**按需检索**而非预先检索的策略。

## 🎯 设计理念

### 问题分析

传统的 RAG 集成方式：
```
用户提问 → 立即检索 RAG → 注入上下文 → Agent 分析 → 输出答案
```

**问题**：
- 在 Agent 还没分析问题之前就检索，可能检索到不相关的信息
- 对于运维场景，Agent 需要先通过工具获取实时数据，然后才能给出建议
- 过早注入 RAG 信息可能干扰 Agent 的分析思路

### 新的设计：按需检索

```
用户提问 → Agent 分析问题（使用工具） → 准备输出建议 → 触发 RAG 检索 → 增强建议
```

**优势**：
1. **先分析后检索**：Agent 先完成问题分析，知道需要什么类型的建议
2. **精准检索**：基于分析结果和用户问题，检索更相关的知识
3. **不影响分析**：RAG 信息只在输出建议时注入，不影响 Agent 的分析过程
4. **符合运维流程**：先诊断问题，再参考标准流程给出建议

## 🔧 实现方式

### 使用 AgentMiddleware

根据 [LangChain 官方文档](https://reference.langchain.com/python/langchain/agents/)，`create_agent` 支持 `middleware` 参数，可以注册多个中间件。

中间件提供了多个钩子（Hooks）：
- `before_agent`: Agent 执行前
- `before_model`: 模型调用前
- `after_model`: 模型调用后 ⭐ **我们使用这个**
- `after_agent`: Agent 执行完成后
- `wrap_tool_call`: 工具调用时

### RAG 中间件实现

```python
class RAGMiddleware(AgentMiddleware):
    async def aafter_model(self, state: AgentState, runtime: Runtime):
        """在模型调用后执行"""
        # 1. 检查 AI 回答是否包含"建议行动方案"等关键词
        # 2. 如果包含，从 RAG 检索相关知识
        # 3. 将检索结果注入到消息中，让 Agent 重新生成或增强回答
```

## 📊 工作流程

```
1. 用户提问："我的集群有什么问题？"
   ↓
2. Agent 开始分析（before_model）
   - 调用工具：kubectl get pods
   - 调用工具：kubectl logs
   - 分析问题根因
   ↓
3. Agent 生成初步回答（after_model）
   - 包含"问题摘要"
   - 包含"根本原因分析"
   - 包含"建议行动方案" ← 触发 RAG
   ↓
4. RAG 中间件检测到关键词（after_model）
   - 从知识库检索相关标准流程
   - 检索关键词：用户问题 + "运维建议"
   ↓
5. 将 RAG 信息注入到消息中
   - 要求 Agent 参考知识库完善建议
   ↓
6. Agent 重新生成或增强回答
   - 结合知识库的标准流程
   - 输出更专业、更标准的运维建议
```

## 🎨 触发策略

### 自动触发（默认）

中间件会自动检测以下关键词：
- "建议行动方案"
- "建议"
- "操作步骤"
- "最佳实践"
- "标准流程"
- "运维手册"
- "解决方案"
- "处理方案"

当 AI 回答包含这些关键词时，自动触发 RAG 检索。

### 手动触发（可选）

可以通过修改 `enable_auto_rag` 参数来控制：

```python
rag_middleware = RAGMiddleware(
    rag_k=4,
    enable_auto_rag=False  # 禁用自动触发
)
```

## 📝 代码示例

### 基本使用

```python
from app.core.rag_middleware import RAGMiddleware
from langchain.agents import create_agent

# 创建 RAG 中间件
rag_middleware = RAGMiddleware(rag_k=4, enable_auto_rag=True)

# 创建 Agent 并注册中间件
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=prompt,
    middleware=[rag_middleware]  # 注册中间件
)
```

### 自定义触发关键词

```python
class CustomRAGMiddleware(RAGMiddleware):
    def __init__(self):
        super().__init__()
        # 添加自定义触发关键词
        self._rag_trigger_keywords.extend([
            "我的建议",
            "推荐做法",
            "标准操作"
        ])
```

## 🔍 与其他 Agent 的 RAG 集成方式对比

### 方式 1：预先检索（传统方式）

**实现**：在调用 Agent 前检索 RAG

```python
# 检索 RAG
rag_context = retrieve_rag(user_query)

# 注入到用户消息
messages = [{"role": "user", "content": f"{user_query}\n{rag_context}"}]

# 调用 Agent
agent.invoke(messages)
```

**适用场景**：
- 知识库内容对理解问题很重要
- 需要背景知识才能回答问题
- 问答系统（Q&A）

**缺点**：
- 可能检索到不相关信息
- 干扰 Agent 的分析思路

### 方式 2：工具化 RAG（作为工具）

**实现**：将 RAG 检索作为 Agent 的一个工具

```python
def search_knowledge_base(query: str) -> str:
    """从知识库检索相关信息"""
    return retrieve_rag(query)

agent = create_agent(
    model=model,
    tools=[search_knowledge_base, ...]  # RAG 作为工具
)
```

**适用场景**：
- Agent 需要主动决定是否检索
- 需要多次检索不同主题
- 需要 Agent 控制检索时机

**缺点**：
- Agent 可能忘记使用这个工具
- 需要额外的工具调用成本

### 方式 3：中间件按需检索（我们的方式）⭐

**实现**：使用中间件在特定时机自动检索

```python
class RAGMiddleware(AgentMiddleware):
    async def aafter_model(self, state, runtime):
        if should_trigger_rag(state):
            rag_context = retrieve_rag(...)
            return {"messages": [...rag_context...]}

agent = create_agent(
    model=model,
    tools=tools,
    middleware=[RAGMiddleware()]  # 注册中间件
)
```

**适用场景**：
- 需要在特定阶段（如输出建议时）检索
- 希望自动触发，无需 Agent 主动调用
- 运维场景：先分析后建议

**优势**：
- ✅ 自动触发，无需 Agent 主动调用
- ✅ 精准时机：在需要时才检索
- ✅ 不影响 Agent 的分析过程
- ✅ 符合运维工作流程

## 🎯 运维场景的最佳实践

### 工作流程

1. **问题发现**：用户提问或告警触发
2. **数据收集**：Agent 调用工具获取实时数据
   - Prometheus 指标
   - ELK 日志
   - Kubernetes 资源状态
3. **问题分析**：Agent 分析数据，找出根因
4. **生成建议**：Agent 准备输出运维建议
5. **RAG 增强**：中间件自动检索标准流程
6. **完善建议**：Agent 结合知识库完善建议

### 示例

```
用户："我的 Pod 一直重启，怎么办？"

Agent 分析：
1. 调用 kubectl get pods → 发现 CrashLoopBackOff
2. 调用 kubectl logs → 发现连接数据库失败
3. 分析根因：数据库连接配置错误

Agent 准备输出建议：
"建议行动方案：
1. 检查数据库连接配置..."

RAG 中间件触发：
- 检测到"建议行动方案"
- 检索知识库："Pod 重启排查流程"
- 检索到标准流程文档

Agent 完善建议：
"建议行动方案（参考标准运维手册）：
1. 立即执行（止血）：
   - 检查数据库服务状态 [标准流程步骤1]
   - 验证网络连通性 [标准流程步骤2]
2. 短期排查（定位）：
   - 查看数据库日志 [标准流程步骤3]
   - 检查配置项 [标准流程步骤4]
..."
```

## ⚙️ 配置说明

### 中间件参数

```python
RAGMiddleware(
    rag_k=4,              # 检索的文档数量
    enable_auto_rag=True  # 是否自动触发
)
```

### 触发关键词

默认触发关键词在 `_rag_trigger_keywords` 中定义，可以根据需要修改。

## 🐛 故障排查

### 问题 1：RAG 未触发

**可能原因**：
- AI 回答中不包含触发关键词
- `enable_auto_rag=False`
- RAG 系统未初始化

**解决**：
- 检查 AI 回答内容
- 确认中间件配置
- 查看初始化日志

### 问题 2：检索结果不相关

**可能原因**：
- 检索关键词不准确
- 知识库内容不匹配

**解决**：
- 调整检索策略
- 优化知识库内容
- 增加检索数量（k 值）

## 📚 参考文档

- [LangChain Agents 官方文档](https://reference.langchain.com/python/langchain/agents/)
- [AgentMiddleware 类型定义](https://reference.langchain.com/python/langchain/agents/middleware/types/)
- [RAG 集成指南](./RAG_INTEGRATION_GUIDE.md)

## 🎉 总结

使用 `AgentMiddleware` 实现 RAG 集成具有以下优势：

1. **精准时机**：在 Agent 需要时才检索，不影响分析过程
2. **自动触发**：无需 Agent 主动调用，自动检测并触发
3. **符合流程**：先分析问题，再参考标准流程给出建议
4. **易于扩展**：可以轻松添加更多触发条件和检索策略

这种方式特别适合运维场景，让 Agent 能够：
- 先通过工具获取实时数据
- 分析问题根因
- 然后参考知识库的标准流程
- 给出专业、标准的运维建议

