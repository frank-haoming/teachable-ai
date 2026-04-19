from __future__ import annotations


def build_extract_prompt(student_message: str, learning_scope: dict | None = None) -> str:
    topic_labels = (learning_scope or {}).get("covered_topic_labels") or (learning_scope or {}).get("covered_topics") or [
        "主语从句",
        "宾语从句",
        "表语从句",
        "同位语从句",
    ]
    topic_text = " / ".join(topic_labels)
    sample_topic = topic_labels[0]
    return f"""你是一个知识提取助手。请分析以下教学消息，提取其中应该进入学习伙伴知识库的知识点和例句。

教学消息：
{student_message}

提取规则：
1. 知识点（type: "knowledge"）：提炼成简洁的规则陈述，不要照搬原文，字数控制在 80 字以内。
2. 例句（type: "example"）：保留原始例句，附上一句解释说明。
3. 分类（topic）：优先使用以下专题名称之一：{topic_text}
   - 如果内容更适合作为总规则或跨多个专题，可使用“通用”
   - 如果内容只是学习偏好、闲聊、或无法归入知识库，返回 has_knowledge: false，items 为空数组
4. 如果消息里同时包含规则和例句，可以同时提取两种 item。

只返回 JSON，格式如下（两种类型各举一例）：
{{
  "has_knowledge": true,
  "items": [
    {{
      "type": "knowledge",
      "topic": "{sample_topic}",
      "content": "宾语从句中引导词 that 在口语中可以省略"
    }},
    {{
      "type": "example",
      "topic": "{sample_topic}",
      "sentence": "I think he is honest.",
      "explanation": "that 引导的宾语从句，that 已省略"
    }}
  ]
}}"""
