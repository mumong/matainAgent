# RAG 向量匹配机制详解

## 📍 代码位置总览

### 1. 匹配触发入口

**文件**：`app/core/rag_middleware.py`

**位置**：第 121 行
```python
rag_context = await get_rag_context_async(user_query, k=self.rag_k)
```

**说明**：RAG 中间件在检测到需要输出运维建议时，调用检索函数。

---

### 2. 检索函数

**文件**：`app/core/rag_integration.py`

**位置**：第 110-143 行
```python
async def get_rag_context_async(query: str, k: int = 4) -> str:
    retriever = get_rag_retriever(k=k)
    documents = await retriever.aretrieve(query)  # 第 126 行
    # ... 格式化返回
```

**说明**：获取 RAG 检索器并调用异步检索方法。

---

### 3. RAG 检索器

**文件**：`app/rag/rag_retriever.py`

**位置**：第 43-61 行
```python
async def aretrieve(self, query: str) -> List[Document]:
    documents = await self.vector_store_manager.asearch(query, k=self.k)  # 第 57 行
    return documents
```

**说明**：调用向量存储管理器的异步搜索方法。

---

### 4. 向量存储管理器

**文件**：`app/rag/vector_store.py`

**位置**：第 218-232 行
```python
async def asearch(self, query: str, k: int = 4) -> List[Document]:
    return await self.vector_store.asimilarity_search(query, k=k)  # 第 232 行
```

**说明**：调用底层向量存储的相似度搜索方法。

---

### 5. 底层向量存储（LangChain 默认实现）

**文件**：`venv/lib/python3.10/site-packages/langchain_core/vectorstores/in_memory.py`

**位置**：第 290-331 行（核心匹配逻辑）

```python
def _similarity_search_with_score_by_vector(
    self,
    embedding: list[float],  # 查询向量
    k: int = 4,
    filter: Callable[[Document], bool] | None = None,
) -> list[tuple[Document, float, list[float]]]:
    docs = list(self.store.values())
    
    # 计算余弦相似度
    similarity = cosine_similarity([embedding], [doc["vector"] for doc in docs])[0]
    
    # 按相似度排序，取 top-k
    top_k_idx = similarity.argsort()[::-1][:k]
    
    return [(Document(...), float(similarity[idx].item()), doc_dict["vector"]) 
            for idx in top_k_idx]
```

**说明**：这是**默认的匹配实现**，使用余弦相似度。

---

### 6. 余弦相似度计算

**文件**：`venv/lib/python3.10/site-packages/langchain_core/vectorstores/utils.py`

**位置**：第 33-78 行

```python
def _cosine_similarity(x: Matrix, y: Matrix) -> np.ndarray:
    """计算两个矩阵之间的行级余弦相似度"""
    x = np.array(x)
    y = np.array(y)
    # 使用 numpy 计算余弦相似度
    # 公式：cos(θ) = (A·B) / (||A|| × ||B||)
```

**说明**：使用 NumPy 实现余弦相似度计算。

---

## 🔍 匹配流程详解

### 完整流程

```
1. RAG 中间件触发
   ↓
   app/core/rag_middleware.py:121
   get_rag_context_async(user_query, k=4)
   
2. 检索函数
   ↓
   app/core/rag_integration.py:126
   retriever.aretrieve(query)
   
3. RAG 检索器
   ↓
   app/rag/rag_retriever.py:57
   vector_store_manager.asearch(query, k=4)
   
4. 向量存储管理器
   ↓
   app/rag/vector_store.py:232
   vector_store.asimilarity_search(query, k=4)
   
5. 向量化查询
   ↓
   InMemoryVectorStore 内部
   embedding.embed_query(query)  # 将查询文本转为向量
   
6. 计算相似度
   ↓
   in_memory.py:313
   cosine_similarity([query_vector], [doc_vectors])
   
7. 排序和筛选
   ↓
   in_memory.py:316
   top_k_idx = similarity.argsort()[::-1][:k]
   
8. 返回结果
   ↓
   返回 top-k 个最相似的文档
```

---

## 🎯 关键问题解答

### 问题 1：大模型输出和 RAG 向量匹配是怎么做的？

**答案**：**不是用大模型的输出进行匹配，而是用用户原始查询进行匹配！**

**代码位置**：`app/core/rag_middleware.py` 第 115 行

```python
# 提取用户原始查询
user_query = self._extract_user_query(messages)  # 提取的是用户最初的问题

# 用用户查询进行检索
rag_context = await get_rag_context_async(user_query, k=self.rag_k)
```

**流程**：
1. 用户提问："我的 Pod 一直重启，怎么办？"
2. Agent 分析问题（使用工具、调用模型）
3. Agent 准备输出建议："建议行动方案：..."
4. RAG 中间件检测到关键词，**提取用户原始查询**："我的 Pod 一直重启，怎么办？"
5. 用**用户原始查询**进行向量匹配
6. 返回相关的运维手册文档

---

### 问题 2：大模型决定做 A-B-C 过程和 RAG 内容如何向量匹配？

**答案**：**当前实现中，匹配使用的是用户原始查询，不是大模型的输出（A-B-C 过程）**

**当前实现**：
- 匹配查询：用户原始问题（如："我的 Pod 一直重启，怎么办？"）
- 匹配方式：语义相似度（余弦相似度）
- 匹配对象：知识库中的所有文档块

**如果你想用大模型的输出（A-B-C 过程）进行匹配**，需要修改：

**修改位置**：`app/core/rag_middleware.py` 第 115-121 行

```python
# 当前实现：使用用户原始查询
user_query = self._extract_user_query(messages)
rag_context = await get_rag_context_async(user_query, k=self.rag_k)

# 如果要用大模型输出匹配，可以这样：
# 1. 提取 AI 的回答（包含 A-B-C 过程）
ai_message = messages[-1]  # 最后一条 AI 消息
ai_content = ai_message.content  # "建议行动方案：1. 检查 A 2. 执行 B 3. 验证 C"

# 2. 从 AI 回答中提取关键步骤
steps = extract_steps(ai_content)  # ["检查 A", "执行 B", "验证 C"]

# 3. 用步骤进行匹配
for step in steps:
    step_docs = await get_rag_context_async(step, k=2)
    # 合并结果
```

---

### 问题 3：代码在哪里？是否使用默认的？

**答案**：**是的，使用 LangChain 的默认实现**

#### 匹配算法位置

1. **余弦相似度计算**：
   - 文件：`venv/lib/python3.10/site-packages/langchain_core/vectorstores/utils.py`
   - 函数：`_cosine_similarity(x, y)`
   - 第 33-78 行

2. **相似度搜索实现**：
   - 文件：`venv/lib/python3.10/site-packages/langchain_core/vectorstores/in_memory.py`
   - 函数：`_similarity_search_with_score_by_vector()`
   - 第 290-331 行

3. **向量化**：
   - 文件：`app/rag/zhipu_embeddings.py`
   - 函数：`embed_query(text)` 和 `embed_documents(texts)`
   - 使用智谱AI的 embedding 模型

#### 默认匹配方式

✅ **使用默认的余弦相似度匹配**

- **算法**：余弦相似度（Cosine Similarity）
- **公式**：`similarity = cos(θ) = (A·B) / (||A|| × ||B||)`
- **实现**：LangChain 的 `InMemoryVectorStore` 默认实现
- **排序**：按相似度分数从高到低排序
- **返回**：top-k 个最相似的文档（默认 k=4）

---

## 📊 匹配过程示例

### 示例：用户查询 "Pod 重启排查"

```
1. 用户查询："Pod 重启排查"
   ↓
2. 向量化（embed_query）
   查询向量：[0.1, 0.3, 0.5, ..., 0.2]  # 1024 维向量
   ↓
3. 知识库文档向量（已预先计算）
   文档1向量：[0.2, 0.4, 0.3, ..., 0.1]
   文档2向量：[0.5, 0.1, 0.2, ..., 0.8]
   文档3向量：[0.1, 0.3, 0.6, ..., 0.2]
   ...
   ↓
4. 计算余弦相似度
   查询 vs 文档1：cos(θ) = 0.85
   查询 vs 文档2：cos(θ) = 0.42
   查询 vs 文档3：cos(θ) = 0.91
   ...
   ↓
5. 排序（按相似度降序）
   文档3：0.91
   文档1：0.85
   文档2：0.42
   ...
   ↓
6. 返回 top-4
   [文档3, 文档1, 文档2, 文档4]
```

---

## 🔧 如何查看匹配过程

### 方法 1：查看相似度分数

修改 `app/rag/rag_retriever.py`，使用 `search_with_score`：

```python
# 在 rag_retriever.py 中
def retrieve(self, query: str) -> List[Document]:
    # 使用 search_with_score 查看相似度分数
    results = self.vector_store_manager.search_with_score(query, k=self.k)
    for doc, score in results:
        print(f"相似度: {score:.4f} - {doc.page_content[:50]}...")
    return [doc for doc, _ in results]
```

### 方法 2：查看向量存储源码

直接查看 LangChain 源码：
- `venv/lib/python3.10/site-packages/langchain_core/vectorstores/in_memory.py`
- 第 290-331 行：`_similarity_search_with_score_by_vector()`

---

## 📝 总结

1. **匹配查询**：当前使用**用户原始查询**，不是大模型的输出
2. **匹配算法**：**余弦相似度**（LangChain 默认实现）
3. **匹配位置**：
   - 入口：`app/core/rag_middleware.py:121`
   - 核心：`venv/lib/.../in_memory.py:313`（余弦相似度计算）
4. **向量化**：使用智谱AI的 embedding 模型（`app/rag/zhipu_embeddings.py`）
5. **是否默认**：✅ 是，使用 LangChain 的默认实现

如果想用大模型的输出（A-B-C 过程）进行匹配，需要修改 `rag_middleware.py` 中的查询提取逻辑。

