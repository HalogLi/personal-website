"""测试混元大模型调用 - 使用 anthropic SDK"""
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("HUNYUAN_INTERNAL_API_KEY", "")
BASE_URL = os.environ.get("HUNYUAN_INTERNAL_BASE_URL", "http://api.taiji.woa.com/openapi")

if not API_KEY:
    print("请在 .env 文件中设置 HUNYUAN_INTERNAL_API_KEY")
    exit(1)

client = anthropic.Anthropic(
    auth_token=API_KEY,
    base_url=BASE_URL,
)

print("=== 测试1: 流式调用 ===")
try:
    with client.beta.messages.stream(
        model="hunyuan-2.0-thinking-20251109",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "你好，请用一句话介绍一下你自己"}
        ]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n\n--- 流式调用成功 ---")
except Exception as e:
    print(f"\n流式调用失败: {type(e).__name__}: {e}")

print("\n=== 测试2: 非流式调用 ===")
try:
    response = client.messages.create(
        model="hunyuan-2.0-thinking-20251109",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "你好，请用一句话介绍一下你自己"}
        ]
    )
    for block in response.content:
        if block.type == "text":
            print(block.text)
    print("\n--- 非流式调用成功 ---")
except Exception as e:
    print(f"非流式调用失败: {type(e).__name__}: {e}")
