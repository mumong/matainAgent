# MCP 工作流程与配置详解

## 📋 目录

1. [MCP 工作原理](#mcp-工作原理)
2. [Kubernetes 集群配置](#kubernetes-集群配置)
3. [多集群管理](#多集群管理)
4. [配置详解](#配置详解)

---

## MCP 工作原理

### 1. 整体架构

```
┌─────────────────┐
│   Your Agent    │
│  (LangChain)    │
└────────┬────────┘
         │
         │ 1. 创建 MCP 客户端
         ▼
┌─────────────────┐
│ MultiServerMCP  │
│     Client      │
└────────┬────────┘
         │
         │ 2. 启动子进程 (stdio)
         ▼
┌─────────────────┐
│  MCP Server     │
│  (npx process)  │
└────────┬────────┘
         │
         │ 3. 执行命令/API 调用
         ▼
┌─────────────────┐
│  External       │
│  Service/API    │
│  (K8s, Maps...) │
└─────────────────┘
```

### 2. 详细工作流程

#### 步骤 A：初始化阶段

```python
# 1. 创建 MultiServerMCPClient
mcp_client = MultiServerMCPClient({
    "kubernetes": {
        "command": "npx",           # 启动命令
        "args": ["-y", "mcp-server-kubernetes"],  # 命令参数
        "env": {...},                # 环境变量
        "transport": "stdio"         # 通信方式
    }
})
```

**发生了什么：**
- `MultiServerMCPClient` 创建一个配置字典
- 配置指定了如何启动 MCP 服务器进程
- **此时还没有启动进程**

#### 步骤 B：获取工具阶段

```python
# 2. 获取工具列表
tools = await mcp_client.get_tools()
```

**发生了什么：**
1. **启动子进程**：`MultiServerMCPClient` 使用 `subprocess` 启动：
   ```bash
   npx -y mcp-server-kubernetes
   ```
2. **建立 stdio 通信**：通过标准输入/输出与子进程通信
3. **MCP 协议握手**：客户端和服务器建立 MCP 协议连接
4. **获取工具列表**：服务器返回所有可用工具的元数据
5. **转换为 LangChain Tools**：`langchain_mcp_adapters` 将 MCP 工具转换为 LangChain 工具格式

#### 步骤 C：Agent 使用阶段

```python
# 3. Agent 调用工具
agent = create_agent(model=model, tools=tools)
result = await agent.ainvoke({"messages": "查看 Pod"})
```

**发生了什么：**
1. **Agent 决策**：LLM 决定调用哪个工具（如 `kubectl_get`）
2. **工具调用**：Agent 调用工具，传入参数
3. **MCP 转发**：工具调用被转发到 MCP 客户端
4. **MCP 协议通信**：客户端通过 stdio 发送请求到 MCP 服务器
5. **服务器执行**：MCP 服务器执行实际操作（如 `kubectl get pods`）
6. **返回结果**：结果通过 MCP 协议返回，最终到达 Agent

### 3. 关键点理解

#### 为什么使用 stdio？

- **隔离性**：MCP 服务器作为独立进程运行，不会影响主程序
- **标准化**：stdio 是跨平台的标准通信方式
- **简单性**：不需要网络配置、端口管理等复杂操作

#### 为什么使用 npx？

- **自动安装**：`-y` 参数自动下载并运行 npm 包
- **版本管理**：npm 自动处理版本和依赖
- **跨平台**：npx 在 Windows、Linux、macOS 都能工作

---

## Kubernetes 集群配置

### 1. 当前配置的工作原理

当你运行 Agent 时，Kubernetes MCP 服务器会：

1. **读取 kubectl 配置**：使用系统默认的 `~/.kube/config` 文件
2. **使用当前上下文**：使用 `kubectl config current-context` 指定的集群
3. **执行命令**：所有 `kubectl` 命令都在当前上下文的集群上执行

### 2. 访问当前集群

**默认行为：**
```python
# 当前配置会自动使用 ~/.kube/config 中的当前上下文
mcp_client = MultiServerMCPClient({
    "kubernetes": {
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
        "env": {},  # 空环境变量 = 使用系统默认配置
        "transport": "stdio"
    }
})
```

**验证当前集群：**
```bash
# 查看当前上下文
kubectl config current-context

# 查看所有上下文
kubectl config get-contexts

# 查看当前集群信息
kubectl cluster-info
```

### 3. 访问其他集群的方法

#### 方法1：切换 kubectl 上下文（推荐）

```bash
# 查看所有上下文
kubectl config get-contexts

# 切换到目标集群
kubectl config use-context <context-name>

# 验证
kubectl config current-context
```

**优点：**
- ✅ 简单直接
- ✅ 不需要修改代码
- ✅ 适用于临时切换

**缺点：**
- ❌ 全局切换，影响所有 kubectl 命令
- ❌ 需要手动切换

#### 方法2：指定 KUBECONFIG 环境变量

```python
# 为不同的集群创建不同的 MCP 客户端
cluster1_client = MultiServerMCPClient({
    "kubernetes": {
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
        "env": {
            "KUBECONFIG": "/path/to/cluster1/kubeconfig"
        },
        "transport": "stdio"
    }
})

cluster2_client = MultiServerMCPClient({
    "kubernetes": {
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
        "env": {
            "KUBECONFIG": "/path/to/cluster2/kubeconfig"
        },
        "transport": "stdio"
    }
})
```

**优点：**
- ✅ 可以同时访问多个集群
- ✅ 不需要切换全局配置
- ✅ 适合多集群场景

**缺点：**
- ❌ 需要管理多个 kubeconfig 文件
- ❌ 代码复杂度增加

#### 方法3：在 kubeconfig 中指定上下文

```python
# 使用 KUBECONFIG 和 KUBECTL_CONTEXT 环境变量
mcp_client = MultiServerMCPClient({
    "kubernetes": {
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
        "env": {
            "KUBECONFIG": "/path/to/kubeconfig",
            "KUBECTL_CONTEXT": "production-cluster"  # 指定上下文
        },
        "transport": "stdio"
    }
})
```

---

## 多集群管理

### 方案1：动态切换（推荐用于单 Agent）

```python
# app/core/mcp/kubernetes_mcp.py

class KubernetesMCPManager:
    def __init__(self, kubeconfig_path: str = None, context: str = None):
        self.kubeconfig_path = kubeconfig_path
        self.context = context
    
    def _create_client(self) -> MultiServerMCPClient:
        env = {}
        
        # 指定 kubeconfig 路径
        if self.kubeconfig_path:
            env["KUBECONFIG"] = self.kubeconfig_path
        
        # 指定上下文（如果 kubeconfig 中有多个上下文）
        if self.context:
            env["KUBECTL_CONTEXT"] = self.context
        
        return MultiServerMCPClient({
            "kubernetes": {
                "command": "npx",
                "args": ["-y", "mcp-server-kubernetes"],
                "env": env,
                "transport": "stdio"
            }
        })
```

**配置文件：**
```yaml
# config/config.yaml
model:
  mcp:
    kubernetes:
      # 使用默认配置（~/.kube/config 的当前上下文）
      kubeconfig: null
      context: null
      
      # 或者指定特定配置
      # kubeconfig: "/path/to/kubeconfig"
      # context: "production-cluster"
```

### 方案2：多客户端（推荐用于多集群）

```python
# app/core/mcp/multi_cluster_mcp.py

class MultiClusterMCPManager:
    def __init__(self):
        self.clients = {}
    
    async def get_cluster_tools(self, cluster_name: str):
        """获取指定集群的工具"""
        if cluster_name not in self.clients:
            config = get_config()
            cluster_config = config.get(f'model.mcp.kubernetes.clusters.{cluster_name}')
            
            self.clients[cluster_name] = MultiServerMCPClient({
                "kubernetes": {
                    "command": "npx",
                    "args": ["-y", "mcp-server-kubernetes"],
                    "env": {
                        "KUBECONFIG": cluster_config.get("kubeconfig"),
                        "KUBECTL_CONTEXT": cluster_config.get("context")
                    },
                    "transport": "stdio"
                }
            })
        
        return await self.clients[cluster_name].get_tools()
```

**配置文件：**
```yaml
# config/config.yaml
model:
  mcp:
    kubernetes:
      clusters:
        production:
          kubeconfig: "/path/to/prod/kubeconfig"
          context: "prod-cluster"
        staging:
          kubeconfig: "/path/to/staging/kubeconfig"
          context: "staging-cluster"
        development:
          kubeconfig: "/path/to/dev/kubeconfig"
          context: "dev-cluster"
```

---

## 配置详解

### 1. MCP 服务器配置结构

```python
{
    "server_name": {                    # 服务器标识符（唯一）
        "command": "npx",              # 启动命令
        "args": ["-y", "package-name"], # 命令参数
        "env": {                        # 环境变量
            "KEY": "value"
        },
        "transport": "stdio"            # 通信方式（目前只支持 stdio）
    }
}
```

### 2. 环境变量的作用

环境变量会传递给 MCP 服务器进程，服务器可以使用这些变量：

- **配置认证**：API keys、tokens
- **指定资源路径**：配置文件路径
- **控制行为**：功能开关、模式设置

### 3. Kubernetes 特定配置

| 环境变量 | 作用 | 示例 |
|---------|------|------|
| `KUBECONFIG` | 指定 kubeconfig 文件路径 | `/path/to/kubeconfig` |
| `KUBECTL_CONTEXT` | 指定使用的上下文 | `production-cluster` |
| `ALLOW_ONLY_NON_DESTRUCTIVE_TOOLS` | 启用非破坏性模式 | `true` |

### 4. 配置优先级

1. **环境变量**（代码中 `env` 字典）
2. **系统环境变量**（如果代码中未指定）
3. **默认值**（kubectl 默认使用 `~/.kube/config`）

---

## 实际示例

### 示例1：使用默认集群

```python
# 使用 ~/.kube/config 的当前上下文
mcp_client = MultiServerMCPClient({
    "kubernetes": {
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
        "env": {},
        "transport": "stdio"
    }
})
```

### 示例2：使用指定 kubeconfig

```python
# 使用指定的 kubeconfig 文件
mcp_client = MultiServerMCPClient({
    "kubernetes": {
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
        "env": {
            "KUBECONFIG": "/home/user/.kube/prod-config"
        },
        "transport": "stdio"
    }
})
```

### 示例3：使用指定上下文

```python
# 使用 kubeconfig 中的特定上下文
mcp_client = MultiServerMCPClient({
    "kubernetes": {
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
        "env": {
            "KUBECONFIG": "/home/user/.kube/config",
            "KUBECTL_CONTEXT": "production"
        },
        "transport": "stdio"
    }
})
```

### 示例4：非破坏性模式

```python
# 只允许只读和创建/更新操作
mcp_client = MultiServerMCPClient({
    "kubernetes": {
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
        "env": {
            "ALLOW_ONLY_NON_DESTRUCTIVE_TOOLS": "true"
        },
        "transport": "stdio"
    }
})
```

---

## 总结

1. **MCP 通过 stdio 与子进程通信**，子进程执行实际命令
2. **Kubernetes MCP 使用 kubectl**，读取系统的 kubeconfig 配置
3. **访问不同集群**可以通过：
   - 切换 kubectl 上下文（简单）
   - 指定 KUBECONFIG 环境变量（灵活）
   - 使用多客户端（多集群）
4. **配置通过环境变量传递**，MCP 服务器读取这些变量

