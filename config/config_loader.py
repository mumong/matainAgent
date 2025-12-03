"""
配置加载模块
用于加载和访问 YAML 配置文件中的值
"""
import yaml
import os
from pathlib import Path


class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, config_path=None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，如果为 None，则使用默认路径
        """
        if config_path is None:
            # 获取当前文件的目录
            current_dir = Path(__file__).parent
            config_path = current_dir / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """加载 YAML 配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件解析错误: {e}")
    
    def get(self, key_path, default=None):
        """
        根据键路径获取配置值
        
        Args:
            key_path: 配置键路径，使用点号分隔，如 'model.deepseek.api'
            default: 如果键不存在时返回的默认值
        
        Returns:
            配置值，如果不存在则返回默认值
        
        Example:
            config.get('model.deepseek.api')
            config.get('model.glm.api', 'default_value')
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_model_config(self, model_name):
        """
        获取指定模型的完整配置
        
        Args:
            model_name: 模型名称，如 'deepseek' 或 'glm'
        
        Returns:
            模型配置字典，如果不存在则返回 None
        """
        return self._config.get('model', {}).get(model_name)
    
    @property
    def config(self):
        """获取完整的配置字典"""
        return self._config


# 创建全局配置实例，方便直接导入使用
_config_loader = None

def get_config(config_path=None):
    """
    获取配置加载器实例（单例模式）
    
    Args:
        config_path: 配置文件路径，仅在第一次调用时生效
    
    Returns:
        ConfigLoader 实例
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_path)
    return _config_loader

