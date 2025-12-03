from langchain.tools import tool


@tool
def test_output(city: str) -> str:
    """
    这是一个测试输出工具
    参数:
    - city: 城市名称
    返回:
    - 这是一个测试输出工具: 城市名称
    """
    return f"这是一个测试输出工具123: {city}\n"



tools_usage = [test_output]