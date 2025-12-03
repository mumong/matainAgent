"""
Kubernetes MCP 集成测试
"""
import asyncio
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from config.config_loader import get_config
from app.tools.mcp_tools import get_all_tools
from langgraph.checkpoint.memory import InMemorySaver


async def test_kubernetes_mcp():
    """测试 Kubernetes MCP 集成"""
    config = get_config()
    
    # 初始化模型
    model = init_chat_model(
        model=config.get('model.deepseek.model'),
        model_provider=config.get('model.deepseek.model_provider'),
        api_key=config.get('model.deepseek.api'),
        base_url=config.get('model.deepseek.api_base'),
        max_tokens=config.get('model.deepseek.max_token'),
    )
    
    # 获取所有工具（包括 Kubernetes MCP 工具）
    print("🔄 正在加载工具...")
    all_tools = await get_all_tools(
        include_kubernetes=True,
        kubernetes_non_destructive=config.get('model.mcp.kubernetes.non_destructive', False)
    )
    
    print(f"\n✅ 成功加载 {len(all_tools)} 个工具")
    
    # 显示 Kubernetes 相关工具
    k8s_tools = [t for t in all_tools if 'kubectl' in t.name.lower() or 'helm' in t.name.lower() or 'kubernetes' in t.name.lower() or 'k8s' in t.name.lower()]
    print(f"\n📋 Kubernetes 相关工具 ({len(k8s_tools)} 个):")
    for tool in k8s_tools[:20]:  # 只显示前20个
        print(f"  - {tool.name}")
    if len(k8s_tools) > 20:
        print(f"  ... 还有 {len(k8s_tools) - 20} 个工具")
    
    # 创建 Agent
    agent = create_agent(
        model=model,
        tools=all_tools,
        system_prompt="你是一个 Kubernetes 集群管理助手，可以帮助用户管理和诊断 Kubernetes 集群。",
        checkpointer=InMemorySaver(),
    )
    
    # 测试查询
    print("\n🤖 测试 Agent...")
    print("=" * 60)
    
    # 测试1：查看集群信息
    print("\n测试1: 查看集群节点信息")
    result = await agent.ainvoke(
        {
            "messages": [{"role": "user", "content": "请查看 Kubernetes 集群的节点信息"}]
        },
        {
            "configurable": {"thread_id": "k8s-test-1"}
        }
    )
    
    # 打印最后一条消息
    if result.get('messages'):
        last_msg = result['messages'][-1]
        if hasattr(last_msg, 'content'):
            print(f"回复: {last_msg.content}")
        else:
            print(f"回复: {last_msg}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_kubernetes_mcp())

