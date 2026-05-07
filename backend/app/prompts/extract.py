from __future__ import annotations


def build_extract_prompt(student_message: str, learning_scope: dict | None = None) -> str:
    topic_labels = (learning_scope or {}).get("covered_topic_labels") or (learning_scope or {}).get("covered_topics") or [
        "主语从句",
        "宾语从句",
        "表语从句",
        "同位语从句",
    ]
    focus_labels = (learning_scope or {}).get("knowledge_focuses") or [
        "定义",
        "基本结构",
        "常见引导词",
        "语法功能",
        "例子",
    ]
    topic_text = " / ".join(topic_labels)
    focus_text = " / ".join(focus_labels)
    sample_topic = topic_labels[0]
    sample_focus = focus_labels[0]
    return f"""你是一个知识提取助手。请分析以下教学消息，提取其中应该进入学习伙伴知识库的知识点。

教学消息：
{student_message}

提取规则：
1. 每条知识用一个统一格式表示，包含 content（知识内容）和 tag（知识维度）。
2. content：提炼成简洁的规则陈述或完整的例句+解释，字数控制在 120 字以内。如果是例句，请将例句和解释合并为一段文字（如"I think he is honest. -- that 引导宾语从句，that 可省略"）。
3. tag：从以下知识维度中选择一个最匹配的：{focus_text}
4. topic：优先使用以下专题名称之一：{topic_text}
   - 如果内容更适合作为总规则或跨多个专题，可使用"通用"
   - 如果学生教的内容不属于以上任何专题，将 topic 设为"其他"。**不要**把不匹配的内容强行归入字面相似但含义不同的专题（例如"谓语从句"不能归入"表语从句"）
   - 如果内容只是闲聊、问候、与学习完全无关的对话，返回 has_knowledge: false，items 为空数组
5. 如果消息里同时包含规则和例句，可以分别提取为不同 tag 的多条 item。
6. touched_topics：无论是否提取到知识点，都请判断这条消息涉及了哪些专题（从上面的专题名称中选择），返回一个数组。如果消息和所有专题都无关，返回空数组。
7. touched_focuses：判断这条消息涉及了哪些知识维度（从上面的维度中选择），返回一个数组。只有消息真正讨论了该维度的实质内容时才算，闲聊或无关内容不算。如果都无关，返回空数组。

只返回 JSON，格式如下：
{{{{
  "has_knowledge": true,
  "touched_topics": ["{sample_topic}"],
  "touched_focuses": ["{sample_focus}"],
  "items": [
    {{{{
      "topic": "{sample_topic}",
      "tag": "定义",
      "content": "宾语从句是一个句子在复合句中充当宾语的成分"
    }}}},
    {{{{
      "topic": "{sample_topic}",
      "tag": "例子",
      "content": "I think he is honest. -- that 引导的宾语从句，that 已省略"
    }}}}
  ]
}}}}"""
