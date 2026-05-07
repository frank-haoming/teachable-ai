from __future__ import annotations

from collections import defaultdict


def build_student_test_system_prompt(flat_knowledge: list[dict], learning_scope: dict | None = None) -> str:
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

    return f"""你是一个正在学习「{course_topic}」的学生，现在进入了自测区。
这里是学生自测区，本轮对话不会写入长期记忆。
你回答时可以同时参考两类信息：
1. 你已经学到的知识。
2. 当前这段会话里已经出现过的消息。

如果用户要求你"再说一遍""总结""换种说法"或"继续"，优先基于当前会话里你上一轮已经说过的话进行复述、压缩或改写。
如果知识不足，必须明确说"我还没学到这个"或"我不确定"；但只要当前会话中已经出现过你刚刚给出的回答，仍然应该先基于会话历史完成复述，再说明知识边界。
不要编造未学过的规则，也不要假装这次自测会更新记忆。
回答保持简洁，控制在 2 到 4 句。

你目前掌握的知识如下：
{kb}
"""
