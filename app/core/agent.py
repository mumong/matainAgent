# 方案1：使用路径设置工具（如果未安装包）
# from app.utils.path_setup import setup_path

# 方案2：可编辑安装后，直接导入（推荐）
from langchain.agents import create_agent
from app.core import prompt
from config.config_loader import get_config
from langchain.chat_models import init_chat_model
from app.tools.base import tools_usage
from app.tools.mcp_tools import get_all_tools_sync
from app.core.prompt import SYSTEM_PROMPT
# from app.core.prompt import prompt_template

# 添加记忆管理 添加记忆message.
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
# mcp call 模块
import asyncio
from langgraph.checkpoint.memory import InMemorySaver

# RAG 集成
from app.core.rag_integration import initialize_rag_system, is_rag_initialized
from app.core.rag_middleware import RAGMiddleware



# 加载model相关配置
config = get_config()

model_usage = init_chat_model(
    model = config.get('model.deepseek.model'),
    model_provider = config.get('model.deepseek.model_provider'),
    api_key = config.get('model.deepseek.api'),
    base_url = config.get('model.deepseek.api_base'),
    max_tokens = config.get('model.deepseek.max_token'),
)

# 加载所有工具（本地工具 + Kubernetes MCP 工具）
# kubernetes_non_destructive: True 表示只允许只读和创建/更新操作，不允许删除操作
k8s_config = config.get('model.mcp.kubernetes', {})
all_tools = get_all_tools_sync(
    include_kubernetes=True,
    kubernetes_non_destructive=k8s_config.get('non_destructive', False),
    kubernetes_kubeconfig=k8s_config.get('kubeconfig'),  # 可选：指定 kubeconfig 路径
    kubernetes_context=k8s_config.get('context'),  # 可选：指定上下文
)

# 初始化 RAG 系统（可选，如果不需要 RAG 功能可以注释掉）
# 注意：RAG 初始化可能需要一些时间，特别是第一次运行时
try:
    initialize_rag_system(auto_init=True)  # auto_init=True 表示如果已初始化则跳过
except Exception as e:
    print(f"⚠️  RAG 系统初始化失败，将不使用知识库功能: {e}")

# 创建 RAG 中间件（如果 RAG 系统已初始化）
rag_middleware = None
if is_rag_initialized():
    rag_middleware = RAGMiddleware(rag_k=4, enable_auto_rag=True)
    print("✅ RAG 中间件已启用：将在输出运维建议时自动检索知识库\n")

# 创建agent智能体。
agent = create_agent(
    model=model_usage,
    tools=all_tools,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
    middleware=[rag_middleware] if rag_middleware else [],  # 添加 RAG 中间件
)

# 提问
question = """
如果什么pod有问题就查看他的日志看一下是什么原因导致的！
结合知识库里面的内容针对我遇到的问题，根据知识库里面的操作应该怎么做？

这是另外的一个问题：我需要你总结下这些知识库的主要内容是什么？
"""


async def run_agent():
    """异步运行 Agent（MCP 工具需要异步调用）
    使用 create_agent 本身的能力处理数据流，直接输出 token.content
    使用 RAG 中间件：Agent 先分析问题，在输出运维建议时自动检索知识库
    """
    # 直接使用用户问题，不需要预先检索 RAG
    # RAG 中间件会在 Agent 准备输出建议时自动触发
    messages = [{"role": "user", "content": question}]
    
    async for token, metadata in agent.astream(
        {'messages': messages},
        {
            "configurable": {
                "thread_id": "1"
            }
        },
        stream_mode="messages"
    ):
        # 直接使用 token.content，就像以往一样简单
        if hasattr(token, 'content') and token.content:
            print(f"{token.content}", end="", flush=True)


# 运行异步函数
if __name__ == "__main__":
    asyncio.run(run_agent())
