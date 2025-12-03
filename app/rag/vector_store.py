"""
向量存储管理器
用于管理文档的向量化和存储
"""
import os
import time
from typing import List, Optional, Tuple
from langchain.embeddings import init_embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from config.config_loader import get_config
from app.rag.zhipu_embeddings import ZhipuAIEmbeddings

# 设置环境变量，避免 tiktoken 网络下载问题
# 如果 TIKTOKEN_CACHE_DIR 已设置，tiktoken 会使用缓存
if "TIKTOKEN_CACHE_DIR" not in os.environ:
    # 设置缓存目录到项目目录下
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", ".tiktoken_cache")
    os.makedirs(cache_dir, exist_ok=True)
    os.environ["TIKTOKEN_CACHE_DIR"] = cache_dir


class VectorStoreManager:
    """向量存储管理器"""
    
    def __init__(self, embedding_model: Optional[str] = None):
        """
        初始化向量存储管理器
        
        Args:
            embedding_model: Embedding 模型名称（例如: "openai:text-embedding-3-small"）
                            如果为 None，将从配置文件读取
        """
        self.config = get_config()
        
        # 初始化 embedding 模型
        if embedding_model is None:
            # 尝试从配置读取，如果没有则使用默认值
            embedding_model = self.config.get(
                'model.rag.embedding_model',
                'openai:text-embedding-3-small'
            )
        
        # 保存配置，延迟初始化 embeddings（避免启动时网络问题）
        self.embedding_model = embedding_model
        
        # 判断是否为智谱AI模型
        self.is_zhipu_model = embedding_model in ['embedding-2', 'embedding-3']
        
        if self.is_zhipu_model:
            # 智谱AI配置
            self.embedding_api_key = self.config.get('model.glm.api')
            if not self.embedding_api_key:
                raise ValueError("使用智谱AI embedding 模型需要配置 model.glm.api")
        else:
            # 其他模型配置（如 DeepSeek）
            self.embedding_api_key = self.config.get('model.deepseek.api')
            self.embedding_api_base = self.config.get('model.deepseek.api_base', 'https://api.deepseek.com')
        
        self.embeddings: Optional[Embeddings] = None
        
        # 初始化向量存储
        self.vector_store: Optional[InMemoryVectorStore] = None
        self._is_initialized = False
    
    def _init_embeddings(self) -> Embeddings:
        """
        初始化 embedding 模型（带重试机制）
        
        Returns:
            Embeddings 实例
        """
        if self.embeddings is not None:
            return self.embeddings
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if self.is_zhipu_model:
                    # 使用智谱AI Embeddings
                    print(f"🔄 初始化智谱AI {self.embedding_model} 模型...")
                    # 使用极小的批量大小和更长的请求延迟，避免触发速率限制
                    # 如果账户等级较低（V0/V1），建议使用更保守的设置
                    self.embeddings = ZhipuAIEmbeddings(
                        api_key=self.embedding_api_key,
                        model=self.embedding_model,
                        batch_size=10,  # 每次只处理 1 条，最保守的设置
                        request_delay=1.0  # 增加请求延迟到 5 秒
                    )
                    print(f"✅ 智谱AI {self.embedding_model} 模型初始化成功")
                    print(f"   - 批量大小: 1 条/次（保守设置，避免速率限制）")
                    print(f"   - 请求延迟: 5.0 秒")
                    print(f"   ⚠️  如果仍有 429 错误，可能是账户配额或权限问题")
                else:
                    # 使用其他模型（如 DeepSeek）
                    self.embeddings = init_embeddings(
                        self.embedding_model,
                        api_key=self.embedding_api_key,
                        base_url=self.embedding_api_base
                    )
                    print(f"✅ Embedding 模型初始化成功 ({self.embedding_model})")
                
                return self.embeddings
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if retry_count < max_retries:
                    wait_time = retry_count * 3  # 递增等待时间：3s, 6s, 9s
                    print(f"⚠️  Embedding 模型初始化失败，{wait_time}秒后重试 ({retry_count}/{max_retries})...")
                    print(f"   错误: {error_msg[:150]}")
                    time.sleep(wait_time)
                else:
                    # 最后一次尝试（仅对非智谱AI模型）
                    if not self.is_zhipu_model:
                        try:
                            print("   尝试使用默认配置（不指定 base_url）...")
                            self.embeddings = init_embeddings(
                                self.embedding_model,
                                api_key=self.embedding_api_key
                            )
                            print("✅ Embedding 模型初始化成功（使用默认配置）")
                            return self.embeddings
                        except Exception as e2:
                            print(f"❌ Embedding 模型初始化最终失败: {e2}")
                            raise
                    else:
                        print(f"❌ 智谱AI Embedding 模型初始化最终失败: {error_msg}")
                        raise e
    
    def initialize(self, documents: List[Document], batch_size: int = 10) -> None:
        """
        初始化向量存储并添加文档（批量处理，带重试机制）
        
        Args:
            documents: 文档列表
            batch_size: 每批处理的文档数量（默认 10）
        """
        if not documents:
            print("⚠️  没有文档可加载")
            return
        
        print(f"\n🔄 开始向量化 {len(documents)} 个文档块（批量大小: {batch_size}）...")
        
        # 确保 embedding 已初始化
        embeddings = self._init_embeddings()
        
        # 创建向量存储
        self.vector_store = InMemoryVectorStore(embedding=embeddings)
        
        # 批量添加文档，带重试机制
        total_docs = len(documents)
        success_count = 0
        failed_count = 0
        
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_docs + batch_size - 1) // batch_size
            
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    # 添加批次文档
                    self.vector_store.add_documents(batch)
                    success_count += len(batch)
                    print(f"   ✅ 批次 {batch_num}/{total_batches}: 成功处理 {len(batch)} 个文档块")
                    break
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = retry_count * 2  # 递增等待时间：2s, 4s, 6s
                        print(f"   ⚠️  批次 {batch_num} 处理失败，{wait_time}秒后重试 ({retry_count}/{max_retries}): {str(e)[:100]}")
                        time.sleep(wait_time)
                    else:
                        failed_count += len(batch)
                        print(f"   ❌ 批次 {batch_num} 处理失败（已重试 {max_retries} 次）: {str(e)[:100]}")
                        # 继续处理下一批，不中断整个流程
            
            # 批次间延迟，避免请求过快（智谱AI模型需要更长的延迟）
            if i + batch_size < total_docs:
                delay = 0.5 if self.is_zhipu_model else 0.5
                time.sleep(delay)
        
        if success_count > 0:
            self._is_initialized = True
            print(f"\n✅ 向量存储初始化完成！")
            print(f"   - 成功: {success_count} 个文档块")
            if failed_count > 0:
                print(f"   - 失败: {failed_count} 个文档块")
            print()
        else:
            print(f"\n❌ 所有文档块处理失败，向量存储未初始化\n")
    
    def search(self, query: str, k: int = 4) -> List[Document]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            k: 返回的文档数量
            
        Returns:
            相关文档列表
        """
        if not self._is_initialized or self.vector_store is None:
            raise ValueError("向量存储未初始化，请先调用 initialize() 方法")
        
        return self.vector_store.similarity_search(query, k=k)
    
    async def asearch(self, query: str, k: int = 4) -> List[Document]:
        """
        异步搜索相关文档
        
        Args:
            query: 查询文本
            k: 返回的文档数量
            
        Returns:
            相关文档列表
        """
        if not self._is_initialized or self.vector_store is None:
            raise ValueError("向量存储未初始化，请先调用 initialize() 方法")
        
        return await self.vector_store.asimilarity_search(query, k=k)
    
    def search_with_score(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """
        搜索相关文档（带相似度分数）
        
        Args:
            query: 查询文本
            k: 返回的文档数量
            
        Returns:
            (文档, 相似度分数) 元组列表
        """
        if not self._is_initialized or self.vector_store is None:
            raise ValueError("向量存储未初始化，请先调用 initialize() 方法")
        
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def is_initialized(self) -> bool:
        """检查向量存储是否已初始化"""
        return self._is_initialized


# 全局向量存储管理器实例
_vector_store_manager: Optional[VectorStoreManager] = None


def get_vector_store_manager() -> VectorStoreManager:
    """
    获取向量存储管理器（单例模式）
    
    Returns:
        VectorStoreManager 实例
    """
    global _vector_store_manager
    
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager()
    
    return _vector_store_manager

