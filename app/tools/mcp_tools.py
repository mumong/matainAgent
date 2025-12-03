"""
MCP 工具集成模块
用于将各种 MCP 服务器的工具集成到 Agent 中
"""
import asyncio
from typing import List
from langchain_core.tools import BaseTool
from app.tools.base import tools_usage
from app.core.mcp_servers.kubernetes_mcp import get_kubernetes_mcp_tools


async def get_all_tools(
    include_kubernetes: bool = True,
    kubernetes_non_destructive: bool = False,
    kubernetes_kubeconfig: str = None,
    kubernetes_context: str = None,
) -> List[BaseTool]:
    """
    获取所有工具（本地工具 + MCP 工具）
    
    Args:
        include_kubernetes: 是否包含 Kubernetes MCP 工具
        kubernetes_non_destructive: Kubernetes 是否使用非破坏性模式
        kubernetes_kubeconfig: Kubernetes kubeconfig 文件路径（可选）
        kubernetes_context: Kubernetes 上下文名称（可选）
    
    Returns:
        List[BaseTool]: 所有工具的列表
    """
    all_tools = list(tools_usage)  # 本地工具
    
    # 添加 Kubernetes MCP 工具
    if include_kubernetes:
        try:
            k8s_tools = await get_kubernetes_mcp_tools(
                non_destructive=kubernetes_non_destructive,
                kubeconfig=kubernetes_kubeconfig,
                context=kubernetes_context
            )
            all_tools.extend(k8s_tools)
            print(f"✅ 总共加载了 {len(all_tools)} 个工具（{len(tools_usage)} 个本地 + {len(k8s_tools)} 个 Kubernetes MCP）")
        except Exception as e:
            print(f"⚠️  加载 Kubernetes MCP 工具失败: {e}")
            print("   请确保：")
            print("   1. 已安装 Node.js 和 npx")
            print("   2. 已配置 kubectl 和 kubeconfig")
            print("   3. 网络可以访问 npm registry")
    
    return all_tools


def get_all_tools_sync(
    include_kubernetes: bool = True,
    kubernetes_non_destructive: bool = False,
    kubernetes_kubeconfig: str = None,
    kubernetes_context: str = None,
) -> List[BaseTool]:
    """
    同步版本：获取所有工具（本地工具 + MCP 工具）
    
    Args:
        include_kubernetes: 是否包含 Kubernetes MCP 工具
        kubernetes_non_destructive: Kubernetes 是否使用非破坏性模式
        kubernetes_kubeconfig: Kubernetes kubeconfig 文件路径（可选）
        kubernetes_context: Kubernetes 上下文名称（可选）
    
    Returns:
        List[BaseTool]: 所有工具的列表
    """
    return asyncio.run(get_all_tools(
        include_kubernetes,
        kubernetes_non_destructive,
        kubernetes_kubeconfig,
        kubernetes_context
    ))

