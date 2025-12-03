# Kubernetes MCP 快速开始

## 🚀 快速集成步骤

### 1. 前置检查

```bash
# 检查 Node.js
node --version  # 需要 >= 14.x
npx --version

# 检查 kubectl
kubectl version --client

# 检查集群连接
kubectl get nodes
```

### 2. 配置（可选）

编辑 `config/config.yaml`：

```yaml
model:
  mcp:
    kubernetes:
      non_destructive: false  # true = 只读模式，false = 完整权限
```

### 3. 使用

#### 方式1：直接使用 Agent（推荐）

Agent 已经自动集成了 Kubernetes MCP 工具，直接使用即可：

```python
# app/core/agent.py 已经配置好了
from app.core.agent import agent

result = agent.invoke({
    "messages": "查看 default 命名空间的所有 Pod"
})
```

#### 方式2：测试集成

```bash
# 运行测试脚本
python app/test/k8s_mcp_test.py
```

## 📝 使用示例

### 示例1：查看集群状态

```python
result = agent.invoke({
    "messages": "我的 Kubernetes 集群有什么问题？"
})
```

### 示例2：查看资源

```python
result = agent.invoke({
    "messages": "查看 default 命名空间中的 deployments 和 services"
})
```

### 示例3：创建资源

```python
result = agent.invoke({
    "messages": "在 default 命名空间创建一个名为 test-nginx 的 Deployment，使用 nginx:latest 镜像，副本数为 2"
})
```

### 示例4：故障诊断

```python
result = agent.invoke({
    "messages": "诊断 default 命名空间中包含 'web' 关键字的 Pod 问题"
})
```

## ⚠️ 注意事项

1. **首次运行**：npx 会自动下载 `mcp-server-kubernetes` 包，可能需要一些时间
2. **权限**：确保 kubectl 有足够的权限执行操作
3. **安全**：生产环境建议设置 `non_destructive: true`

## 🔧 故障排查

### 问题：无法加载工具

**检查清单：**
- [ ] Node.js 已安装
- [ ] kubectl 已配置
- [ ] 网络可以访问 npm registry
- [ ] kubeconfig 文件存在且有效

### 问题：权限不足

**解决方案：**
```bash
# 检查当前上下文
kubectl config current-context

# 检查权限
kubectl auth can-i get pods --all-namespaces
```

## 📚 更多信息

详细文档请参考：[KUBERNETES_MCP_INTEGRATION.md](./KUBERNETES_MCP_INTEGRATION.md)

