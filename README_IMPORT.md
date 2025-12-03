# 模块导入解决方案

本项目提供了多种解决模块导入问题的方法，适用于不同场景。

## 方案1：可编辑安装（推荐，业界标准做法）⭐

这是**大型项目最推荐的做法**，被 Django、Flask、LangChain 等主流项目采用。

### 安装步骤：

```bash
# 在项目根目录执行
pip install -e .
```

### 优点：
- ✅ 一次安装，全局可用
- ✅ 不需要在每个文件中添加路径设置代码
- ✅ 符合 Python 包管理最佳实践
- ✅ 支持 `python -m` 方式运行
- ✅ IDE 可以正确识别和自动补全

### 使用方式：

安装后，可以直接在任何地方导入：

```python
from config.config_loader import get_config
from app.core.agent import model_usage
from app.tools.base import tools_usage
```

### 运行方式：

```bash
# 方式1：直接运行（推荐）
python app/core/agent.py

# 方式2：模块方式运行
python -m app.core.agent
```

---

## 方案2：使用路径设置工具（简单实用）

如果不想安装包，可以在文件开头使用统一的路径设置工具。

### 使用方法：

在任何需要导入项目模块的文件开头添加：

```python
from app.utils.path_setup import setup_path
setup_path()  # 这行可以省略，因为会自动执行

# 然后正常导入
from config.config_loader import get_config
from app.core.agent import model_usage
```

### 优点：
- ✅ 不需要安装
- ✅ 统一管理，易于维护
- ✅ 可以从任何位置运行

---

## 方案3：从项目根目录运行（最简单）

### 使用方法：

```bash
# 确保在项目根目录
cd /root/huhu/agent/matain_agent

# 使用 -m 方式运行
python -m app.core.agent
```

### 优点：
- ✅ 不需要任何额外配置
- ✅ Python 会自动处理模块路径

### 缺点：
- ❌ 必须从项目根目录运行
- ❌ 不能直接运行 `python app/core/agent.py`

---

## 方案4：环境变量（适合生产环境）

### 设置方式：

```bash
export PYTHONPATH=/root/huhu/agent/matain_agent:$PYTHONPATH
```

### 优点：
- ✅ 系统级配置，一次设置
- ✅ 适合生产环境

---

## 推荐方案对比

| 方案 | 适用场景 | 专业程度 | 易用性 |
|------|---------|---------|--------|
| 可编辑安装 | 开发/生产 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 路径设置工具 | 快速开发 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 模块方式运行 | 简单项目 | ⭐⭐ | ⭐⭐⭐ |
| 环境变量 | 生产环境 | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 业界实践

### 大型开源项目通常使用：

1. **Django** - 使用 `setup.py` + 可编辑安装
2. **Flask** - 使用 `pyproject.toml` + 可编辑安装
3. **LangChain** - 使用 `pyproject.toml` + 可编辑安装
4. **FastAPI** - 使用 `pyproject.toml` + 可编辑安装

### 为什么推荐可编辑安装？

1. **符合 PEP 标准** - Python 官方推荐的包管理方式
2. **IDE 友好** - 自动补全和类型检查正常工作
3. **测试友好** - 测试框架可以正确发现和导入模块
4. **部署友好** - 生产环境可以直接使用 `pip install .`
5. **团队协作** - 所有开发者使用相同的方式，减少问题

---

## 快速开始

**推荐：使用方案1（可编辑安装）**

```bash
# 1. 安装项目
pip install -e .

# 2. 现在可以直接运行任何文件
python app/core/agent.py
python app/test/test.py
python app/test/graph.py
```

**或者：使用方案2（路径设置工具）**

在需要导入的文件开头添加：
```python
from app.utils.path_setup import setup_path
```

