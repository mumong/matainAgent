# 添加新 MCP 服务器标准流程

## 📋 目录

1. [流程概览](#流程概览)
2. [详细步骤](#详细步骤)
3. [完整示例](#完整示例)
4. [最佳实践](#最佳实践)

---

## 流程概览

添加新 MCP 服务器的标准流程：

```
步骤 A: 调研和准备
    ↓
步骤 B: 创建 MCP 管理器模块
    ↓
步骤 C: 更新工具集成模块
    ↓
步骤 D: 更新配置文件
    ↓
步骤 E: 更新 Agent 配置
    ↓
步骤 F: 测试验证
```

---

## 详细步骤

### 步骤 A：调研和准备

#### A1. 了解 MCP 服务器

**目标：** 确定要集成的 MCP 服务器及其要求

**需要了解的信息：**
- MCP 服务器的 npm 包名或 GitHub 仓库
- 启动命令和参数
- 所需的环境变量（API keys、配置路径等）
- 提供的工具列表
- 特殊配置要求

**示例：**
```bash
# 查找 MCP 服务器
# 1. 访问 MCP Registry: https://mcp-registry.vercel.app/
# 2. 或搜索 npm: npm search mcp-server
# 3. 或查看 GitHub: https://github.com/search?q=mcp-server

# 例如：mcp-server-github
# 包名: @modelcontextprotocol/server-github
# 需要: GITHUB_PERSONAL_ACCESS_TOKEN
```

#### A2. 准备配置信息

**目标：** 收集所有必要的配置项

**检查清单：**
- [ ] API Key 或 Token（如果需要）
- [ ] 配置文件路径（如果有）
- [ ] 其他环境变量
- [ ] 特殊启动参数

**示例：**
```yaml
# 需要收集的信息
mcp_server_name: "github"
npm_package: "@modelcontextprotocol/server-github"
required_env:
  - GITHUB_PERSONAL_ACCESS_TOKEN
optional_env:
  - GITHUB_API_URL
```

---

### 步骤 B：创建 MCP 管理器模块

#### B1. 创建管理器文件

**文件位置：** `app/core/mcp/{mcp_name}_mcp.py`

**作用：** 封装 MCP 客户端的创建和管理逻辑

**模板：**
```python
"""
{MCP 名称} MCP 集成模块
用于将 {MCP 描述} MCP 服务器的工具集成到 Agent 中
"""
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from config.config_loader import get_config


class {MCPName}MCPManager:
    """{MCP 名称} MCP 管理器"""
    
    def __init__(self, **kwargs):
        """
        初始化 {MCP 名称} MCP 管理器
        
        Args:
            **kwargs: 配置参数（根据实际需求添加）
        """
        self.config = get_config()
        self.client = None
        self._tools = None
    
    def _create_client(self) -> MultiServerMCPClient:
        """创建 MCP 客户端"""
        env = {}
        
        # TODO: 添加环境变量配置
        # 从配置文件读取
        # env["API_KEY"] = self.config.get('model.mcp.{mcp_name}.api_key')
        
        return MultiServerMCPClient(
            {
                "{mcp_name}": {
                    "command": "npx",  # 或 "node", "python" 等
                    "args": [
                        "-y",
                        "{npm_package_name}"
                    ],
                    "env": env,
                    "transport": "stdio"
                }
            }
        )
    
    async def get_tools(self):
        """
        获取 {MCP 名称} MCP 工具列表
        
        Returns:
            List[Tool]: MCP 工具列表
        """
        if self._tools is None:
            if self.client is None:
                self.client = self._create_client()
            
            self._tools = await self.client.get_tools()
            print(f"✅ 成功加载 {len(self._tools)} 个 {MCP 名称} MCP 工具")
        
        return self._tools


# 全局实例（可选）
_{mcp_name}_mcp_manager: {MCPName}MCPManager | None = None


async def get_{mcp_name}_mcp_tools(**kwargs):
    """
    获取 {MCP 名称} MCP 工具（便捷函数）
    
    Args:
        **kwargs: 配置参数
    
    Returns:
        List[Tool]: MCP 工具列表
    """
    global _{mcp_name}_mcp_manager
    
    if _{mcp_name}_mcp_manager is None:
        _{mcp_name}_mcp_manager = {MCPName}MCPManager(**kwargs)
    
    return await _{mcp_name}_mcp_manager.get_tools()
```

#### B2. 实现具体逻辑

**关键点：**
1. **环境变量配置**：从配置文件读取必要的环境变量
2. **错误处理**：添加适当的异常处理
3. **日志输出**：添加有用的日志信息

---

### 步骤 C：更新工具集成模块

#### C1. 导入新模块

**文件：** `app/tools/mcp_tools.py`

**操作：** 在文件顶部添加导入

```python
from app.core.mcp.{mcp_name}_mcp import get_{mcp_name}_mcp_tools
```

#### C2. 更新 get_all_tools 函数

**操作：** 在 `get_all_tools` 函数中添加新 MCP 工具的加载逻辑

```python
async def get_all_tools(
    include_kubernetes: bool = True,
    include_{mcp_name}: bool = True,  # 新增参数
    kubernetes_non_destructive: bool = False,
    {mcp_name}_config: dict = None,  # 新增配置参数
) -> List[BaseTool]:
    """获取所有工具（本地工具 + MCP 工具）"""
    all_tools = list(tools_usage)  # 本地工具
    
    # 添加 Kubernetes MCP 工具
    if include_kubernetes:
        # ... 现有代码 ...
    
    # 添加 {MCP 名称} MCP 工具
    if include_{mcp_name}:
        try:
            {mcp_name}_tools = await get_{mcp_name}_mcp_tools(
                **(_{mcp_name}_config or {})
            )
            all_tools.extend({mcp_name}_tools)
            print(f"✅ 成功加载 {len({mcp_name}_tools)} 个 {MCP 名称} MCP 工具")
        except Exception as e:
            print(f"⚠️  加载 {MCP 名称} MCP 工具失败: {e}")
    
    return all_tools
```

#### C3. 更新同步版本

**操作：** 同样更新 `get_all_tools_sync` 函数

```python
def get_all_tools_sync(
    include_kubernetes: bool = True,
    include_{mcp_name}: bool = True,
    kubernetes_non_destructive: bool = False,
    {mcp_name}_config: dict = None,
) -> List[BaseTool]:
    """同步版本：获取所有工具"""
    return asyncio.run(
        get_all_tools(
            include_kubernetes=include_kubernetes,
            include_{mcp_name}=include_{mcp_name},
            kubernetes_non_destructive=kubernetes_non_destructive,
            {mcp_name}_config={_{mcp_name}_config},
        )
    )
```

---

### 步骤 D：更新配置文件

#### D1. 添加配置项

**文件：** `config/config.yaml`

**操作：** 在 `model.mcp` 下添加新 MCP 的配置

```yaml
model:
  mcp:
    kubernetes:
      non_destructive: false
    {mcp_name}:  # 新增
      api_key: "your-api-key-here"  # 根据实际需求添加
      # 其他配置项...
```

---

### 步骤 E：更新 Agent 配置

#### E1. 更新 Agent 初始化

**文件：** `app/core/agent.py`

**操作：** 更新工具加载逻辑

```python
# 加载所有工具（本地工具 + MCP 工具）
all_tools = get_all_tools_sync(
    include_kubernetes=True,
    include_{mcp_name}=True,  # 新增
    kubernetes_non_destructive=config.get('model.mcp.kubernetes.non_destructive', False),
    {mcp_name}_config=config.get('model.mcp.{mcp_name}', {}),  # 新增
)
```

---

### 步骤 F：测试验证

#### F1. 创建测试文件

**文件：** `app/test/{mcp_name}_mcp_test.py`

**模板：**
```python
"""
{MCP 名称} MCP 集成测试
"""
import asyncio
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from config.config_loader import get_config
from app.tools.mcp_tools import get_all_tools
from langgraph.checkpoint.memory import InMemorySaver


async def test_{mcp_name}_mcp():
    """测试 {MCP 名称} MCP 集成"""
    config = get_config()
    
    # 初始化模型
    model = init_chat_model(...)
    
    # 获取所有工具
    all_tools = await get_all_tools(
        include_{mcp_name}=True,
        {mcp_name}_config=config.get('model.mcp.{mcp_name}', {})
    )
    
    # 创建 Agent
    agent = create_agent(
        model=model,
        tools=all_tools,
        system_prompt="...",
        checkpointer=InMemorySaver(),
    )
    
    # 测试
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "测试消息"}]
    })
    
    print(result)


if __name__ == "__main__":
    asyncio.run(test_{mcp_name}_mcp())
```

#### F2. 运行测试

```bash
python app/test/{mcp_name}_mcp_test.py
```

---

## 完整示例：添加 GitHub MCP

### 步骤 A：调研

```yaml
mcp_server_name: "github"
npm_package: "@modelcontextprotocol/server-github"
required_env:
  - GITHUB_PERSONAL_ACCESS_TOKEN
```

### 步骤 B：创建管理器

**文件：** `app/core/mcp/github_mcp.py`

```python
"""
GitHub MCP 集成模块
"""
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from config.config_loader import get_config


class GitHubMCPManager:
    """GitHub MCP 管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.client = None
        self._tools = None
    
    def _create_client(self) -> MultiServerMCPClient:
        """创建 MCP 客户端"""
        env = {
            "GITHUB_PERSONAL_ACCESS_TOKEN": self.config.get('model.mcp.github.api_key')
        }
        
        return MultiServerMCPClient(
            {
                "github": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-github"
                    ],
                    "env": env,
                    "transport": "stdio"
                }
            }
        )
    
    async def get_tools(self):
        """获取 GitHub MCP 工具列表"""
        if self._tools is None:
            if self.client is None:
                self.client = self._create_client()
            
            self._tools = await self.client.get_tools()
            print(f"✅ 成功加载 {len(self._tools)} 个 GitHub MCP 工具")
        
        return self._tools


_github_mcp_manager: GitHubMCPManager | None = None


async def get_github_mcp_tools():
    """获取 GitHub MCP 工具（便捷函数）"""
    global _github_mcp_manager
    
    if _github_mcp_manager is None:
        _github_mcp_manager = GitHubMCPManager()
    
    return await _github_mcp_manager.get_tools()
```

### 步骤 C：更新工具集成

**文件：** `app/tools/mcp_tools.py`

```python
from app.core.mcp.github_mcp import get_github_mcp_tools

async def get_all_tools(
    include_kubernetes: bool = True,
    include_github: bool = True,  # 新增
    kubernetes_non_destructive: bool = False,
) -> List[BaseTool]:
    all_tools = list(tools_usage)
    
    # ... Kubernetes 代码 ...
    
    # 添加 GitHub MCP 工具
    if include_github:
        try:
            github_tools = await get_github_mcp_tools()
            all_tools.extend(github_tools)
            print(f"✅ 成功加载 {len(github_tools)} 个 GitHub MCP 工具")
        except Exception as e:
            print(f"⚠️  加载 GitHub MCP 工具失败: {e}")
    
    return all_tools
```

### 步骤 D：更新配置

**文件：** `config/config.yaml`

```yaml
model:
  mcp:
    kubernetes:
      non_destructive: false
    github:  # 新增
      api_key: "ghp_your_token_here"
```

### 步骤 E：更新 Agent

**文件：** `app/core/agent.py`

```python
all_tools = get_all_tools_sync(
    include_kubernetes=True,
    include_github=True,  # 新增
    kubernetes_non_destructive=config.get('model.mcp.kubernetes.non_destructive', False),
)
```

---

## 最佳实践

### 1. 命名规范

- **文件命名**：`{mcp_name}_mcp.py`（小写，下划线分隔）
- **类命名**：`{MCPName}MCPManager`（驼峰，首字母大写）
- **函数命名**：`get_{mcp_name}_mcp_tools`（小写，下划线分隔）

### 2. 错误处理

```python
try:
    tools = await get_mcp_tools()
except Exception as e:
    logger.error(f"加载 MCP 工具失败: {e}")
    # 不要抛出异常，让 Agent 继续使用其他工具
    return []
```

### 3. 配置验证

```python
def _validate_config(self):
    """验证配置是否完整"""
    api_key = self.config.get('model.mcp.{mcp_name}.api_key')
    if not api_key:
        raise ValueError("缺少必要的配置: model.mcp.{mcp_name}.api_key")
```

### 4. 文档注释

```python
"""
{MCP 名称} MCP 集成模块

功能：
- 提供 {功能1}
- 提供 {功能2}

要求：
- API Key: 需要在 config.yaml 中配置
- 其他要求...

示例：
    tools = await get_{mcp_name}_mcp_tools()
"""
```

### 5. 测试覆盖

- ✅ 测试工具加载
- ✅ 测试配置缺失情况
- ✅ 测试错误处理
- ✅ 测试实际工具调用

---

## 检查清单

完成所有步骤后，检查：

- [ ] 创建了 MCP 管理器模块
- [ ] 更新了工具集成模块
- [ ] 更新了配置文件
- [ ] 更新了 Agent 配置
- [ ] 创建了测试文件
- [ ] 测试通过
- [ ] 添加了文档注释
- [ ] 更新了相关文档

---

## 总结

添加新 MCP 服务器的标准流程：

1. **调研** → 了解 MCP 服务器要求
2. **创建管理器** → 封装 MCP 客户端逻辑
3. **集成工具** → 将 MCP 工具添加到工具列表
4. **配置** → 添加配置文件项
5. **更新 Agent** → 让 Agent 使用新工具
6. **测试** → 验证集成是否成功

每一步都有明确的作用和意义，遵循这个流程可以确保集成的质量和一致性。

