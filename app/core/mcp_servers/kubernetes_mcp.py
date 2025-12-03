"""
Kubernetes MCP 集成模块
用于将 Kubernetes MCP 服务器的工具集成到 Agent 中
"""
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from config.config_loader import get_config


class KubernetesMCPManager:
    """Kubernetes MCP 管理器"""
    
    def __init__(self, non_destructive: bool = False, kubeconfig: str = None, context: str = None):
        """
        初始化 Kubernetes MCP 管理器
        
        Args:
            non_destructive: 是否启用非破坏性模式（只读和创建/更新操作）
            kubeconfig: kubeconfig 文件路径（可选，默认使用 ~/.kube/config）
            context: Kubernetes 上下文名称（可选，默认使用当前上下文）
        """
        self.config = get_config()
        self.non_destructive = non_destructive
        self.kubeconfig = kubeconfig
        self.context = context
        self.client = None
        self._tools = None
    
    def _create_client(self, kubeconfig: str = None, context: str = None) -> MultiServerMCPClient:
        """
        创建 MCP 客户端
        
        Args:
            kubeconfig: kubeconfig 文件路径（可选，默认使用 ~/.kube/config）
            context: Kubernetes 上下文名称（可选，默认使用当前上下文）
        """
        env = {}
        
        # 如果启用非破坏性模式
        if self.non_destructive:
            env["ALLOW_ONLY_NON_DESTRUCTIVE_TOOLS"] = "true"
        
        # 指定 kubeconfig 路径
        if kubeconfig:
            env["KUBECONFIG"] = kubeconfig
        
        # 指定上下文（如果 kubeconfig 中有多个上下文）
        if context:
            env["KUBECTL_CONTEXT"] = context
        
        return MultiServerMCPClient(
            {
                "kubernetes": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "mcp-server-kubernetes"
                    ],
                    "env": env,
                    "transport": "stdio"
                }
            }
        )
    
    async def get_tools(self):
        """
        获取 Kubernetes MCP 工具列表
        
        Returns:
            List[Tool]: Kubernetes MCP 工具列表
        """
        if self._tools is None:
            if self.client is None:
                self.client = self._create_client(
                    kubeconfig=self.kubeconfig,
                    context=self.context
                )
            
            self._tools = await self.client.get_tools()
            cluster_info = ""
            if self.kubeconfig:
                cluster_info = f" (kubeconfig: {self.kubeconfig})"
            if self.context:
                cluster_info += f" (context: {self.context})"
            print(f"✅ 成功加载 {len(self._tools)} 个 Kubernetes MCP 工具{cluster_info}")
            print(f"📋 工具列表: {[t.name for t in self._tools[:10]]}...")  # 只显示前10个
        
        return self._tools
    
    async def close(self):
        """关闭 MCP 客户端连接"""
        if self.client:
            # 如果客户端有关闭方法，在这里调用
            pass


# 全局实例（可选，用于单例模式）
_kubernetes_mcp_manager: KubernetesMCPManager | None = None


async def get_kubernetes_mcp_tools(
    non_destructive: bool = False,
    kubeconfig: str = None,
    context: str = None
):
    """
    获取 Kubernetes MCP 工具（便捷函数）
    
    Args:
        non_destructive: 是否启用非破坏性模式
        kubeconfig: kubeconfig 文件路径（可选）
        context: Kubernetes 上下文名称（可选）
    
    Returns:
        List[Tool]: Kubernetes MCP 工具列表
    """
    global _kubernetes_mcp_manager
    
    # 如果配置改变，重新创建管理器
    if (_kubernetes_mcp_manager is None or 
        _kubernetes_mcp_manager.non_destructive != non_destructive or
        _kubernetes_mcp_manager.kubeconfig != kubeconfig or
        _kubernetes_mcp_manager.context != context):
        _kubernetes_mcp_manager = KubernetesMCPManager(
            non_destructive=non_destructive,
            kubeconfig=kubeconfig,
            context=context
        )
    
    return await _kubernetes_mcp_manager.get_tools()

