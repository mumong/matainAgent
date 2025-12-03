"""
RAG 检索器
用于从知识库中检索相关信息
"""
from typing import List, Optional
from langchain_core.documents import Document
from app.rag.vector_store import get_vector_store_manager


class RAGRetriever:
    """RAG 检索器"""
    
    def __init__(self, k: int = 4):
        """
        初始化 RAG 检索器
        
        Args:
            k: 检索的文档数量（默认 4）
        """
        self.k = k
        self.vector_store_manager = get_vector_store_manager()
    
    def retrieve(self, query: str) -> List[Document]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            
        Returns:
            相关文档列表
        """
        if not self.vector_store_manager.is_initialized():
            return []
        
        try:
            documents = self.vector_store_manager.search(query, k=self.k)
            return documents
        except Exception as e:
            print(f"⚠️  检索失败: {e}")
            return []
    
    async def aretrieve(self, query: str) -> List[Document]:
        """
        异步检索相关文档
        
        Args:
            query: 查询文本
            
        Returns:
            相关文档列表
        """
        if not self.vector_store_manager.is_initialized():
            return []
        
        try:
            documents = await self.vector_store_manager.asearch(query, k=self.k)
            return documents
        except Exception as e:
            print(f"⚠️  检索失败: {e}")
            return []
    
    def format_context(self, documents: List[Document]) -> str:
        """
        格式化检索到的文档为上下文文本
        
        Args:
            documents: 文档列表
            
        Returns:
            格式化后的上下文文本
        """
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('filename', doc.metadata.get('source', '未知来源'))
            context_parts.append(f"[文档 {i} - {source}]\n{doc.page_content}\n")
        
        return "\n---\n\n".join(context_parts)


# 全局 RAG 检索器实例
_rag_retriever: Optional[RAGRetriever] = None


def get_rag_retriever(k: int = 4) -> RAGRetriever:
    """
    获取 RAG 检索器（单例模式）
    
    Args:
        k: 检索的文档数量
        
    Returns:
        RAGRetriever 实例
    """
    global _rag_retriever
    
    if _rag_retriever is None or _rag_retriever.k != k:
        _rag_retriever = RAGRetriever(k=k)
    
    return _rag_retriever

