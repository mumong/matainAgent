"""
RAG 集成模块
用于在 Agent 中集成 RAG 知识库功能
"""
import os
from typing import Optional, List
from langchain_core.documents import Document
from app.rag.document_loader import DocumentLoader
from app.rag.vector_store import get_vector_store_manager
from app.rag.rag_retriever import get_rag_retriever


# 全局变量，标记 RAG 是否已初始化
_rag_initialized: bool = False


def initialize_rag_system(files_dir: str = "app/rag/files", auto_init: bool = True) -> bool:
    """
    初始化 RAG 系统
    
    Args:
        files_dir: 文档目录路径
        auto_init: 是否自动初始化（如果文档已加载过，可以跳过）
    
    Returns:
        True 如果初始化成功，False 否则
    """
    global _rag_initialized
    
    if _rag_initialized and auto_init:
        return True
    
    try:
        print("\n" + "="*60)
        print("🚀 初始化 RAG 知识库...")
        print("="*60 + "\n")
        
        # 1. 加载文档
        loader = DocumentLoader(files_dir=files_dir)
        documents = loader.load_all_documents()
        
        if not documents:
            print("⚠️  未找到任何文档，RAG 功能将不可用")
            _rag_initialized = False
            return False
        
        # 2. 初始化向量存储
        vector_store_manager = get_vector_store_manager()
        vector_store_manager.initialize(documents)
        
        if vector_store_manager.is_initialized():
            _rag_initialized = True
            print("="*60)
            print("✅ RAG 知识库初始化完成！")
            print("="*60 + "\n")
            return True
        else:
            _rag_initialized = False
            return False
            
    except Exception as e:
        print(f"❌ RAG 系统初始化失败: {e}")
        import traceback
        traceback.print_exc()
        _rag_initialized = False
        return False


def get_rag_context(query: str, k: int = 4) -> str:
    """
    从 RAG 知识库检索相关上下文
    
    Args:
        query: 用户查询
        k: 检索的文档数量
    
    Returns:
        格式化的上下文文本，如果没有相关文档则返回空字符串
    """
    if not _rag_initialized:
        return ""
    
    try:
        retriever = get_rag_retriever(k=k)
        documents = retriever.retrieve(query)
        
        if not documents:
            return ""
        
        # 格式化上下文
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', '未知来源')
            # 提取文件名
            if isinstance(source, str):
                filename = os.path.basename(source)
            else:
                filename = str(source)
            
            context_parts.append(f"[参考文档 {i}: {filename}]\n{doc.page_content}")
        
        context = "\n\n---\n\n".join(context_parts)
        return f"\n\n【知识库参考信息】\n{context}\n【知识库参考信息结束】\n"
        
    except Exception as e:
        print(f"⚠️  RAG 检索失败: {e}")
        return ""


async def get_rag_context_async(query: str, k: int = 4) -> str:
    """
    异步从 RAG 知识库检索相关上下文
    
    Args:
        query: 用户查询
        k: 检索的文档数量
    
    Returns:
        格式化的上下文文本，如果没有相关文档则返回空字符串
    """
    if not _rag_initialized:
        return ""
    
    try:
        retriever = get_rag_retriever(k=k)
        documents = await retriever.aretrieve(query)
        
        if not documents:
            return ""
        
        # 格式化上下文
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', '未知来源')
            filename = os.path.basename(source) if isinstance(source, str) else str(source)
            context_parts.append(f"[参考文档 {i}: {filename}]\n{doc.page_content}")
        
        context = "\n\n---\n\n".join(context_parts)
        return f"\n\n【知识库参考信息】\n{context}\n【知识库参考信息结束】\n"
        
    except Exception as e:
        print(f"⚠️  RAG 检索失败: {e}")
        return ""


def is_rag_initialized() -> bool:
    """检查 RAG 系统是否已初始化"""
    return _rag_initialized

