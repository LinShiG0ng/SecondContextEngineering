"""
Web API路由
实现所有的HTTP API端点和WebSocket
"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import time
import json
from pathlib import Path

from context_engineering_demo.context_manager import ContextManager
from context_engineering_demo.llm_client import LLMClient
from context_engineering_demo.config_loader import load_config
from context_engineering_demo.utils import count_tokens, estimate_cost, calculate_similarity
from context_engineering_demo import config as default_config


# ===== FastAPI应用 =====
app = FastAPI(
    title="上下文工程演示系统",
    description="智能上下文管理和压缩演示平台",
    version="1.0.0"
)

# 启用CORS
if default_config.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 挂载静态文件
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ===== 全局状态 =====
class AppState:
    """应用状态管理"""
    def __init__(self):
        self.config = None
        self.context_manager = None
        self.llm_client = None
        self.initialized = False

    async def initialize(self):
        """初始化应用"""
        if self.initialized:
            return

        # 加载配置
        self.config = load_config()

        # 初始化LLM客户端（先初始化，用于智能压缩）
        llm_config = self.config.get('llm', {})
        if llm_config.get('api_key'):
            self.llm_client = LLMClient(llm_config)
            print(f"✨ LLM客户端已初始化: {llm_config.get('provider')} - {llm_config.get('model')}")
        else:
            print("⚠️  未配置LLM API，将使用规则匹配Fallback模式")

        # 初始化上下文管理器（传入llm_client以启用智能压缩）
        max_tokens = self.config.get('context', {}).get('max_tokens', 8000)
        self.context_manager = ContextManager(
            max_tokens=max_tokens,
            llm_client=self.llm_client  # 传入llm_client
        )

        self.initialized = True


state = AppState()


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    await state.initialize()


# ===== 数据模型 =====

class Message(BaseModel):
    """消息格式"""
    role: str
    content: str
    timestamp: Optional[float] = None
    tokens: Optional[int] = None


class ConversationImport(BaseModel):
    """导入的对话数据"""
    messages: List[Message]
    config: Optional[Dict] = None


class CompressionRequest(BaseModel):
    """压缩请求"""
    messages: List[Message]
    force: Optional[bool] = False


class ChatRequest(BaseModel):
    """对话请求"""
    message: str


class CompareRequest(BaseModel):
    """对比请求"""
    messages: List[Message]
    test_query: str


# ===== API端点 =====

@app.get("/", response_class=HTMLResponse)
async def index():
    """主页面"""
    template_path = Path(__file__).parent / "templates" / "index.html"

    if not template_path.exists():
        return """
        <html>
            <head><title>上下文工程演示系统</title></head>
            <body>
                <h1>🧠 上下文工程演示系统</h1>
                <p>⚠️ 前端页面尚未创建</p>
                <p>请访问 <a href="/docs">/docs</a> 查看API文档</p>
            </body>
        </html>
        """

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


@app.post("/api/import")
async def import_conversation(data: ConversationImport):
    """
    导入外部对话历史

    接收JSON格式的对话数据，分析并准备压缩
    """
    try:
        print(f"\n=== 导入API被调用 ===")
        print(f"收到消息数量: {len(data.messages)}")

        # 确保初始化
        await state.initialize()

        messages = [msg.dict() for msg in data.messages]
        print(f"转换后的消息: {messages[:2] if len(messages) > 2 else messages}")  # 显示前2条

        # 分析消息
        total_tokens = sum(count_tokens(m['content']) for m in messages)
        system_prompts = [m for m in messages if m['role'] == 'system']
        other_messages = [m for m in messages if m['role'] != 'system']

        print(f"分析结果:")
        print(f"  - 总消息数: {len(messages)}")
        print(f"  - System Prompt: {len(system_prompts)}条")
        print(f"  - User/Assistant: {len(other_messages)}条")
        print(f"  - 总Tokens: {total_tokens}")

        # 检查是否可以压缩
        can_compress = len(other_messages) >= 5

        response_data = {
            "status": "success",
            "message_count": len(messages),
            "system_prompt_count": len(system_prompts),
            "user_assistant_count": len(other_messages),
            "total_tokens": total_tokens,
            "can_compress": can_compress,
            "message": "导入成功" if can_compress else "消息数量不足（需要至少5条对话）"
        }

        print(f"返回响应: status={response_data['status']}, can_compress={can_compress}")
        print(f"=== 导入API完成 ===\n")

        return response_data

    except Exception as e:
        import traceback
        error_detail = f"导入失败: {str(e)}\n{traceback.format_exc()}"
        print(f"导入错误: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/api/compress")
async def compress_context(data: CompressionRequest):
    """
    执行上下文压缩

    核心功能：
    1. 识别并分离system prompt（不压缩）
    2. 对user和assistant消息执行AU2压缩
    3. 返回压缩后的完整上下文
    """
    try:
        print(f"\n=== 压缩API被调用 ===")
        print(f"收到消息数量: {len(data.messages)}")

        # 确保初始化
        await state.initialize()
        print(f"State已初始化: {state.initialized}")

        messages = [msg.dict() for msg in data.messages]
        print(f"转换后的消息: {len(messages)}条")

        if len(messages) < 2:
            raise HTTPException(status_code=400, detail="消息数量不足（至少需要2条）")

        # 执行压缩
        print("开始执行压缩...")
        start_time = time.time()
        compression_result = await state.context_manager.compressor.compress(messages)
        execution_time = time.time() - start_time
        print(f"压缩完成，耗时: {execution_time:.2f}秒")

        # 提取结果
        compressed_messages = compression_result['compressed_messages']
        statistics = compression_result['statistics']
        system_prompts = compression_result['system_prompts']

        print(f"压缩结果:")
        print(f"  - 原始消息: {len(messages)}条")
        print(f"  - 压缩后消息: {len(compressed_messages)}条")
        print(f"  - System Prompt: {len(system_prompts)}条")

        # 计算原始tokens
        original_messages = [m for m in messages if m['role'] != 'system']
        original_tokens = sum(count_tokens(m['content']) for m in original_messages)

        # 计算压缩后tokens（排除system prompts）
        compressed_content = [m for m in compressed_messages if m['role'] != 'system']
        compressed_tokens = sum(count_tokens(m.get('content', '')) for m in compressed_content)

        response_data = {
            "status": "success",
            "original": {
                "messages": messages,
                "tokens": original_tokens + sum(count_tokens(sp['content']) for sp in system_prompts),
                "message_count": len(messages)
            },
            "compressed": {
                "messages": compressed_messages,
                "tokens": compressed_tokens + sum(count_tokens(sp['content']) for sp in system_prompts),
                "message_count": len(compressed_messages)
            },
            "statistics": {
                "compression_ratio": 1 - (compressed_tokens / max(original_tokens, 1)),
                "tokens_saved": original_tokens - compressed_tokens,
                "system_prompts_preserved": len(system_prompts),
                "system_role_untouched": True,
                "execution_time": execution_time,
                "info_retention": statistics.get('info_retention', 0.95)
            }
        }

        print(f"返回响应: status={response_data['status']}")
        print(f"=== 压缩API完成 ===\n")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"压缩失败: {str(e)}\n{traceback.format_exc()}"
        print(f"压缩错误: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/api/export")
async def export_compressed(data: Dict):
    """
    导出压缩后的上下文

    以标准OpenAI/Anthropic格式导出，可直接用于API调用
    """
    try:
        messages = data.get('messages', [])

        if not messages:
            raise HTTPException(status_code=400, detail="没有消息可导出")

        # 计算元数据
        total_tokens = sum(count_tokens(m.get('content', '')) for m in messages)
        system_count = len([m for m in messages if m.get('role') == 'system'])

        # 构建导出格式
        export_data = {
            "messages": messages,
            "metadata": {
                "compressed": True,
                "system_prompts_preserved": system_count,
                "total_tokens": total_tokens,
                "compression_only_applied_to": ["user", "assistant"],
                "system_role_untouched": True,
                "format": "OpenAI/Anthropic compatible",
                "export_timestamp": time.time()
            }
        }

        return export_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    对话接口

    支持在Web界面直接与大模型对话，测试压缩效果
    """
    try:
        # 确保初始化
        await state.initialize()

        if not state.llm_client:
            raise HTTPException(status_code=400, detail="LLM客户端未配置")

        # 添加用户消息
        await state.context_manager.add_message('user', request.message)

        # 获取上下文
        context = await state.context_manager.get_context(request.message)

        # 调用LLM
        response = await state.llm_client.chat(context, stream=False)

        # 添加助手响应
        await state.context_manager.add_message('assistant', response)

        # 检查是否需要压缩
        usage_rate = state.context_manager.calculate_usage()
        should_compress = usage_rate >= default_config.AUTO_COMPACT_THRESHOLD

        # 如果需要，执行压缩
        compression_triggered = False
        compression_stats = None

        if should_compress:
            compression_result = await state.context_manager.compress()
            if compression_result['success']:
                compression_triggered = True
                compression_stats = compression_result['statistics']

        return {
            "status": "success",
            "response": response,
            "tokens": count_tokens(response),
            "usage_rate": usage_rate,
            "compression_triggered": compression_triggered,
            "compression_stats": compression_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")


@app.get("/api/stats")
async def get_statistics():
    """获取统计信息"""
    try:
        await state.initialize()

        stats = state.context_manager.get_statistics()

        # 添加LLM统计
        if state.llm_client:
            stats['api'] = state.llm_client.get_stats()

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@app.post("/api/compare")
async def compare_compression(request: CompareRequest):
    """
    对比压缩效果

    使用相同问题测试压缩前后的响应质量
    """
    try:
        await state.initialize()

        if not state.llm_client:
            raise HTTPException(status_code=400, detail="LLM客户端未配置")

        messages = [msg.dict() for msg in request.messages]
        test_query = request.test_query

        # 测试1: 使用原始上下文
        original_context = messages.copy()
        original_tokens = sum(count_tokens(m['content']) for m in original_context)

        start_time = time.time()
        try:
            response_original = await state.llm_client.chat(
                original_context + [{'role': 'user', 'content': test_query}],
                stream=False
            )
            time_original = time.time() - start_time
            output_tokens_original = count_tokens(response_original)
            cost_original = estimate_cost(original_tokens, state.llm_client.model, 'input') + \
                          estimate_cost(output_tokens_original, state.llm_client.model, 'output')
        except Exception as e:
            response_original = f"错误: {str(e)}"
            time_original = 0
            cost_original = 0

        # 测试2: 使用压缩上下文
        compression_result = await state.context_manager.compressor.compress(messages)
        compressed_context = compression_result['compressed_messages']
        compressed_tokens = sum(count_tokens(m.get('content', '')) for m in compressed_context)

        start_time = time.time()
        try:
            response_compressed = await state.llm_client.chat(
                compressed_context + [{'role': 'user', 'content': test_query}],
                stream=False
            )
            time_compressed = time.time() - start_time
            output_tokens_compressed = count_tokens(response_compressed)
            cost_compressed = estimate_cost(compressed_tokens, state.llm_client.model, 'input') + \
                            estimate_cost(output_tokens_compressed, state.llm_client.model, 'output')
        except Exception as e:
            response_compressed = f"错误: {str(e)}"
            time_compressed = 1
            cost_compressed = 0

        # 计算相似度
        similarity = calculate_similarity(response_original, response_compressed)

        # 计算改进指标
        token_reduction = (1 - compressed_tokens / original_tokens) * 100 if original_tokens > 0 else 0
        speed_increase = time_original / time_compressed if time_compressed > 0 else 0
        cost_reduction = (1 - cost_compressed / cost_original) * 100 if cost_original > 0 else 0

        return {
            "status": "success",
            "original": {
                "tokens": original_tokens,
                "response_time": time_original,
                "cost": cost_original,
                "response": response_original[:200] + "..." if len(response_original) > 200 else response_original
            },
            "compressed": {
                "tokens": compressed_tokens,
                "response_time": time_compressed,
                "cost": cost_compressed,
                "response": response_compressed[:200] + "..." if len(response_compressed) > 200 else response_compressed
            },
            "improvements": {
                "token_reduction": f"{token_reduction:.1f}%",
                "speed_increase": f"{speed_increase:.1f}x",
                "cost_reduction": f"{cost_reduction:.1f}%",
                "similarity_score": similarity
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比测试失败: {str(e)}")


@app.post("/api/reset")
async def reset_conversation():
    """重置对话"""
    try:
        await state.initialize()
        state.context_manager.reset()

        return {
            "status": "success",
            "message": "对话已重置"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")


# ===== WebSocket支持（可选）=====

@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """
    WebSocket实时对话

    支持流式响应和实时状态更新
    """
    await websocket.accept()

    try:
        await state.initialize()

        while True:
            # 接收消息
            data = await websocket.receive_json()
            message_type = data.get('type')

            if message_type == 'message':
                content = data.get('content')

                # 添加用户消息
                await state.context_manager.add_message('user', content)

                # 获取上下文
                context = await state.context_manager.get_context(content)

                # 调用LLM（流式）
                if state.llm_client:
                    response = await state.llm_client.chat(context, stream=False)

                    # 发送响应
                    await websocket.send_json({
                        'type': 'response',
                        'content': response,
                        'tokens': count_tokens(response)
                    })

                    # 添加助手响应
                    await state.context_manager.add_message('assistant', response)

                    # 检查压缩
                    usage_rate = state.context_manager.calculate_usage()
                    if usage_rate >= default_config.AUTO_COMPACT_THRESHOLD:
                        await websocket.send_json({
                            'type': 'compression',
                            'status': 'started'
                        })

                        compression_result = await state.context_manager.compress()

                        await websocket.send_json({
                            'type': 'compression',
                            'status': 'completed',
                            'stats': compression_result['statistics']
                        })
                else:
                    await websocket.send_json({
                        'type': 'error',
                        'message': 'LLM客户端未配置'
                    })

    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'message': str(e)
        })
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
