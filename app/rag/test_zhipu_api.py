"""
测试智谱AI API Key 和 embedding 功能
用于诊断 API 连接问题
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.rag.zhipu_embeddings import ZhipuAIEmbeddings
from config.config_loader import get_config

def test_zhipu_api():
    """测试智谱AI API"""
    config = get_config()
    api_key = config.get('model.glm.api')
    
    if not api_key:
        print("❌ 未找到 API Key，请检查 config.yaml 中的 model.glm.api 配置")
        return
    
    print(f"🔍 测试智谱AI API Key: {api_key[:10]}...{api_key[-5:]}")
    print("=" * 60)
    
    try:
        # 创建 embeddings 实例
        embeddings = ZhipuAIEmbeddings(
            api_key=api_key,
            model="embedding-3",
            batch_size=1,
            request_delay=3.0
        )
        
        # 测试单个文本
        print("\n📝 测试 1: 单个文本 embedding...")
        test_text = "这是一个测试文本"
        result = embeddings.embed_query(test_text)
        print(f"✅ 成功！向量维度: {len(result)}")
        
        # 测试多个文本
        print("\n📝 测试 2: 多个文本 embedding（2条）...")
        test_texts = [
            "第一条测试文本",
            "第二条测试文本"
        ]
        results = embeddings.embed_documents(test_texts)
        print(f"✅ 成功！处理了 {len(results)} 条文本")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！API Key 有效，可以正常使用")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print("\n可能的原因：")
        print("1. API Key 无效或已过期")
        print("2. 账户配额已用完")
        print("3. 账户等级太低，并发限制太严格")
        print("4. 网络连接问题")
        print("\n建议：")
        print("1. 检查智谱AI控制台的 API Key 状态")
        print("2. 检查账户余额和配额")
        print("3. 查看账户等级（V0/V1/V2/V3）")
        print("4. 尝试在智谱AI控制台手动测试 API")

if __name__ == "__main__":
    test_zhipu_api()

