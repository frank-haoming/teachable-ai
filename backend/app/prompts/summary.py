from __future__ import annotations


def build_summary_prompt(messages: list[dict]) -> str:
    transcript = "\n".join(f'{item["role"]}: {item["content"]}' for item in messages)
    return f"""请把下面这段教学对话压缩成一段简洁摘要，保留：
1. 学生新教了哪些知识
2. AI 有哪些困惑或误解
3. 后续适合继续追问的点

对话：
{transcript}
"""
