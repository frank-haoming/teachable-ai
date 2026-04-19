from __future__ import annotations


def build_test_prompt(
    flat_knowledge: list[dict],
    question_text: str,
    options: dict[str, str],
    learning_scope: dict | None = None,
) -> str:
    course_topic = (learning_scope or {}).get("course_topic") or "英语名词从句"
    rules, examples = [], []
    for item in flat_knowledge:
        if item["item_type"] == "knowledge" and item.get("content"):
            rules.append(item["content"])
        elif item["item_type"] == "example" and item.get("sentence"):
            exp = item.get("explanation") or ""
            examples.append(f'{item["sentence"]}（{exp}）' if exp else item["sentence"])
    rule_text = "\n".join(f"- {r}" for r in rules) if rules else "（暂无规则）"
    ex_text = "\n".join(f"- {e}" for e in examples) if examples else "（暂无例句）"
    return f"""你是一个正在参加测验的学生，当前课程主题是「{course_topic}」。你只能基于自己已学到的知识回答，不能使用任何外部知识。

已学规则：
{rule_text}

已学例句：
{ex_text}

考试题目：{question_text}
A. {options["A"]}
B. {options["B"]}
C. {options["C"]}
D. {options["D"]}

请先分析题干的句子结构，识别从句类型，再对照已学规则和例句选择答案。
如果没有学过相关知识，选最接近的选项并在 reasoning 中注明"这是基于有限知识的猜测"。

只返回 JSON：
{{
  "answer": "A|B|C|D",
  "reasoning": "逐步分析过程（2-4句）"
}}"""
