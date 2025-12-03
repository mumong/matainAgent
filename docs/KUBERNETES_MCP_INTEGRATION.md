# Kubernetes MCP 集成指南

## 概述

本项目已集成 [mcp-server-kubernetes](https://github.com/Flux159/mcp-server-kubernetes)，让 Agent 可以直接操作 Kubernetes 集群。

## 功能特性

通过 Kubernetes MCP 集成，Agent 可以：

### 基础操作
- ✅ 查看资源：`kubectl_get`, `kubectl_describe`
- ✅ 创建资源：`kubectl_create`, `kubectl_apply`
- ✅ 更新资源：`kubectl_patch`, `kubectl_scale`
- ✅ 删除资源：`kubectl_delete`（非破坏性模式下禁用）
- ✅ 查看日志：`kubectl_logs`
- ✅ 管理上下文：`kubectl_context`

### 高级操作
- ✅ Helm 操作：安装、升级、卸载 Helm Chart
- ✅ 端口转发：`port_forward`
- ✅ Pod 清理：清理异常状态的 Pod
- ✅ 节点管理：节点维护操作（cordon、drain、uncordon）
- ✅ 故障诊断：`k8s-diagnose` 提示词

## 前置要求

### 1. 安装 Node.js 和 npx

```bash
# 检查是否已安装
node --version
npx --version

# 如果未安装，请安装 Node.js
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs
```

### 2. 配置 kubectl

```bash
# 检查 kubectl 是否已安装
kubectl version --client

# 如果未安装，请安装 kubectl
# 参考：https://kubernetes.io/docs/tasks/tools/

# 配置 kubeconfig（通常位于 ~/.kube/config）
# 确保可以访问你的 Kubernetes 集群
kubectl get nodes
```

### 3. 验证连接

```bash
# 测试 kubectl 连接
kubectl cluster-info
kubectl get namespaces
```

## 配置说明

在 `config/config.yaml` 中配置：

```yaml
model:
  mcp:
    kubernetes:
      # 非破坏性模式
      # true: 只允许只读和创建/更新操作，禁止删除操作
      # false: 允许所有操作（包括删除）
      non_destructive: false
```

### 非破坏性模式

启用非破坏性模式（`non_destructive: true`）后：

**允许的操作：**
- ✅ 查看资源信息
- ✅ 创建和更新资源
- ✅ 查看日志
- ✅ Helm 安装/升级
- ✅ 端口转发

**禁止的操作：**
- ❌ 删除资源
- ❌ Helm 卸载
- ❌ Pod 清理
- ❌ 节点管理（可能涉及 drain）

## 使用方法

### 方式1：在 Agent 中使用（已集成）

Agent 启动时会自动加载 Kubernetes MCP 工具，可以直接使用：

```python
# agent 已经包含了所有 Kubernetes 工具
result = agent.invoke({
    "messages": "查看 default 命名空间的所有 Pod"
})
```

### 方式2：单独测试

```python
from app.tools.mcp_tools import get_all_tools_sync

# 获取所有工具（包括 Kubernetes MCP 工具）
tools = get_all_tools_sync(include_kubernetes=True)

# 查看工具列表
for tool in tools:
    print(f"- {tool.name}: {tool.description}")
```

## 使用示例

### 示例1：查看集群状态

```python
result = agent.invoke({
    "messages": "我的 Kubernetes 集群有什么问题？请检查所有命名空间的 Pod 状态"
})
```

### 示例2：查看特定资源

```python
result = agent.invoke({
    "messages": "查看 default 命名空间中的 deployments"
})
```

### 示例3：创建资源

```python
result = agent.invoke({
    "messages": "在 default 命名空间创建一个名为 test-pod 的 Pod，使用 nginx 镜像"
})
```

### 示例4：故障诊断

```python
result = agent.invoke({
    "messages": "诊断 default 命名空间中包含 'web' 关键字的 Pod 问题"
})
```

## 安全建议

1. **生产环境建议启用非破坏性模式**
   ```yaml
   non_destructive: true
   ```

2. **使用 RBAC 限制权限**
   - 为 Agent 创建专用的 ServiceAccount
   - 使用最小权限原则配置 Role/RoleBinding

3. **监控和审计**
   - 启用 Kubernetes 审计日志
   - 监控 Agent 的操作

## 故障排查

### 问题1：无法加载 Kubernetes MCP 工具

**错误信息：**
```
⚠️  加载 Kubernetes MCP 工具失败: ...
```

**解决方案：**
1. 检查 Node.js 和 npx 是否已安装
2. 检查网络是否可以访问 npm registry
3. 检查 kubectl 配置是否正确

### 问题2：权限不足

**错误信息：**
```
Error from server (Forbidden): ...
```

**解决方案：**
1. 检查 kubeconfig 中的用户权限
2. 使用 RBAC 授予必要权限
3. 考虑使用非破坏性模式

### 问题3：连接超时

**错误信息：**
```
Unable to connect to the server: ...
```

**解决方案：**
1. 检查 Kubernetes 集群是否可访问
2. 检查网络连接
3. 验证 kubeconfig 配置

## 参考资源

- [mcp-server-kubernetes GitHub](https://github.com/Flux159/mcp-server-kubernetes)
- [Kubernetes 官方文档](https://kubernetes.io/docs/)
- [kubectl 命令参考](https://kubernetes.io/docs/reference/kubectl/)

## 支持的工具列表

Kubernetes MCP 服务器提供以下工具（部分）：

- `kubectl_get` - 获取资源
- `kubectl_describe` - 描述资源
- `kubectl_create` - 创建资源
- `kubectl_apply` - 应用 YAML
- `kubectl_delete` - 删除资源
- `kubectl_logs` - 查看日志
- `kubectl_scale` - 扩缩容
- `kubectl_patch` - 更新资源
- `kubectl_rollout` - 管理部署
- `port_forward` - 端口转发
- `install_helm_chart` - 安装 Helm Chart
- `upgrade_helm_chart` - 升级 Helm Chart
- `cleanup_pods` - 清理 Pod
- `node_management` - 节点管理
- `k8s-diagnose` - 故障诊断提示词

完整列表请参考 [mcp-server-kubernetes 文档](https://github.com/Flux159/mcp-server-kubernetes)。

