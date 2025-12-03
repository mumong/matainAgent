"""
使用配置文件的完整示例
展示如何在其他文件中使用 YAML 配置
"""
from config.config_loader import get_config


def example_1_basic_usage():
    """示例1: 基本使用方法"""
    # 获取配置加载器实例
    config = get_config()
    
    # 方法1: 使用 get() 方法获取配置值
    deepseek_api = config.get('model.deepseek.api')
    print(f"DeepSeek API Key: {deepseek_api}")
    
    # 方法2: 获取模型配置
    deepseek_config = config.get_model_config('deepseek')
    print(f"DeepSeek 完整配置: {deepseek_config}")
    
    # 方法3: 直接访问配置字典
    full_config = config.config
    print(f"完整配置: {full_config}")


def example_2_use_in_function():
    """示例2: 在函数中使用配置"""
    config = get_config()
    
    def call_deepseek_api():
        """调用 DeepSeek API 的示例函数"""
        api_key = config.get('model.deepseek.api')
        api_base = config.get('model.deepseek.api_base')
        model_name = config.get('model.deepseek.model')
        max_token = config.get('model.deepseek.max_token')
        
        print(f"使用 API Key: {api_key}")
        print(f"API Base: {api_base}")
        print(f"Model: {model_name}")
        print(f"Max Token: {max_token}")
        
        # 这里可以继续使用这些配置值进行 API 调用
        # import requests
        # response = requests.post(
        #     f"{api_base}/v1/chat/completions",
        #     headers={"Authorization": f"Bearer {api_key}"},
        #     json={"model": model_name, "max_tokens": max_token, ...}
        # )
    
    call_deepseek_api()


def example_3_use_in_class():
    """示例3: 在类中使用配置"""
    config = get_config()
    
    class APIClient:
        """API 客户端类"""
        
        def __init__(self, model_name='deepseek'):
            self.config = get_config()
            self.model_name = model_name
            self.model_config = self.config.get_model_config(model_name)
            
            if self.model_config:
                self.api_key = self.model_config.get('api')
                self.api_base = self.model_config.get('api_base')
                self.model = self.model_config.get('model')
                self.max_token = self.model_config.get('max_token')
            else:
                raise ValueError(f"模型配置不存在: {model_name}")
        
        def get_api_key(self):
            """获取 API Key"""
            return self.api_key
        
        def get_api_base(self):
            """获取 API Base URL"""
            return self.api_base
        
        def make_request(self):
            """发起 API 请求（示例）"""
            print(f"准备向 {self.api_base} 发起请求")
            print(f"使用模型: {self.model}")
            print(f"API Key: {self.api_key[:10]}...")  # 只显示前10个字符
            # 实际的 API 调用代码...
    
    # 使用示例
    client = APIClient('deepseek')
    client.make_request()
    
    # 使用另一个模型
    try:
        glm_client = APIClient('glm')
        print(f"GLM API Key: {glm_client.get_api_key()}")
    except ValueError as e:
        print(f"错误: {e}")


def example_4_with_default_value():
    """示例4: 使用默认值"""
    config = get_config()
    
    # 如果配置不存在，返回默认值
    timeout = config.get('model.deepseek.timeout', 30)  # 默认30秒
    print(f"超时时间: {timeout}")
    
    # 检查配置是否存在
    if config.get('model.deepseek.api'):
        print("DeepSeek API Key 已配置")
    else:
        print("DeepSeek API Key 未配置")


if __name__ == "__main__":
    print("=" * 50)
    print("示例1: 基本使用方法")
    print("=" * 50)
    example_1_basic_usage()
    
    print("\n" + "=" * 50)
    print("示例2: 在函数中使用配置")
    print("=" * 50)
    example_2_use_in_function()
    
    print("\n" + "=" * 50)
    print("示例3: 在类中使用配置")
    print("=" * 50)
    example_3_use_in_class()
    
    print("\n" + "=" * 50)
    print("示例4: 使用默认值")
    print("=" * 50)
    example_4_with_default_value()

