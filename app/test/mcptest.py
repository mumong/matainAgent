import asyncio

from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from config.config_loader import get_config


from langchain.agents.structured_output import AutoStrategy

from pydantic import BaseModel


class Result(BaseModel):
    loc1: str   
    loc2: str
    distance: float


# 加载model相关配置
config = get_config()

model_usage = init_chat_model(
    model = config.get('model.deepseek.model'),
    model_provider = config.get('model.deepseek.model_provider'),
    api_key = config.get('model.deepseek.api'),
    base_url = config.get('model.deepseek.api_base'),
    max_tokens = config.get('model.deepseek.max_token'),
)

mcp_client = MultiServerMCPClient(
    {
        "amap-maps": {
              "command": "npx",  # Linux 上直接使用 npx，不需要 cmd
              "args": [
                "-y",
                "@amap/amap-maps-mcp-server"
              ],
              "env": {
                "AMAP_MAPS_API_KEY": config.get('model.mcp.amap-maps.api_key')
              },
              'transport': 'stdio'
            }
    }
)

async def get_server_tools():
    mcp_tools = await mcp_client.get_tools()
    print(f"加载了{len(mcp_tools)}: {[t.name for t in mcp_tools]}")
    agent_with_mcp = create_agent(
        model_usage,
        tools=mcp_tools,
        system_prompt = "你是一个高德地图规划助手，能帮我规划形成和获得地图基本信息",
        response_format = AutoStrategy(Result),
    )
    result = await agent_with_mcp.ainvoke(
        {
            "messages":{
                "role": 'user',
                "content": "请告诉我北京圆明园到北京西北旺地铁站距离"
            }
        }
    )
    for msg in result['messages']:
        msg.pretty_print()


asyncio.run(get_server_tools())

