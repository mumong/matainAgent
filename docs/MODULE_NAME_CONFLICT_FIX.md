# 模块名冲突问题修复

## 问题描述

运行 `python3 app/core/agent.py` 时出现错误：

```
ImportError: cannot import name 'ClientSession' from 'mcp'
```

## 问题原因

**模块名冲突**：项目中的 `app/core/mcp/` 目录名与第三方包 `mcp` 冲突。

当 `langchain_mcp_adapters` 尝试导入：
```python
from mcp import ClientSession
```

Python 的模块搜索顺序：
1. 当前目录
2. 项目目录（`app/core/mcp/`）
3. 第三方包目录

Python 找到了本地的 `app/core/mcp/` 目录，而不是应该导入的第三方 `mcp` 包，导致导入失败。

## 解决方案

**重命名目录**：将 `app/core/mcp/` 重命名为 `app/core/mcp_servers/`

### 修复步骤

1. **重命名目录**
   ```bash
   mv app/core/mcp app/core/mcp_servers
   ```

2. **更新导入语句**
   ```python
   # 修改前
   from app.core.mcp.kubernetes_mcp import get_kubernetes_mcp_tools
   
   # 修改后
   from app.core.mcp_servers.kubernetes_mcp import get_kubernetes_mcp_tools
   ```

## 验证修复

```bash
# 测试导入
python3 -c "from app.core.mcp_servers.kubernetes_mcp import get_kubernetes_mcp_tools; print('OK')"

# 运行 agent
python3 app/core/agent.py
```

## 预防措施

### 命名规范

在创建新目录/模块时，避免使用可能与第三方包冲突的名称：

**避免使用的名称：**
- `mcp` - 与 `mcp` 包冲突
- `langchain` - 与 `langchain` 包冲突
- `pydantic` - 与 `pydantic` 包冲突
- `asyncio` - 与标准库冲突

**推荐的命名方式：**
- 使用描述性名称：`mcp_servers`, `mcp_integrations`, `mcp_adapters`
- 添加项目前缀：`app_mcp`, `my_mcp`
- 使用复数形式：`mcp_servers`, `tools`, `adapters`

### 检查冲突

在创建新模块前，可以检查是否与现有包冲突：

```python
# 检查是否可以导入
try:
    import mcp
    print("警告：'mcp' 包已存在，避免使用此名称作为模块名")
except ImportError:
    print("'mcp' 包不存在，可以使用")
```

## 相关文件

已更新的文件：
- `app/tools/mcp_tools.py` - 更新导入路径
- 目录重命名：`app/core/mcp/` → `app/core/mcp_servers/`

## 总结

- ✅ **问题**：模块名冲突导致导入失败
- ✅ **解决**：重命名目录避免冲突
- ✅ **预防**：使用描述性、唯一的模块名称

