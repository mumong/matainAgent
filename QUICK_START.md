# 快速开始 - 解决模块导入问题

## 🚀 推荐方案：可编辑安装（一次配置，永久使用）

### 步骤1：安装项目

```bash
cd /root/huhu/agent/matain_agent
pip install -e .
```

### 步骤2：现在可以直接运行任何文件

```bash
# 直接运行，无需任何路径设置
python app/core/agent.py
python app/test/test.py
python app/test/graph.py
```

### 步骤3：在任何文件中直接导入

```python
# 不需要任何路径设置代码，直接导入即可
from config.config_loader import get_config
from app.core.agent import model_usage
from app.tools.base import tools_usage
```

---

## 🔧 备选方案：路径设置工具

如果不想安装包，可以在文件开头添加：

```python
from app.utils.path_setup import setup_path
# setup_path() 会自动执行，这行可以省略

# 然后正常导入
from config.config_loader import get_config
```

---

## 📝 修改现有文件

如果文件已经有路径设置代码，可以删除：

**之前：**
```python
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
```

**之后（使用可编辑安装）：**
```python
# 直接导入，无需路径设置
from config.config_loader import get_config
```

**或者（使用路径工具）：**
```python
from app.utils.path_setup import setup_path
from config.config_loader import get_config
```

---

## ✅ 验证安装

运行以下命令验证：

```bash
python -c "from config.config_loader import get_config; print('✅ 导入成功！')"
```

如果看到 "✅ 导入成功！"，说明安装成功。

