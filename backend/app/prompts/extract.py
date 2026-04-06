from __future__ import annotations


def build_extract_prompt(student_message: str) -> str:
    return f"""你是一个知识提取助手。请分析以下学生消息，提取其中关于英语名词从句的知识点和例句。

学生消息：
{student_message}

提取规则：
1. 知识点（type: "knowledge"）：提炼成简洁的规则陈述，不要照搬原文，字数控制在 80 字以内。
2. 例句（type: "example"）：保留原始例句，附上一句解释说明。
3. 分类（topic）：subject_clause / object_clause / predicative_clause / appositive_clause / general / other
   - general：跨类别的通用语法（如：名词从句可作主宾表同位语）
   - other：学习偏好、风格、非语法性内容
4. 如果消息是闲聊、问候、或没有可提取的语法内容，返回 has_knowledge: false，items 为空数组。

只返回 JSON，格式如下（两种类型各举一例）：
{{
  "has_knowledge": true,
  "items": [
    {{
      "type": "knowledge",
      "topic": "object_clause",
      "content": "宾语从句中引导词 that 在口语中可以省略"
    }},
    {{
      "type": "example",
      "topic": "object_clause",
      "sentence": "I think he is honest.",
      "explanation": "that 引导的宾语从句，that 已省略"
    }}
  ]
}}"""
