# 集成 Prometheus MCP 服务指南

## 📋 概述

本文档以 **Prometheus MCP 服务**为例，用伪代码的形式说明如何集成一个新的 MCP 服务到 Agent 中。

**目标：** 让 Agent 能够通过 MCP 协议访问 Prometheus，查询监控指标、查看告警规则等。

---

## 🔄 标准工作流程

```
步骤 1: 创建 MCP 管理器模块
    ↓
步骤 2: 配置 MultiServerMCPClient
    ↓
步骤 3: 实现获取 Tools 的方法
    ↓
步骤 4: 集成到 get_all_tools 函数
    ↓
步骤 5: 更新配置文件
    ↓
步骤 6: 完成（无需修改其他代码）
```

---

## 📝 详细步骤（伪代码）

### 步骤 1: 创建 MCP 管理器模块

**文件位置：** `app/core/mcp_servers/prometheus_mcp.py`

**作用：** 封装 Prometheus MCP 客户端的创建和管理逻辑

**伪代码：**

```python
"""
Prometheus MCP 集成模块
用于将 Prometheus MCP 服务器的工具集成到 Agent 中
"""

# 导入必要的库
导入 asyncio
导入 MultiServerMCPClient 从 langchain_mcp_adapters.client
导入 get_config 从 config.config_loader


定义类 PrometheusMCPManager:
    """Prometheus MCP 管理器"""
    
    定义 __init__(self, prometheus_url: str = None, token: str = None):
        """
        初始化 Prometheus MCP 管理器
        
        参数:
            prometheus_url: Prometheus 服务地址（例如: http://prometheus:9090）
            token: 认证 Token（如果需要）
        """
        self.config = 获取配置()
        self.prometheus_url = prometheus_url 或 从配置读取('model.mcp.prometheus.url')
        self.token = token 或 从配置读取('model.mcp.prometheus.token')
        self.client = None  # MCP 客户端实例
        self._tools = None  # 缓存的工具列表
    
    定义 _create_client(self) -> MultiServerMCPClient:
        """
        创建 MCP 客户端
        
        返回:
            MultiServerMCPClient: 配置好的 MCP 客户端
        """
        # 准备环境变量
        env = {}
        
        如果 self.prometheus_url:
            env["PROMETHEUS_URL"] = self.prometheus_url
        
        如果 self.token:
            env["PROMETHEUS_TOKEN"] = self.token
        
        # 创建 MultiServerMCPClient
        返回 MultiServerMCPClient({
            "prometheus": {
                "command": "npx",  # 启动命令
                "args": [
                    "-y",
                    "@prometheus/mcp-server-prometheus"  # MCP 服务器 npm 包名
                ],
                "env": env,  # 环境变量
                "transport": "stdio"  # 通信方式（标准输入输出）
            }
        })
    
    定义 async get_tools(self):
        """
        获取 Prometheus MCP 工具列表
        
        返回:
            List[Tool]: Prometheus MCP 工具列表
        """
        如果 self._tools 是 None:
            如果 self.client 是 None:
                self.client = self._create_client()
            
            # 从 MCP 客户端获取工具
            self._tools = 等待 self.client.get_tools()
            
            打印(f"✅ 成功加载 {len(self._tools)} 个 Prometheus MCP 工具")
            打印(f"📋 工具列表: {[t.name for t in self._tools[:10]]}...")
        
        返回 self._tools
    
    定义 async close(self):
        """关闭 MCP 客户端连接"""
        如果 self.client:
            # 如果客户端有关闭方法，在这里调用
            通过


# 全局实例（单例模式）
_全局_prometheus_mcp_manager: PrometheusMCPManager | None = None


定义 async get_prometheus_mcp_tools(
    prometheus_url: str = None,
    token: str = None
):
    """
    获取 Prometheus MCP 工具（便捷函数）
    
    参数:
        prometheus_url: Prometheus 服务地址（可选）
        token: 认证 Token（可选）
    
    返回:
        List[Tool]: Prometheus MCP 工具列表
    """
    全局 _全局_prometheus_mcp_manager
    
    # 如果配置改变，重新创建管理器
    如果 (_全局_prometheus_mcp_manager 是 None 或 
        _全局_prometheus_mcp_manager.prometheus_url != prometheus_url 或
        _全局_prometheus_mcp_manager.token != token):
        _全局_prometheus_mcp_manager = PrometheusMCPManager(
            prometheus_url=prometheus_url,
            token=token
        )
    
    返回 等待 _全局_prometheus_mcp_manager.get_tools()
```

**关键点说明：**

1. **类结构：** 使用 `PrometheusMCPManager` 类封装所有逻辑
2. **配置读取：** 从 `config.yaml` 读取配置，也支持参数传入
3. **客户端创建：** `_create_client()` 方法创建 `MultiServerMCPClient`
4. **工具缓存：** `_tools` 缓存工具列表，避免重复获取
5. **单例模式：** 使用全局变量实现单例，避免重复创建客户端

---

### 步骤 2: 配置 MultiServerMCPClient

**在 `_create_client()` 方法中：**

```python
MultiServerMCPClient({
    "prometheus": {  # 服务器名称（自定义）
        "command": "npx",  # 启动命令
        "args": [
            "-y",  # 自动确认安装
            "@prometheus/mcp-server-prometheus"  # MCP 服务器的 npm 包名
        ],
        "env": {  # 环境变量
            "PROMETHEUS_URL": "http://prometheus:9090",
            "PROMETHEUS_TOKEN": "your-token-here"  # 如果需要认证
        },
        "transport": "stdio"  # 通信方式：标准输入输出
    }
})
```

**配置说明：**

- **command:** 启动命令，通常是 `"npx"`（Node.js 包执行器）
- **args:** 命令参数
  - `"-y"`: 自动确认安装包（如果未安装）
  - `"@prometheus/mcp-server-prometheus"`: MCP 服务器的 npm 包名
- **env:** 环境变量字典
  - 用于传递配置信息（URL、Token 等）
  - MCP 服务器会读取这些环境变量
- **transport:** 通信方式，固定为 `"stdio"`（标准输入输出）

---

### 步骤 3: 实现获取 Tools 的方法

**在 `get_tools()` 方法中：**

```python
async def get_tools(self):
    # 1. 检查是否已缓存
    如果 self._tools 是 None:
        # 2. 检查客户端是否已创建
        如果 self.client 是 None:
            self.client = self._create_client()
        
        # 3. 调用 MCP 客户端获取工具
        self._tools = 等待 self.client.get_tools()
        
        # 4. 打印成功信息
        打印(f"✅ 成功加载 {len(self._tools)} 个 Prometheus MCP 工具")
    
    # 5. 返回工具列表
    返回 self._tools
```

**工作流程：**

1. **检查缓存：** 如果已获取过工具，直接返回缓存的工具列表
2. **创建客户端：** 如果客户端未创建，调用 `_create_client()` 创建
3. **获取工具：** 调用 `await self.client.get_tools()` 获取工具列表
   - 此时会启动 MCP 服务器子进程
   - 通过 stdio 与服务器通信
   - 获取服务器提供的所有工具
4. **缓存工具：** 将工具列表保存到 `self._tools`
5. **返回工具：** 返回工具列表

---

### 步骤 4: 集成到 get_all_tools 函数

**文件位置：** `app/tools/mcp_tools.py`

**修改 `get_all_tools()` 函数：**

```python
# 1. 导入 Prometheus MCP 工具获取函数
导入 get_prometheus_mcp_tools 从 app.core.mcp_servers.prometheus_mcp


定义 async get_all_tools(
    include_kubernetes: bool = True,
    kubernetes_non_destructive: bool = False,
    kubernetes_kubeconfig: str = None,
    kubernetes_context: str = None,
    # 新增参数
    include_prometheus: bool = True,  # 是否包含 Prometheus MCP 工具
    prometheus_url: str = None,  # Prometheus 服务地址
    prometheus_token: str = None,  # Prometheus 认证 Token
) -> List[BaseTool]:
    """
    获取所有工具（本地工具 + MCP 工具）
    """
    # 2. 初始化工具列表（包含本地工具）
    all_tools = 列表(tools_usage)  # 本地工具
    
    # 3. 添加 Kubernetes MCP 工具（原有逻辑）
    如果 include_kubernetes:
        尝试:
            k8s_tools = 等待 get_kubernetes_mcp_tools(...)
            all_tools.扩展(k8s_tools)
        捕获 异常 as e:
            打印(f"⚠️  加载 Kubernetes MCP 工具失败: {e}")
    
    # 4. 添加 Prometheus MCP 工具（新增逻辑）
    如果 include_prometheus:
        尝试:
            prometheus_tools = 等待 get_prometheus_mcp_tools(
                prometheus_url=prometheus_url,
                token=prometheus_token
            )
            all_tools.扩展(prometheus_tools)
            打印(f"✅ 总共加载了 {len(all_tools)} 个工具（{len(tools_usage)} 个本地 + {len(k8s_tools)} 个 K8s + {len(prometheus_tools)} 个 Prometheus）")
        捕获 异常 as e:
            打印(f"⚠️  加载 Prometheus MCP 工具失败: {e}")
            打印("   请确保：")
            打印("   1. 已安装 Node.js 和 npx")
            打印("   2. Prometheus MCP 服务器包已发布到 npm")
            打印("   3. 网络可以访问 npm registry")
            打印("   4. Prometheus 服务地址和 Token 配置正确")
    
    # 5. 返回所有工具
    返回 all_tools


定义 get_all_tools_sync(...):
    """
    同步版本：获取所有工具（本地工具 + MCP 工具）
    """
    # 使用 asyncio.run() 运行异步函数
    返回 asyncio.run(get_all_tools(...))
```

**关键点说明：**

1. **导入函数：** 从新创建的 `prometheus_mcp.py` 导入 `get_prometheus_mcp_tools`
2. **添加参数：** 在 `get_all_tools()` 函数中添加 Prometheus 相关参数
3. **条件加载：** 使用 `include_prometheus` 参数控制是否加载 Prometheus 工具
4. **错误处理：** 使用 `try-except` 捕获异常，避免一个 MCP 服务失败影响其他服务
5. **同步版本：** 在 `get_all_tools_sync()` 中也添加相应参数

---

### 步骤 5: 更新配置文件

**文件位置：** `config/config.yaml`

**添加 Prometheus 配置：**

```yaml
model:
  deepseek:
    api: "sk-..."
    # ... 其他配置
  mcp:
    amap-maps:
      api_key: "..."
    kubernetes:
      non_destructive: false
    # 新增 Prometheus 配置
    prometheus:
      # Prometheus 服务地址
      # 格式: http://host:port 或 https://host:port
      url: "http://prometheus:9090"
      
      # 认证 Token（如果需要）
      # 如果 Prometheus 需要认证，在这里配置 Token
      token: "your-prometheus-token-here"
      
      # 或者使用 Bearer Token
      # bearer_token: "your-bearer-token"
```

**配置说明：**

- **url:** Prometheus 服务的完整地址
  - 示例：`http://prometheus:9090`
  - 示例：`https://prometheus.example.com:9090`
- **token:** 认证 Token（如果需要）
  - 某些 Prometheus 实例可能需要认证
  - 根据实际 MCP 服务器的要求配置

---

### 步骤 6: 更新 Agent 配置（可选）

**文件位置：** `app/core/agent.py`

**如果需要在 Agent 中读取配置：**

```python
# 加载所有工具（本地工具 + Kubernetes MCP 工具 + Prometheus MCP 工具）
k8s_config = 配置.get('model.mcp.kubernetes', {})
prometheus_config = 配置.get('model.mcp.prometheus', {})  # 新增

all_tools = get_all_tools_sync(
    include_kubernetes=True,
    kubernetes_non_destructive=k8s_config.get('non_destructive', False),
    kubernetes_kubeconfig=k8s_config.get('kubeconfig'),
    kubernetes_context=k8s_config.get('context'),
    # 新增 Prometheus 配置
    include_prometheus=True,
    prometheus_url=prometheus_config.get('url'),
    prometheus_token=prometheus_config.get('token'),
)
```

**说明：**

- 这一步是**可选的**
- 如果不在 Agent 中读取配置，Prometheus 工具会使用 `prometheus_mcp.py` 中从配置文件读取的默认值
- 如果需要在运行时动态配置，才需要在这里传递参数

---

## ✅ 完成检查清单

完成以上步骤后，检查以下内容：

- [ ] 创建了 `app/core/mcp_servers/prometheus_mcp.py` 文件
- [ ] 实现了 `PrometheusMCPManager` 类
- [ ] 实现了 `get_prometheus_mcp_tools()` 函数
- [ ] 在 `app/tools/mcp_tools.py` 中导入了 `get_prometheus_mcp_tools`
- [ ] 在 `get_all_tools()` 函数中添加了 Prometheus 工具加载逻辑
- [ ] 在 `get_all_tools_sync()` 函数中添加了相应参数
- [ ] 在 `config/config.yaml` 中添加了 Prometheus 配置
- [ ] （可选）在 `app/core/agent.py` 中读取配置并传递参数

---

## 🎯 关键理解

### 1. 工作流程总结

```
创建管理器模块
    ↓
配置 MultiServerMCPClient（包含命令、参数、环境变量）
    ↓
实现获取 Tools 的方法（调用 client.get_tools()）
    ↓
集成到 get_all_tools 函数（添加参数和加载逻辑）
    ↓
更新配置文件（添加 MCP 服务的配置项）
    ↓
完成（Agent 会自动使用新工具）
```

### 2. 为什么不需要修改其他代码？

**原因：**

1. **Agent 使用统一的工具接口：** `create_agent()` 接收工具列表，不关心工具来源
2. **工具自动注册：** 通过 `get_all_tools()` 函数，所有工具（本地 + MCP）都会自动添加到 Agent
3. **透明集成：** Agent 调用工具时，不需要知道工具是来自本地还是 MCP 服务器

**工作流程：**

```
Agent 调用工具
    ↓
工具执行（可能是本地函数或 MCP 工具）
    ↓
如果是 MCP 工具，通过 MultiServerMCPClient 与 MCP 服务器通信
    ↓
MCP 服务器执行实际操作（查询 Prometheus API）
    ↓
返回结果给 Agent
```

### 3. MultiServerMCPClient 的作用

**MultiServerMCPClient 是连接 Agent 和 MCP 服务器的桥梁：**

1. **启动子进程：** 通过 `subprocess` 启动 MCP 服务器（如 `npx @prometheus/mcp-server-prometheus`）
2. **建立通信：** 通过 stdio（标准输入输出）与子进程通信
3. **协议转换：** 将 LangChain 的工具调用转换为 MCP 协议消息
4. **工具注册：** 从 MCP 服务器获取工具列表，注册到 LangChain

---

## 📚 实际代码示例

### 完整的 prometheus_mcp.py

```python
"""
Prometheus MCP 集成模块
用于将 Prometheus MCP 服务器的工具集成到 Agent 中
"""
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from config.config_loader import get_config


class PrometheusMCPManager:
    """Prometheus MCP 管理器"""
    
    def __init__(self, prometheus_url: str = None, token: str = None):
        self.config = get_config()
        self.prometheus_url = prometheus_url or self.config.get('model.mcp.prometheus.url')
        self.token = token or self.config.get('model.mcp.prometheus.token')
        self.client = None
        self._tools = None
    
    def _create_client(self) -> MultiServerMCPClient:
        """创建 MCP 客户端"""
        env = {}
        
        if self.prometheus_url:
            env["PROMETHEUS_URL"] = self.prometheus_url
        
        if self.token:
            env["PROMETHEUS_TOKEN"] = self.token
        
        return MultiServerMCPClient(
            {
                "prometheus": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@prometheus/mcp-server-prometheus"  # 注意：这是示例包名，实际需要查找正确的包名
                    ],
                    "env": env,
                    "transport": "stdio"
                }
            }
        )
    
    async def get_tools(self):
        """获取 Prometheus MCP 工具列表"""
        if self._tools is None:
            if self.client is None:
                self.client = self._create_client()
            
            self._tools = await self.client.get_tools()
            print(f"✅ 成功加载 {len(self._tools)} 个 Prometheus MCP 工具")
            print(f"📋 工具列表: {[t.name for t in self._tools[:10]]}...")
        
        return self._tools
    
    async def close(self):
        """关闭 MCP 客户端连接"""
        if self.client:
            pass


# 全局实例
_prometheus_mcp_manager: PrometheusMCPManager | None = None


async def get_prometheus_mcp_tools(
    prometheus_url: str = None,
    token: str = None
):
    """获取 Prometheus MCP 工具（便捷函数）"""
    global _prometheus_mcp_manager
    
    if (_prometheus_mcp_manager is None or 
        _prometheus_mcp_manager.prometheus_url != prometheus_url or
        _prometheus_mcp_manager.token != token):
        _prometheus_mcp_manager = PrometheusMCPManager(
            prometheus_url=prometheus_url,
            token=token
        )
    
    return await _prometheus_mcp_manager.get_tools()
```

---

## 🔍 查找 MCP 服务器

### 如何找到 Prometheus MCP 服务器？

1. **MCP Registry：** https://mcp-registry.vercel.app/
2. **npm 搜索：** `npm search mcp-server-prometheus`
3. **GitHub 搜索：** `github.com search mcp-server-prometheus`
4. **官方文档：** 查看 Model Context Protocol 官方文档

### 如果找不到现成的 MCP 服务器？

**选项 1：创建自定义 MCP 服务器**

- 参考 MCP 协议规范
- 使用 TypeScript/JavaScript 实现
- 发布到 npm

**选项 2：使用 HTTP 工具**

- 创建 LangChain HTTP 工具
- 直接调用 Prometheus API
- 不需要 MCP 服务器

---

## 🎉 总结

集成新 MCP 服务的标准流程：

1. ✅ **创建管理器模块** - 封装 MCP 客户端逻辑
2. ✅ **配置 MultiServerMCPClient** - 指定命令、参数、环境变量
3. ✅ **实现获取 Tools 方法** - 调用 `client.get_tools()`
4. ✅ **集成到 get_all_tools** - 添加参数和加载逻辑
5. ✅ **更新配置文件** - 添加 MCP 服务的配置项
6. ✅ **完成** - Agent 自动使用新工具，无需修改其他代码

**关键点：** 所有工具（本地 + MCP）都通过统一的 `get_all_tools()` 函数提供给 Agent，Agent 不需要知道工具的具体来源。

