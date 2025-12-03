import json
import uvicorn

from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
from pydantic import BaseModel, Field

from fastapi import HTTPException, FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.messages import BaseMessage


from app.core.agent import model_usage
from app.rag.document_loader import DocumentLoader
from app.rag.vector_store import get_vector_store_manager
from app.rag.rag_retriever import get_rag_retriever

def get_model():
    return model_usage


# ==================== RAG 系统初始化 ====================
def initialize_rag_system():
    """初始化 RAG 系统：加载文档并构建向量存储"""
    print("\n" + "="*60)
    print("🚀 初始化 RAG 知识库...")
    print("="*60 + "\n")
    
    try:
        # 1. 加载文档
        loader = DocumentLoader()
        documents = loader.load_all_documents()
        
        if not documents:
            print("⚠️  未找到任何文档，RAG 功能将不可用")
            return False
        
        # 2. 初始化向量存储
        vector_store_manager = get_vector_store_manager()
        vector_store_manager.initialize(documents)
        
        print("="*60)
        print("✅ RAG 知识库初始化完成！")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ RAG 系统初始化失败: {error_msg}")
        
        # 如果是网络连接问题，给出友好提示
        if "Connection" in error_msg or "ConnectionResetError" in error_msg or "Connection aborted" in error_msg:
            print("\n💡 提示：")
            print("   这可能是网络连接问题导致的。")
            print("   解决方案：")
            print("   1. 检查网络连接")
            print("   2. 稍后重试（系统会自动重试）")
            print("   3. 或者使用本地 embedding 模型")
            print("\n   系统将继续运行，但 RAG 功能将不可用。")
        else:
            import traceback
            traceback.print_exc()
        
        return False


# 在模块加载时初始化 RAG 系统
_rag_initialized = initialize_rag_system()


class ContentBlock(BaseModel):
    type: str = Field(description="内容类型: text, image, audio")
    content: str = Field(description="内容数据")


class MessageRequest(BaseModel):
    content_blocks: List[ContentBlock] = Field(default=[], description="内容块")
    history: List[Dict[str, Any]] = Field(default=[], description="对话历史")


class MessageResponse(BaseModel):
    content: str
    timestamp: str
    role: str


def create_multimodal_message(request: MessageRequest) -> HumanMessage:
    """创建多模态消息"""
    message_content = []

    # 处理内容块
    for i, block in enumerate(request.content_blocks):
        if block.type == "text":
            message_content.append({
                "type": "text",
                "text": block.content
            })

    return HumanMessage(content=message_content[0]["text"])

def convert_history_to_messages(history: List[Dict[str, Any]], rag_context: str = "") -> List[BaseMessage]:
    """
    将历史记录转换为 LangChain 消息格式，支持多模态内容
    
    Args:
        history: 对话历史
        rag_context: RAG 检索到的上下文（可选）
    """
    messages = []

    # 构建系统消息（包含 RAG 上下文）
    system_prompt = """你是一个专业的多模态 RAG 助手，具备与用户对话的能力，请以专业、准确、友好的方式回答用户所提问题。"""
    
    if rag_context:
        system_prompt += f"""

以下是来自知识库的相关信息，请基于这些信息回答用户的问题。如果知识库中的信息不足以回答问题，请基于你的知识进行回答，但要明确说明信息来源。

【知识库信息】
{rag_context}
    """

    messages.append(SystemMessage(content=system_prompt))

    # 转换历史消息
    for i, msg in enumerate(history):
        content = msg.get("content", "")
        content_blocks = msg.get("content_blocks", [])
        message_content = []
        if msg["role"] == "user":
            for block in content_blocks:
                if block.get("type") == "text":
                    message_content.append({
                        "type": "text",
                        "text": block.get("content", "")
                    })
            messages.append(HumanMessage(content=message_content))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=content))

    return messages







async def generate_streaming_response(
        messages: List[BaseMessage],
        user_query: str = ""
) -> AsyncGenerator[str, None]:
    """
    生成流式响应（集成 RAG）
    
    Args:
        messages: 消息列表
        user_query: 用户查询（用于 RAG 检索）
    """
    try:
        model = get_model()
        # 创建流式响应
        full_response = ""

        chunk_count = 0
        async for chunk in model.astream(messages):
            chunk_count += 1
            if hasattr(chunk, 'content') and chunk.content:
                content = chunk.content
                full_response += content

                # 直接发送每个chunk的内容，避免重复
                data = {
                    "type": "content_delta",
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        # 发送完成信号
        final_data = {
            "type": "message_complete",
            "full_content": full_response,
            "timestamp": datetime.now().isoformat(),
        }
        yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
    except Exception as e:
        error_data = {
            "type": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"






# 创建 FastAPI 应用
app = FastAPI(
    title="多模态 RAG 工作台 API",
    description="基于 LangChain 1.0 的智能对话 API",
    version="1.0.0"
)

# 配置跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat/stream")
async def chat_stream(request: MessageRequest):
    """流式聊天接口（支持多模态 + RAG）"""
    try:
        # 获取用户查询文本
        user_query = ""
        if request.content_blocks:
            for block in request.content_blocks:
                if block.type == "text":
                    user_query = block.content
                    break
        
        # RAG 检索（如果已初始化）
        rag_context = ""
        if _rag_initialized and user_query:
            try:
                retriever = get_rag_retriever(k=4)
                relevant_docs = await retriever.aretrieve(user_query)
                if relevant_docs:
                    rag_context = retriever.format_context(relevant_docs)
            except Exception as e:
                print(f"⚠️  RAG 检索失败: {e}")
        
        # 转换消息历史（包含 RAG 上下文）
        messages = convert_history_to_messages(request.history, rag_context=rag_context)

        # 添加当前用户消息（支持多模态）
        current_message = create_multimodal_message(request)
        messages.append(current_message)

        # 返回流式响应
        return StreamingResponse(
            generate_streaming_response(messages, user_query=user_query),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@app.post("/api/chat")
async def chat_sync(request: MessageRequest):
    """同步聊天接口（支持多模态 + RAG）"""
    try:
        # 获取用户查询文本
        user_query = ""
        if request.content_blocks:
            for block in request.content_blocks:
                if block.type == "text":
                    user_query = block.content
                    break
        
        # RAG 检索（如果已初始化）
        rag_context = ""
        if _rag_initialized and user_query:
            try:
                retriever = get_rag_retriever(k=4)
                relevant_docs = await retriever.aretrieve(user_query)
                if relevant_docs:
                    rag_context = retriever.format_context(relevant_docs)
            except Exception as e:
                print(f"⚠️  RAG 检索失败: {e}")
        
        # 转换消息历史（包含 RAG 上下文）
        messages = convert_history_to_messages(request.history, rag_context=rag_context)

        # 添加当前用户消息（支持多模态）
        current_message = create_multimodal_message(request)
        messages.append(current_message)

        # 获取模型响应
        model = get_model()
        response = await model.ainvoke(messages)

        return MessageResponse(
            content=response.content,
            role="assistant",
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="localhost",
        port=8000
    )