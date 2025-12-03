# RAG 系统故障排查指南

## 🔴 常见错误：Connection Reset / Connection Aborted

### 错误现象

```
ConnectionResetError: [Errno 104] Connection reset by peer
urllib3.exceptions.ProtocolError: ('Connection aborted.', ConnectionResetError(...))
```

### 问题原因

1. **网络连接不稳定**：tiktoken 尝试从网络下载编码文件时连接被重置
2. **API 服务限制**：一次性处理太多文档导致连接被重置
3. **防火墙/代理问题**：网络环境限制

### 解决方案

#### 方案 1：使用批量处理（已实现）

系统已自动实现批量处理，每批处理 10 个文档块，带重试机制。

**如果仍然失败，可以调整批量大小：**

```python
# 在 vector_store.py 的 initialize 方法中
vector_store_manager.initialize(documents, batch_size=5)  # 减小批量大小
```

#### 方案 2：预先下载 tiktoken 文件

```bash
# 设置缓存目录
export TIKTOKEN_CACHE_DIR=/path/to/cache

# 或者在 Python 中设置
import os
os.environ["TIKTOKEN_CACHE_DIR"] = "/path/to/cache"
```

系统已自动设置缓存目录到 `.tiktoken_cache`。

#### 方案 3：使用本地 Embedding 模型

如果网络问题持续，可以使用本地 embedding 模型（如 Ollama）：

```yaml
# config/config.yaml
model:
  rag:
    embedding_model: "ollama:nomic-embed-text"  # 本地模型
```

**安装 Ollama：**
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载 embedding 模型
ollama pull nomic-embed-text
```

#### 方案 4：重试机制（已实现）

系统已实现自动重试：
- Embedding 初始化：最多重试 3 次，等待时间递增（3s, 6s, 9s）
- 文档批量处理：每批最多重试 3 次，等待时间递增（2s, 4s, 6s）

#### 方案 5：检查网络和 API 配置

```bash
# 测试网络连接
curl https://api.deepseek.com

# 检查 API Key 是否正确
python3 -c "from config.config_loader import get_config; print(get_config().get('model.deepseek.api')[:10])"
```

## 🟡 其他常见问题

### 问题 1: PDF 文件无法加载

**错误：** `ImportError: PyMuPDF (fitz) is required`

**解决：**
```bash
pip install pymupdf
```

### 问题 2: Embedding 模型不支持

**错误：** `ValueError: Provider 'xxx' is not supported`

**解决：**
- 检查模型名称格式：`provider:model-name`
- 确认已安装对应的集成包（如 `langchain-openai`）

### 问题 3: 内存不足

**现象：** 处理大量文档时内存占用过高

**解决：**
- 减小 `chunk_size`（默认 1000）
- 减小 `batch_size`（默认 10）
- 使用持久化向量存储（如 Chroma、FAISS）

## 📊 性能优化建议

### 1. 调整批量大小

```python
# 网络不稳定时，减小批量大小
loader = DocumentLoader(chunk_size=800, chunk_overlap=150)
vector_store_manager.initialize(documents, batch_size=5)
```

### 2. 使用持久化存储

考虑使用 Chroma 或 FAISS 替代 InMemoryVectorStore：

```python
from langchain_chroma import Chroma

vector_store = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
```

### 3. 异步处理

对于大量文档，可以考虑异步批量处理。

## 🔧 调试技巧

### 1. 检查初始化状态

```python
from app.rag.vector_store import get_vector_store_manager

manager = get_vector_store_manager()
print(f"已初始化: {manager.is_initialized()}")
```

### 2. 测试单个文档

```python
from app.rag.document_loader import DocumentLoader

loader = DocumentLoader()
docs = loader.load_txt_file(Path("app/rag/files/test.txt"))
print(f"加载了 {len(docs)} 个文档块")
```

### 3. 测试 Embedding

```python
from app.rag.vector_store import VectorStoreManager

manager = VectorStoreManager()
embeddings = manager._init_embeddings()
test_vector = embeddings.embed_query("测试文本")
print(f"向量维度: {len(test_vector)}")
```

## 📝 日志说明

系统会输出详细的日志信息：

- ✅ 成功操作
- ⚠️  警告信息（可恢复的错误）
- ❌ 错误信息（需要处理）
- 🔄 进行中的操作

## 🆘 仍然无法解决？

如果以上方案都无法解决问题，可以：

1. **检查完整错误日志**：查看 traceback 信息
2. **测试网络连接**：确认可以访问 API 服务
3. **使用本地模型**：切换到不需要网络的 embedding 模型
4. **减少文档数量**：先处理少量文档测试

