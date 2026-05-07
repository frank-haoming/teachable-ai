from __future__ import annotations

from collections import defaultdict


def build_test_prompt(
    flat_knowledge: list[dict],
    question_text: str,
    options: dict[str, str],
    learning_scope: dict | None = None,
) -> str:
    course_topic = (learning_scope or {}).get("course_topic") or "英语名词从句"

    by_tag: dict[str, list[str]] = defaultdict(list)
    for item in flat_knowledge:
        tag = item.get("tag") or "其他"
        content = item.get("content") or ""
        if content:
            by_tag[tag].append(f"- {content}")

    if by_tag:
        sections = []
        for tag, lines in by_tag.items():
            sections.append(f"【{tag}】\n" + "\n".join(lines))
        kb = "\n\n".join(sections)
    else:
        kb = "（暂无）"

    return f"""你是一个正在参加测验的学生，当前课程主题是「{course_topic}」。你只能基于自己已学到的知识回答，不能使用任何外部知识。

已学知识：
{kb}

考试题目：{question_text}
A. {options["A"]}
B. {options["B"]}
C. {options["C"]}
D. {options["D"]}

请先分析题干的句子结构，识别题目，再对照已学知识选择答案。
如果没有学过相关知识，选最接近的选项并在 reasoning 中注明"这是基于有限知识的猜测"。

只返回 JSON：
{{{{
  "answer": "A|B|C|D",
  "reasoning": "逐步分析过程（2-4句）"
}}}}"""
