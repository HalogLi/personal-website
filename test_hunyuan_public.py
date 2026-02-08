"""测试混元大模型调用 - 公网方式（使用 OpenAI SDK）"""
import os
from openai import OpenAI


API_KEY = "sk-P1IkRHaJUDHK3vt12LGHvKyr6u8NBJR8OqU4VRUocP3Anayu"
BASE_URL = "https://api.hunyuan.cloud.tencent.com/v1"
MODEL = "hunyuan-turbos-latest"

if not API_KEY:
    print("请设置环境变量 apikey1770550430490（混元公网 API Key）")
    print("  export apikey1770550430490='your-api-key-here'")
    exit(1)

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

# ============================================================
# 测试1: 基础非流式调用
# ============================================================
print("=" * 60)
print("测试1: 基础非流式调用")
print("=" * 60)
try:
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "你好，请用一句话介绍一下你自己"}
        ],
    )
    print(f"模型: {completion.model}")
    print(f"回复: {completion.choices[0].message.content}")
    print(f"Token 用量: prompt={completion.usage.prompt_tokens}, "
          f"completion={completion.usage.completion_tokens}, "
          f"total={completion.usage.total_tokens}")
    print("--- 非流式调用成功 ---\n")
except Exception as e:
    print(f"非流式调用失败: {type(e).__name__}: {e}\n")

# ============================================================
# 测试2: 流式调用
# ============================================================
print("=" * 60)
print("测试2: 流式调用")
print("=" * 60)
try:
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "请用三句话介绍腾讯公司"}
        ],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n--- 流式调用成功 ---\n")
except Exception as e:
    print(f"流式调用失败: {type(e).__name__}: {e}\n")

# ============================================================
# 测试3: 带 system prompt 的多轮对话
# ============================================================
print("=" * 60)
print("测试3: 带 system prompt 的多轮对话")
print("=" * 60)
try:
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是一个专业的算法工程师助手，回答简洁专业。"},
            {"role": "user", "content": "什么是图神经网络？"},
            {"role": "assistant", "content": "图神经网络(GNN)是一类处理图结构数据的深度学习模型，通过消息传递机制聚合邻居节点信息来学习节点和图的表示。"},
            {"role": "user", "content": "它在反欺诈场景有哪些应用？"}
        ],
    )
    print(f"回复: {completion.choices[0].message.content}")
    print("--- 多轮对话成功 ---\n")
except Exception as e:
    print(f"多轮对话失败: {type(e).__name__}: {e}\n")

# ============================================================
# 测试4: 带 enable_enhancement 参数调用
# ============================================================
print("=" * 60)
print("测试4: 带 enable_enhancement 参数")
print("=" * 60)
try:
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "今天天气怎么样？"}
        ],
        extra_body={
            "enable_enhancement": True,
        },
    )
    print(f"回复: {completion.choices[0].message.content}")
    print("--- enable_enhancement 调用成功 ---\n")
except Exception as e:
    print(f"enable_enhancement 调用失败: {type(e).__name__}: {e}\n")

# ============================================================
# 测试5: 温度和 top_p 参数控制
# ============================================================
print("=" * 60)
print("测试5: 温度参数控制 (temperature=0.1 低随机性)")
print("=" * 60)
try:
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "1+1等于几？"}
        ],
        temperature=0.1,
        top_p=0.9,
        max_tokens=100,
    )
    print(f"回复: {completion.choices[0].message.content}")
    print("--- 温度参数调用成功 ---\n")
except Exception as e:
    print(f"温度参数调用失败: {type(e).__name__}: {e}\n")

print("=" * 60)
print("所有测试完成！")
print("=" * 60)
