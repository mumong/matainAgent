# from config.config_loader import get_config


# def main():
#     """
#     主程序入口
#     """
#     # 获取配置
#     config = get_config()
    
#     # 使用配置值
#     deepseek_api = config.get('model.deepseek.api')
#     print(f"DeepSeek API Key: {deepseek_api}")
    
#     # 获取模型配置
#     deepseek_config = config.get_model_config('deepseek')
#     if deepseek_config:
#         print(f"DeepSeek 模型: {deepseek_config.get('model')}")
#         print(f"API Base: {deepseek_config.get('api_base')}")
#         print(f"Max Token: {deepseek_config.get('max_token')}")


# if __name__ == "__main__":
#     main()