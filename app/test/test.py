import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from langchain.agents import create_agent
from config.model_factory import create_model_from_config


def get_weather(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}总是阳光明媚！"


# 从配置文件创建模型
model = create_model_from_config('deepseek')

# 创建 agent
agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="你是一个乐于助人的助手",
)

# 运行代理
if __name__ == "__main__":
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "旧金山的天气怎么样"}]}
    )
    print(result)