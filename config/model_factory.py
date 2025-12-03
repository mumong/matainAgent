"""
模型工厂模块
用于根据配置文件创建 langchain 模型实例
"""
from langchain.chat_models import init_chat_model
from config.config_loader import get_config


def create_model_from_config(model_name: str = 'deepseek'):
    """
    根据配置文件创建模型实例
    
    Args:
        model_name: 模型名称，对应 config.yaml 中的 model 键，如 'deepseek' 或 'glm'
    
    Returns:
        BaseChatModel 实例
    
    Example:
        from config.model_factory import create_model_from_config
        
        # 创建 deepseek 模型
        model = create_model_from_config('deepseek')
        
        # 在 create_agent 中使用
        from langchain.agents import create_agent
        agent = create_agent(model=model, tools=[...])
    """
    config = get_config()
    model_config = config.get_model_config(model_name)
    
    if not model_config:
        raise ValueError(f"模型配置不存在: {model_name}")
    
    # 根据模型名称确定模型标识符
    if model_name == 'deepseek':
        model_id = model_config.get('model', 'deepseek-chat')
        return init_chat_model(
            model_id,
            api_key=model_config.get('api'),
            base_url=model_config.get('api_base'),
            max_tokens=model_config.get('max_token'),
        )
    elif model_name == 'glm':
        # GLM 模型的处理（如果需要的话）
        # 这里可以根据实际情况调整
        raise NotImplementedError(f"模型 {model_name} 暂未实现")
    else:
        raise ValueError(f"不支持的模型: {model_name}")

