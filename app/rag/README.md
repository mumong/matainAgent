# RAG 知识库系统

## 📋 概述

本 RAG 系统用于从 `files/` 目录下的文档（txt 和 pdf）构建知识库，并在 Agent 回答问题时提供相关知识参考。

## 🏗️ 系统架构

```
files/ (文档目录)
    ├── *.txt 文件
    └── *.pdf 文件
        ↓
DocumentLoader (文档加载器)
    ├── 读取 txt 文件
    └── 读取 pdf 文件（使用 PDFProcessor）
        ↓
文本分割 (TextSplitter)
    ├── chunk_size: 1000
    └── chunk_overlap: 200
        ↓
VectorStoreManager (向量存储管理器)
    ├── Embedding 模型初始化
    └── InMemoryVectorStore
        ↓
RAGRetriever (RAG 检索器)
    └── 相似度搜索
        ↓
rag.py (集成到响应生成)
    └── 将检索结果作为上下文
```

## 📁 文件结构

```
app/rag/
├── __init__.py              # 模块初始化
├── rag.py                   # 主文件（FastAPI 应用 + RAG 集成）
├── document_loader.py        # 文档加载器
├── pdf_utils.py             # PDF 处理工具
├── vector_store.py          # 向量存储管理器
├── rag_retriever.py         # RAG 检索器
├── files/                   # 文档目录
│   ├── *.txt               # 文本文件
│   └── *.pdf               # PDF 文件
└── README.md               # 本文档
```

## 🔧 核心模块说明

### 1. DocumentLoader (`document_loader.py`)

**功能：** 从 `files/` 目录加载所有 txt 和 pdf 文件

**主要方法：**
- `load_txt_file(file_path)`: 加载单个 txt 文件
- `load_pdf_file(file_path)`: 加载单个 pdf 文件
- `load_all_documents()`: 加载所有文档

**使用示例：**
```python
from app.rag.document_loader import DocumentLoader

loader = DocumentLoader()
documents = loader.load_all_documents()
```

### 2. PDFProcessor (`pdf_utils.py`)

**功能：** 处理 PDF 文件，提取文本内容

**主要方法：**
- `extract_text_from_pdf(pdf_path)`: 提取 PDF 文本
- `process_pdf(pdf_path)`: 处理 PDF 并返回文档块

**依赖：**
- `pymupdf` (fitz): `pip install pymupdf`

### 3. VectorStoreManager (`vector_store.py`)

**功能：** 管理文档的向量化和存储

**主要方法：**
- `initialize(documents)`: 初始化向量存储并添加文档
- `search(query, k)`: 搜索相关文档
- `asearch(query, k)`: 异步搜索相关文档

**配置：**
- Embedding 模型从配置文件读取（`model.rag.embedding_model`）
- 默认使用：`openai:text-embedding-3-small`
- 使用 DeepSeek API（如果配置了）

### 4. RAGRetriever (`rag_retriever.py`)

**功能：** 从知识库检索相关信息

**主要方法：**
- `retrieve(query)`: 检索相关文档
- `aretrieve(query)`: 异步检索相关文档
- `format_context(documents)`: 格式化检索结果

### 5. rag.py (主文件)

**功能：** FastAPI 应用，集成 RAG 功能

**关键特性：**
- 启动时自动初始化 RAG 系统
- 在生成响应前自动检索相关知识
- 将检索结果作为上下文传递给模型

## 🚀 使用方法

### 1. 准备文档

将文档放入 `app/rag/files/` 目录：

```bash
app/rag/files/
├── document1.txt
├── document2.txt
└── manual.pdf
```

### 2. 启动服务

```bash
python3 app/rag/rag.py
```

**启动时会自动：**
1. 扫描 `files/` 目录
2. 加载所有 txt 和 pdf 文件
3. 进行文本分割
4. 向量化并存储到向量数据库

### 3. 使用 API

**流式聊天接口：**
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "content_blocks": [{"type": "text", "content": "你的问题"}],
    "history": []
  }'
```

**同步聊天接口：**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content_blocks": [{"type": "text", "content": "你的问题"}],
    "history": []
  }'
```

## ⚙️ 配置说明

### Embedding 模型配置

在 `config/config.yaml` 中添加（可选）：

```yaml
model:
  rag:
    embedding_model: "openai:text-embedding-3-small"  # 可选，默认值
```

**支持的模型：**
- `openai:text-embedding-3-small`
- `openai:text-embedding-3-large`
- 其他 LangChain 支持的 embedding 模型

**注意：** 如果不配置，系统会使用 DeepSeek API（如果可用）或默认模型。

## 🔍 工作流程

### 用户提问 → Agent 回答

```
1. 用户发送问题
    ↓
2. RAG 检索器从知识库检索相关文档（top 4）
    ↓
3. 将检索结果格式化为上下文
    ↓
4. 将上下文添加到系统提示词
    ↓
5. 模型基于上下文生成回答
    ↓
6. 返回给用户
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

默认检索 top 4 个文档块，可以在调用时调整：
```python
retriever = get_rag_retriever(k=6)  # 检索 top 6
```

## 🐛 故障排查

### 问题 1: PDF 文件无法加载

**错误：** `ImportError: PyMuPDF (fitz) is required`

**解决：**
```bash
pip install pymupdf
```

### 问题 2: Embedding 模型初始化失败

**可能原因：**
- API Key 未配置
- 网络连接问题
- 模型名称错误

**解决：**
- 检查 `config/config.yaml` 中的 API 配置
- 确认网络可以访问 API 服务

### 问题 3: 检索结果为空

**可能原因：**
- 知识库未初始化
- 查询与文档不匹配

**检查：**
```python
from app.rag.vector_store import get_vector_store_manager

manager = get_vector_store_manager()
print(f"已初始化: {manager.is_initialized()}")
```

## 📝 注意事项

1. **内存使用：** 向量存储使用内存存储，重启后需要重新加载
2. **文档更新：** 修改文档后需要重启服务才能生效
3. **文件格式：** 目前支持 txt 和 pdf，其他格式需要扩展
4. **编码问题：** txt 文件应使用 UTF-8 编码

## 🔄 扩展功能

### 添加新的文档格式支持

在 `document_loader.py` 中添加：

```python
def load_docx_file(self, file_path: Path) -> List[Document]:
    # 实现 DOCX 文件加载
    pass
```

### 使用持久化向量存储

可以替换 `InMemoryVectorStore` 为：
- Chroma
- FAISS
- Pinecone
- 等持久化存储方案

## 📚 相关文档

- LangChain Vector Stores: https://docs.langchain.com/oss/python/integrations/vectorstores
- LangChain Embeddings: https://docs.langchain.com/oss/python/integrations/embeddings

