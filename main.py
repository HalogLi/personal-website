"""李海龙个人助手网站 - FastAPI 后端（使用 anthropic SDK）"""
import os
import json
import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="李海龙 Personal Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 混元大模型配置（从环境变量读取）
HUNYUAN_API_KEY = os.environ.get("HUNYUAN_INTERNAL_API_KEY", "")
HUNYUAN_BASE_URL = os.environ.get("HUNYUAN_INTERNAL_BASE_URL", "http://api.taiji.woa.com/openapi")
HUNYUAN_MODEL = "hunyuan-2.0-thinking-20251109"

# 创建 anthropic 异步客户端（全局复用）
async_client = anthropic.AsyncAnthropic(
    auth_token=HUNYUAN_API_KEY,
    base_url=HUNYUAN_BASE_URL,
)

# 同步客户端（用于线程池调用流式接口）
sync_client = anthropic.Anthropic(
    auth_token=HUNYUAN_API_KEY,
    base_url=HUNYUAN_BASE_URL,
)

RESUME_CONTEXT = """李海龙，算法工程师。腾讯科技风控算法方向，负责社交反欺诈与支付安全。擅长图算法、时序建模、多模态融合与 Graph+LLM 结合。
教育：西安电子科技大学硕士（电子科学与技术，2018-2021），本科（智能科学与技术，2014-2018）。
核心项目：刷单反欺诈（构建图召回+时序精排+梯度打击三层架构，受害者下降85%）；支付安全（多模态识别欺诈收款号，召回85%，干预90%，资损下降65%）；Graph+LLM 欺诈识别（Qwen3-1.7B 微调准确率90.3%）；电竞视频关键帧提取与聚类（YOLOv3 mAP 93%，推荐准确率92%）。
技能：Python/C++/SQL/Lua，Flink/Spark/Hive/HDFS/Neo4j，PyTorch/TensorFlow/Caffe，CNN/RNN/GNN/Transformer，RAG。
实习：杭州海康威视研究院，智能算法工程师，EfficientNet 人/车/动物三分类，准确率91%→96%。
荣誉：互联网+银奖、美赛H奖、中兴捧月全国优胜、2项专利。"""

SYSTEM_PROMPT = "你是李海龙的个人AI助手。基于他的简历信息回答问题，回答要简洁专业，使用中文回复。如果问题与简历无关，可以正常对话但适当引导回简历相关话题。"


class ChatRequest(BaseModel):
    question: str


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health():
    """健康检查 - 使用 anthropic AsyncAnthropic 测试连通性"""
    try:
        resp = await async_client.messages.create(
            model=HUNYUAN_MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}],
        )
        return JSONResponse({"status": "ok", "model": HUNYUAN_MODEL, "provider": "混元大模型"})
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse({"status": "ok", "model": HUNYUAN_MODEL, "provider": "混元大模型", "api_note": str(e)})


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """流式对话接口 - 使用 anthropic SDK 同步流式 + 线程池"""

    async def generate():
        try:
            logger.info(f"Calling Hunyuan API: model={HUNYUAN_MODEL}, question={req.question[:50]}")

            loop = asyncio.get_event_loop()
            queue = asyncio.Queue()

            def stream_in_thread():
                """在线程中运行同步流式调用，将结果放入队列"""
                try:
                    with sync_client.beta.messages.stream(
                        model=HUNYUAN_MODEL,
                        max_tokens=2048,
                        messages=[
                            {
                                "role": "user",
                                "content": f"{SYSTEM_PROMPT}\n\n简历信息：\n{RESUME_CONTEXT}\n\n用户问题：{req.question}",
                            }
                        ],
                    ) as stream:
                        for text in stream.text_stream:
                            loop.call_soon_threadsafe(queue.put_nowait, ("text", text))
                    loop.call_soon_threadsafe(queue.put_nowait, ("done", None))
                except Exception as e:
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", str(e)))

            # 在线程池中启动流式调用
            asyncio.get_event_loop().run_in_executor(None, stream_in_thread)

            while True:
                event_type, data = await queue.get()
                if event_type == "text":
                    yield f"data: {json.dumps({'content': data}, ensure_ascii=False)}\n\n"
                elif event_type == "done":
                    yield "data: [DONE]\n\n"
                    return
                elif event_type == "error":
                    logger.error(f"Stream error: {data}")
                    yield f"data: {json.dumps({'error': f'调用失败: {data}'}, ensure_ascii=False)}\n\n"
                    return

        except Exception as e:
            logger.error(f"Chat error: {type(e).__name__}: {e}")
            yield f"data: {json.dumps({'error': f'调用失败: {type(e).__name__}: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/chat_sync")
async def chat_sync(req: ChatRequest):
    """非流式对话接口 - 使用 anthropic AsyncAnthropic"""
    try:
        logger.info(f"Sync call: question={req.question[:50]}")

        resp = await async_client.messages.create(
            model=HUNYUAN_MODEL,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": f"{SYSTEM_PROMPT}\n\n简历信息：\n{RESUME_CONTEXT}\n\n用户问题：{req.question}",
                }
            ],
        )

        text = "".join(block.text for block in resp.content if block.type == "text")
        return JSONResponse({"content": text, "model": resp.model})

    except Exception as e:
        logger.error(f"Sync chat error: {type(e).__name__}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
