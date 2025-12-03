"""
路径设置工具模块
用于统一处理项目路径，解决模块导入问题

使用方法：
    from app.utils.path_setup import setup_path
    setup_path()
"""
import sys
from pathlib import Path


def setup_path():
    """
    将项目根目录添加到 Python 路径中
    
    这个函数应该在文件开头调用，用于确保可以正确导入项目模块
    即使从任何位置运行脚本也能正常工作
    """
    # 获取当前文件的目录
    current_file = Path(__file__).resolve()
    # 计算项目根目录（向上查找3级：utils -> app -> 项目根）
    project_root = current_file.parent.parent.parent
    
    # 如果项目根目录不在路径中，则添加
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root


# 自动执行路径设置（当模块被导入时）
setup_path()

