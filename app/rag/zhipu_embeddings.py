"""
智谱AI Embeddings 实现
用于调用智谱AI的 embedding-2 或 embedding-3 模型
"""
import requests
import time
from typing import List, Optional
from langchain_core.embeddings import Embeddings
from config.config_loader import get_config


class ZhipuAIEmbeddings(Embeddings):
    """智谱AI Embeddings 类"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "embedding-2",
        api_base: str = "https://open.bigmodel.cn/api/paas/v4/embeddings",
        dimensions: Optional[int] = None,
        batch_size: int = 10,
        request_delay: float = 1.0,
    ):
        """
        初始化智谱AI Embeddings
        
        Args:
            api_key: 智谱AI API Key，如果为 None 则从配置文件读取
            model: 模型名称，支持 "embedding-2" 或 "embedding-3"
            api_base: API 基础URL
            dimensions: 向量维度（仅 embedding-3 支持，可选：256, 512, 1024, 2048）
            batch_size: 每批处理的文本数量（默认 10，避免触发速率限制）
            request_delay: 请求之间的延迟时间（秒，默认 1.0）
        """
        self.config = get_config()
        self.api_key = api_key if api_key else self.config.get('model.glm.api')
        if not self.api_key:
            raise ValueError("智谱AI API Key 未配置，请在 config.yaml 中设置 model.glm.api")
        
        self.model = model
        self.api_base = api_base
        self.dimensions = dimensions
        self.batch_size = min(batch_size, 64)  # 最大不超过 64（API 限制）
        self.request_delay = request_delay
        
        # 测试 API Key 有效性（可选，延迟到第一次调用时测试）
        self._api_key_tested = False
        
    def _test_api_key(self) -> bool:
        """
        测试 API Key 是否有效（发送一个最小请求）
        
        Returns:
            True 如果 API Key 有效，False 否则
        """
        if self._api_key_tested:
            return True
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": "test"
        }
        
        try:
            response = requests.post(
                self.api_base,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                self._api_key_tested = True
                return True
            elif response.status_code == 401:
                error_msg = "API Key 无效或未授权"
                try:
                    error_detail = response.json()
                    error_msg = error_detail.get('error', {}).get('message', error_msg)
                except:
                    pass
                raise ValueError(f"❌ {error_msg}，请检查 config.yaml 中的 model.glm.api 配置")
            elif response.status_code == 429:
                # 429 错误可能是速率限制，但不一定是 API Key 问题
                print("⚠️  测试 API Key 时遇到速率限制，但 API Key 可能是有效的")
                self._api_key_tested = True  # 假设有效，继续尝试
                return True
            else:
                error_msg = f"未知错误: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg = error_detail.get('error', {}).get('message', error_msg)
                except:
                    error_msg = response.text[:200]
                print(f"⚠️  API Key 测试返回 {response.status_code}: {error_msg}")
                self._api_key_tested = True  # 继续尝试
                return True
                
        except Exception as e:
            print(f"⚠️  测试 API Key 时出错: {e}")
            self._api_key_tested = True  # 继续尝试
            return True
    
    def _embed(self, texts: List[str]) -> List[List[float]]:
        """
        调用智谱AI API 生成 embeddings（带速率限制处理和重试机制）
        
        Args:
            texts: 文本列表
            
        Returns:
            embeddings 列表
        """
        # 首次调用时测试 API Key
        if not self._api_key_tested:
            print("🔍 测试 API Key 有效性...")
            self._test_api_key()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        all_embeddings = []
        max_retries = 5  # 最大重试次数
        
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
            
            # 构建请求体
            payload = {
                "model": self.model,
                "input": batch_texts if len(batch_texts) > 1 else batch_texts[0]
            }
            
            # embedding-3 支持自定义维度
            if self.model == "embedding-3" and self.dimensions:
                payload["dimensions"] = self.dimensions
            
            # 重试机制（处理 429 错误）
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    response = requests.post(
                        self.api_base,
                        headers=headers,
                        json=payload,
                        timeout=60  # 增加超时时间
                    )
                    
                    # 处理 429 速率限制错误
                    if response.status_code == 429:
                        try:
                            error_detail = response.json()
                            error_msg = error_detail.get('error', {}).get('message', '未知错误')
                        except:
                            error_msg = response.text[:200]
                        
                        retry_after = int(response.headers.get('Retry-After', 10))
                        wait_time = retry_after * (2 ** retry_count)  # 指数退避
                        wait_time = min(wait_time, 120)  # 最多等待 120 秒
                        
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"   ⚠️  批次 {batch_num}/{total_batches} 遇到速率限制 (429)")
                            print(f"      错误详情: {error_msg[:100]}")
                            print(f"      等待 {wait_time} 秒后重试 ({retry_count}/{max_retries})...")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"批次 {batch_num} 达到最大重试次数，速率限制仍未解除。错误: {error_msg}")
                    
                    # 处理其他 HTTP 错误
                    if response.status_code != 200:
                        try:
                            error_detail = response.json()
                            error_msg = error_detail.get('error', {}).get('message', response.text[:200])
                        except:
                            error_msg = response.text[:200]
                        raise Exception(f"API 返回错误 {response.status_code}: {error_msg}")
                    
                    # 处理其他 HTTP 错误
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    # 解析响应
                    if "data" in result:
                        batch_embeddings = [item["embedding"] for item in result["data"]]
                        all_embeddings.extend(batch_embeddings)
                        success = True
                    else:
                        raise ValueError(f"API 响应格式错误: {result}")
                        
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 5 * retry_count
                        print(f"   ⚠️  批次 {batch_num} 请求超时，{wait_time} 秒后重试 ({retry_count}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        raise Exception(f"批次 {batch_num} 请求超时，已达到最大重试次数")
                        
                except requests.exceptions.RequestException as e:
                    # 非 429 错误，直接抛出
                    raise Exception(f"调用智谱AI Embedding API 失败: {str(e)}")
            
            # 批次之间延迟，避免触发速率限制
            if i + self.batch_size < len(texts):
                time.sleep(self.request_delay)
        
        return all_embeddings
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        为文档列表生成 embeddings
        
        Args:
            texts: 文档文本列表
            
        Returns:
            embeddings 列表
        """
        if not texts:
            return []
        return self._embed(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        为查询文本生成 embedding
        
        Args:
            text: 查询文本
            
        Returns:
            embedding 向量
        """
        embeddings = self._embed([text])
        return embeddings[0] if embeddings else []

