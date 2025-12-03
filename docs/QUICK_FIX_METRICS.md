# 快速修复：Metrics API 错误

## 问题

```
error: Metrics API not available
```

## 原因

Kubernetes 集群没有安装 **Metrics Server**，导致 `kubectl top` 命令无法工作。

## 快速解决（2 步）

### 步骤1：检查 Metrics Server

```bash
kubectl get deployment metrics-server -n kube-system
```

### 步骤2：安装 Metrics Server

```bash
# 一键安装
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 等待就绪（约30秒）
kubectl wait --for=condition=available --timeout=300s deployment/metrics-server -n kube-system

# 验证
kubectl top nodes
```

## 如果无法安装 Metrics Server

Agent 已经配置为：
1. ✅ 在 System Prompt 中提示使用替代方法
2. ✅ 捕获错误并提供友好提示
3. ✅ 继续使用其他工具进行诊断

Agent 会自动使用 `kubectl describe` 或 `kubectl get` 等替代方法。

## 验证

安装后，再次运行：

```bash
python3 app/core/agent.py
```

应该可以正常使用 `kubectl top` 命令了。

