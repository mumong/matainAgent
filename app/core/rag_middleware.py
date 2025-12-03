"""
RAG 中间件
使用 AgentMiddleware 在 Agent 执行过程中智能集成 RAG 知识库
在 Agent 准备输出运维建议时，自动从知识库检索相关信息
"""
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from langgraph.runtime import Runtime

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState
from langchain_core.messages import AIMessage, HumanMessage
from app.core.rag_integration import get_rag_context_async, is_rag_initialized


class RAGMiddleware(AgentMiddleware):
    """
    RAG 中间件
    
    工作流程：
    1. Agent 先正常分析问题（使用工具、调用模型）
    2. 在模型生成回答后，检查是否包含"建议行动方案"等关键词
    3. 如果包含，从 RAG 知识库检索相关的运维手册和最佳实践
    4. 将检索到的信息注入到上下文中，让 Agent 重新生成或增强回答
    """
    
    def __init__(self, rag_k: int = 4, enable_auto_rag: bool = True):
        """
        初始化 RAG 中间件
        
        Args:
            rag_k: 检索的文档数量
            enable_auto_rag: 是否自动启用 RAG（如果为 False，需要手动触发）
        """
        super().__init__()
        self.rag_k = rag_k
        self.enable_auto_rag = enable_auto_rag
        self._rag_trigger_keywords = [
            "建议行动方案",
            "建议",
            "操作步骤",
            "最佳实践",
            "标准流程",
            "运维手册",
            "解决方案",
            "处理方案"
        ]
    
    def _should_trigger_rag(self, messages: list) -> bool:
        """
        判断是否应该触发 RAG 检索
        
        策略：
        1. 检查最后一条 AI 消息是否包含触发关键词
        2. 或者检查 Agent 是否已经完成了工具调用（准备输出最终建议）
        
        Args:
            messages: 消息列表
            
        Returns:
            True 如果需要触发 RAG，False 否则
        """
        if not self.enable_auto_rag or not is_rag_initialized():
            return False
        
        # 检查最后一条 AI 消息
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                # 检查是否包含触发关键词
                if any(keyword in content for keyword in self._rag_trigger_keywords):
                    return True
                # 检查是否已经完成了工具调用（准备输出最终答案）
                if not msg.tool_calls or len(msg.tool_calls) == 0:
                    # 如果 AI 已经生成回答且没有工具调用，可能需要 RAG
                    if len(content) > 100:  # 回答有一定长度
                        return True
                break
        
        return False
    
    def _extract_user_query(self, messages: list) -> Optional[str]:
        """
        从消息列表中提取用户原始查询
        
        Args:
            messages: 消息列表
            
        Returns:
            用户查询文本，如果找不到则返回 None
        """
        for msg in messages:
            if isinstance(msg, HumanMessage):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                # 移除可能已添加的 RAG 上下文
                if "【知识库参考信息】" in content:
                    # 提取原始问题（在 RAG 上下文之前）
                    content = content.split("【知识库参考信息】")[0].strip()
                return content
        return None
    
    async def aafter_model(
        self, state: AgentState, runtime: "Runtime"
    ) -> dict[str, Any] | None:
        """
        在模型调用后执行
        
        检查 AI 的回答，如果包含"建议行动方案"等关键词，
        则从 RAG 知识库检索相关信息并注入到上下文中
        """
        messages = state.get("messages", [])
        
        # 判断是否需要触发 RAG
        if not self._should_trigger_rag(messages):
            return None
        
        # 提取 Agent 的分析结果（包含 A-B-C 过程的回答）
        # 优先使用 Agent 的分析结果进行匹配，这样更精准
        ai_message = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                ai_message = msg
                break
        
        if not ai_message:
            return None
        
        # 提取 AI 回答内容（包含建议行动方案）
        ai_content = ai_message.content if isinstance(ai_message.content, str) else str(ai_message.content)
        
        # 从 AI 回答中提取关键部分（建议行动方案部分）
        # 如果包含"建议行动方案"，提取该部分；否则使用整个回答
        query_for_rag = ai_content
        if "建议行动方案" in ai_content:
            # 提取"建议行动方案"部分
            parts = ai_content.split("建议行动方案")
            if len(parts) > 1:
                query_for_rag = "建议行动方案" + parts[1]
                # 只取前 500 字符，避免查询过长
                query_for_rag = query_for_rag[:500]
        else:
            # 如果没有明确的关键词，使用整个回答的前 300 字符
            query_for_rag = ai_content[:300]
        
        # 同时结合用户原始查询，提高匹配准确性
        user_query = self._extract_user_query(messages)
        if user_query:
            # 组合用户查询和 AI 分析结果
            combined_query = f"{user_query} {query_for_rag}"
        else:
            combined_query = query_for_rag
        
        # 从 RAG 知识库检索相关信息
        print("\n🔍 检测到需要输出运维建议，正在从知识库检索相关标准流程...")
        print(f"   检索关键词：{combined_query[:100]}...")
        rag_context = await get_rag_context_async(combined_query, k=self.rag_k)
        
        if not rag_context:
            print("ℹ️  知识库中暂无相关信息\n")
            return None
        
        print("✅ 已找到相关知识，将结合标准运维流程生成建议\n")
        
        # 构建增强提示
        enhancement_prompt = f"""
请参考以下运维知识库中的标准流程和最佳实践，完善你的"建议行动方案"部分：

{rag_context}

要求：
1. 确保你的建议与知识库中的标准流程一致
2. 如果知识库中有相关的标准操作步骤，请优先使用
3. 结合你之前分析的问题和知识库内容，给出更专业、更标准的运维建议
4. 如果知识库内容与你的分析有冲突，请说明原因并给出建议
"""
        
        # 将增强提示添加到消息列表
        # 注意：这里我们添加一个系统消息来指导模型
        enhanced_messages = messages + [
            HumanMessage(content=enhancement_prompt)
        ]
        
        return {"messages": enhanced_messages}
    
    async def abefore_model(
        self, state: AgentState, runtime: "Runtime"
    ) -> dict[str, Any] | None:
        """
        在模型调用前执行
        
        可选：在 Agent 开始分析时，如果检测到是运维相关问题，
        可以预先从 RAG 检索一些背景知识
        """
        # 这里可以实现预检索逻辑（可选）
        # 例如：如果用户问题明确是运维问题，可以预先检索相关知识
        return None

