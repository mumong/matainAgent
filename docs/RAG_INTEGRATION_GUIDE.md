# RAG 知识库集成指南

## 📋 概述

本指南说明如何在现有的 `agent.py` 中集成 RAG（检索增强生成）知识库功能，让 Agent 在回答问题时能够参考知识库中的文档。

## 🎯 集成方案

### 方案特点

1. **最小侵入**：只需在 `agent.py` 中添加几行代码
2. **可选功能**：如果 RAG 初始化失败，Agent 仍可正常工作
3. **自动检索**：根据用户问题自动从知识库检索相关信息
4. **无缝集成**：检索到的信息自动注入到 Agent 的上下文中

## 📁 文件结构

```
app/
├── core/
│   ├── agent.py              # 主 Agent 文件（已集成 RAG）
│   ├── rag_integration.py    # RAG 集成模块（新增）
│   └── prompt.py             # 系统提示词
└── rag/
    ├── document_loader.py    # 文档加载器
    ├── vector_store.py       # 向量存储管理器
    └── rag_retriever.py     # RAG 检索器
```

## 🔧 集成步骤

### 1. 已完成的集成

在 `app/core/agent.py` 中已经集成了 RAG 功能：

```python
# 导入 RAG 模块
from app.core.rag_integration import initialize_rag_system, get_rag_context_async, is_rag_initialized

# 初始化 RAG 系统
initialize_rag_system(auto_init=True)

# 在 run_agent() 中使用
rag_context = await get_rag_context_async(user_question, k=4)
```

### 2. 工作原理

```
用户提问
    ↓
从知识库检索相关文档（语义匹配）
    ↓
将检索结果格式化为上下文
    ↓
注入到 Agent 的系统提示词中
    ↓
Agent 基于知识库内容 + 工具 + 大模型生成回答
```

## 💾 数据存储说明

### 当前实现：内存存储

**问题 1：Embedding 是否存储在内存？**

✅ **是的**，当前使用 `InMemoryVectorStore`，所有数据（包括向量）都存储在内存中。

**问题 2：每次运行都要重新 Embedding 吗？**

✅ **是的**，因为数据在内存中，进程退出后数据会丢失，下次启动需要重新：
1. 加载文档（TXT/PDF）
2. 进行 Embedding（向量化）
3. 构建向量索引

### 持久化方案（可选）

如果需要持久化，可以使用以下方法：

#### 方法 1：使用 InMemoryVectorStore 的 dump/load

```python
# 保存向量存储
vector_store_manager.vector_store.dump("rag_vectors.json")

# 加载向量存储
from langchain_core.vectorstores import InMemoryVectorStore
vector_store = InMemoryVectorStore.load("rag_vectors.json", embedding=embeddings)
```

#### 方法 2：使用持久化向量数据库

推荐使用：
- **Chroma**：轻量级，易于使用
- **FAISS**：Facebook 开源，性能好
- **Qdrant**：功能强大，支持持久化
- **Milvus**：企业级向量数据库

示例（使用 Chroma）：

```python
from langchain_chroma import Chroma

# 创建持久化向量存储
vector_store = Chroma(
    collection_name="rag_knowledge",
    embedding_function=embeddings,
    persist_directory="./chroma_db"  # 持久化目录
)
```

## 🔍 匹配方式说明

**问题：匹配是怎么做的？默认的语义匹配吗？**

✅ **是的**，使用**语义相似度匹配**（Semantic Similarity Search）。

### 工作原理

1. **向量化**：
   - 用户查询 → Embedding 模型 → 查询向量
   - 知识库文档 → Embedding 模型 → 文档向量

2. **相似度计算**：
   - 使用 **余弦相似度**（Cosine Similarity）计算查询向量和文档向量的相似度
   - 公式：`similarity = cos(θ) = (A·B) / (||A|| × ||B||)`
   - 值范围：[-1, 1]，越接近 1 越相似

3. **排序和筛选**：
   - 按相似度分数从高到低排序
   - 返回 top-k 个最相关的文档（默认 k=4）

### 为什么使用语义匹配？

- ✅ **理解语义**：不是简单的关键词匹配，而是理解文本的语义
- ✅ **同义词支持**：能匹配同义词和相近表达
- ✅ **上下文理解**：能理解上下文和语境

### 示例

```
用户查询："如何部署应用？"
知识库文档："应用部署步骤：1. 准备环境 2. 运行命令..."

即使没有完全相同的词，也能匹配到相关文档
```

## ⚙️ 配置说明

### 1. 文档目录

默认文档目录：`app/rag/files/`

支持的格式：
- `.txt`：纯文本文件
- `.pdf`：PDF 文档

### 2. Embedding 模型配置

在 `config/config.yaml` 中配置：

```yaml
model:
  rag:
    embedding_model: 'embedding-2'  # 或 'embedding-3'
  glm:
    api: "your-api-key"  # 智谱AI API Key
```

### 3. 检索参数

在 `app/core/agent.py` 中调整：

```python
# k=4 表示检索 top 4 个最相关的文档
rag_context = await get_rag_context_async(user_question, k=4)
```

## 🚀 使用示例

### 基本使用

```python
# 在 agent.py 中，RAG 功能已自动集成
# 只需正常提问，Agent 会自动从知识库检索相关信息

question = "如何部署 Kubernetes 应用？"
# Agent 会自动：
# 1. 从知识库检索相关文档
# 2. 结合知识库内容回答
```

### 禁用 RAG（如果需要）

```python
# 在 agent.py 中注释掉 RAG 初始化
# initialize_rag_system(auto_init=True)  # 注释掉这行
```

## 📊 性能优化

### 1. 文档块大小

默认配置：
- `chunk_size`: 1000 字符
- `chunk_overlap`: 200 字符

可以根据文档类型调整：
```python
loader = DocumentLoader(chunk_size=1500, chunk_overlap=300)
```

### 2. 检索数量

默认检索 top 4 个文档，可以根据需要调整：
```python
rag_context = await get_rag_context_async(query, k=6)  # 检索 top 6
```

### 3. 批量处理

文档加载和向量化支持批量处理，减少 API 调用次数。

## 🐛 故障排查

### 问题 1：RAG 未初始化

**现象**：Agent 回答时没有使用知识库

**解决**：
1. 检查 `app/rag/files/` 目录是否有文档
2. 检查 Embedding 模型配置是否正确
3. 查看初始化日志

### 问题 2：检索结果为空

**可能原因**：
- 知识库中没有相关文档
- 查询与文档语义差异太大

**解决**：
- 增加检索数量（k 值）
- 优化文档内容
- 调整文档块大小

### 问题 3：初始化太慢

**原因**：Embedding 需要时间，特别是大量文档

**解决**：
- 使用持久化存储，避免每次重新 Embedding
- 减小文档块大小
- 使用更快的 Embedding 模型

## 📝 总结

1. **存储**：当前使用内存存储，每次重启需重新 Embedding
2. **匹配**：使用语义相似度匹配（余弦相似度）
3. **集成**：已集成到 `agent.py`，自动工作
4. **持久化**：可以使用 dump/load 或向量数据库实现持久化

## 🔗 相关文档

- [RAG 系统 README](../app/rag/README.md)
- [故障排查指南](../app/rag/TROUBLESHOOTING.md)

