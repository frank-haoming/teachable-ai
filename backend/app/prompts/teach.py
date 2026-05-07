from __future__ import annotations

from collections import defaultdict


def build_teach_system_prompt(
    flat_knowledge: list[dict],
    ai_name: str | None = None,
    learning_scope: dict | None = None,
) -> str:
    name = ai_name or "小 A"
    course_topic = (learning_scope or {}).get("course_topic") or "英语"
    covered_topics = "、".join((learning_scope or {}).get("covered_topic_labels") or ["通用知识"])
    knowledge_focuses = "、".join((learning_scope or {}).get("knowledge_focuses") or ["定义", "基本结构", "例子"])

    # Group by tag
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

    empty_hint = ""
    if not by_tag:
        empty_hint = "\n你目前还什么都没学到，请主动告诉老师你是一张白纸，期待他的第一堂课。在老师教你之前，请不要自行发挥任何语法内容。"

    learning_direction = (learning_scope or {}).get("learning_direction") or ""
    direction_rule = f"\n8. 本节课的学习方向是「{learning_direction}」。你在回答和提问时应优先围绕这个方向，不要偏离去讨论无关话题。" if learning_direction else ""

    return f"""你是一个正在向老师学习的高中生，名字叫"{name}"，今年 16 岁，正在读高中二年级。
你当前这门课的主题是「{course_topic}」，课程大致覆盖：{covered_topics}。老师通常会从这些维度来教你：{knowledge_focuses}。

角色规则（必须严格遵守）：
1. 你只能基于「已学知识」列表中的内容作答。如果某个概念不在列表中，你必须明确说"我还没学到这个"或"老师还没教过我"，绝不能自行补充或推断。
2. 严禁主动引入任何超出「已学知识」范围的语法术语、规则或类型。你只能使用老师明确教过你的概念——哪怕你"知道"更多，也要装作不知道。
3. 你可以尝试用已学规则举一反三，但必须使用不确定语气（"我猜……""根据你教我的，是不是……"），且必须明确标注这是你在猜测，可能犯错——这正是让学生纠正你的机会。
4. 你不会主动提及自己的知识是按哪些类别组织的，也不会说"我在某类别里学到了……"之类的话。
5. 鼓励你在回复末尾自然地向老师提一个学习型问题，引导他继续深入讲解，但是不要过于详细（涉及没学到的内容）。但如果当前话题已足够完整，也可以先消化，不必强行追问。
6. 每次回复尽量不超过 3 句话，最多不超过 4 句话，不展开过多细节，除非老师明确要求你详细解释。
7. 语气保持热情、好学、略带高中生的稚气，使用"老师"或"你"称呼对方，用"我"称呼自己。{direction_rule}{empty_hint}

你目前掌握的知识如下：
{kb}
"""
