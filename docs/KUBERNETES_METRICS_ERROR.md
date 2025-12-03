# Kubernetes Metrics API 错误处理

## 问题描述

运行 Agent 时出现错误：

```
error: Metrics API not available
mcp.shared.exceptions.McpError: MCP error -32603: Failed to execute kubectl command
```

## 问题原因

**这不是代码问题，而是 Kubernetes 集群配置问题。**

`kubectl top` 命令需要 **Metrics Server** 在集群中运行。如果集群没有安装 Metrics Server，这个命令会失败。

### 为什么需要 Metrics Server？

- `kubectl top nodes` - 查看节点资源使用情况
- `kubectl top pods` - 查看 Pod 资源使用情况
- Kubernetes Dashboard 的资源监控
- HPA (Horizontal Pod Autoscaler) 自动扩缩容

## 解决方案

### 方案1：安装 Metrics Server（推荐，解决根本问题）

#### 步骤1：检查是否已安装

```bash
# 检查 Metrics Server 是否运行
kubectl get deployment metrics-server -n kube-system

# 如果返回 "NotFound"，说明未安装
```

#### 步骤2：安装 Metrics Server

**标准 Kubernetes 集群：**

```bash
# 下载 Metrics Server 清单
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

**如果使用 kubeadm 或其他方式安装的集群，可能需要修改配置：**

```bash
# 1. 下载清单文件
wget https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 2. 编辑文件，在 args 中添加以下参数（如果需要）
# --kubelet-insecure-tls  # 如果使用自签名证书
# --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname

# 3. 应用配置
kubectl apply -f components.yaml
```

#### 步骤3：验证安装

```bash
# 等待 Metrics Server 就绪
kubectl wait --for=condition=available --timeout=300s deployment/metrics-server -n kube-system

# 测试命令
kubectl top nodes
kubectl top pods --all-namespaces
```

### 方案2：配置 Agent 优雅处理错误（临时方案）

如果暂时无法安装 Metrics Server，可以配置 Agent 优雅地处理工具错误，让 Agent 继续运行并使用其他工具。

**修改 `app/core/agent.py`：**

```python
from langchain.tools import ToolNode

# 创建工具节点，配置错误处理
tool_node = ToolNode(
    all_tools,
    handle_tool_errors=True  # 捕获所有工具错误，返回错误消息而不是抛出异常
)

# 注意：create_agent 内部会创建 ToolNode，我们需要通过其他方式配置
# 或者使用自定义的 ToolNode
```

**但是，`create_agent` 不直接支持传递 `handle_tool_errors` 参数。**

**更好的方案：在 System Prompt 中提示 Agent 处理错误：**

```python
SYSTEM_PROMPT = """
你是一个 Kubernetes 集群管理助手。

重要提示：
- 如果某个工具调用失败（如 Metrics API 不可用），请继续使用其他工具
- 不要因为单个工具失败而停止诊断
- 可以尝试使用替代方法获取信息（例如：使用 kubectl describe 代替 kubectl top）
"""
```

### 方案3：使用 try-except 包装（代码层面）

在运行 Agent 时捕获异常：

```python
async def run_agent():
    """异步运行 Agent（MCP 工具需要异步调用）"""
    try:
        async for token in agent.astream(...):
            # 处理输出
            pass
    except Exception as e:
        # 捕获错误，但不中断
        print(f"\n⚠️  工具调用出错: {e}")
        print("   这可能是集群配置问题，不是代码问题")
        # 可以选择继续或退出
```

## 当前错误分析

从你的错误信息看：

1. ✅ **Agent 正常工作** - 能够调用工具
2. ✅ **工具调用成功** - `kubectl get events` 成功执行
3. ❌ **特定工具失败** - `kubectl top nodes` 失败（Metrics API 不可用）

**这说明：**
- 代码没有问题
- Agent 能够正常调用工具
- 只是集群缺少 Metrics Server

## 快速检查

```bash
# 检查 Metrics Server
kubectl get deployment metrics-server -n kube-system

# 如果不存在，安装它
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 等待就绪
kubectl wait --for=condition=available --timeout=300s deployment/metrics-server -n kube-system
```

## 临时解决方案

如果暂时无法安装 Metrics Server，可以：

1. **修改 System Prompt**，提示 Agent 使用替代方法
2. **在代码中捕获异常**，优雅处理错误
3. **使用其他工具**获取资源信息（如 `kubectl describe nodes`）

## 总结

- ✅ **问题**：集群缺少 Metrics Server
- ✅ **解决**：安装 Metrics Server 或配置 Agent 优雅处理错误
- ✅ **验证**：运行 `kubectl top nodes` 测试

