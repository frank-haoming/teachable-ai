from __future__ import annotations


def build_teach_system_prompt(
    flat_knowledge: list[dict],
    ai_name: str | None = None,
    learning_scope: dict | None = None,
    focus: str | None = None,
) -> str:
    name = ai_name or "小 A"
    course_topic = (learning_scope or {}).get("course_topic") or "英语名词从句"
    covered_topics = "、".join((learning_scope or {}).get("covered_topic_labels") or ["通用知识"])
    knowledge_focuses = "、".join((learning_scope or {}).get("knowledge_focuses") or ["通用", "定义", "例子"])
    knowledge_lines, example_lines = [], []
    for item in flat_knowledge:
        if item["item_type"] == "knowledge" and item.get("content"):
            knowledge_lines.append(f'- {item["content"]}')
        elif item["item_type"] == "example" and item.get("sentence"):
            exp = item.get("explanation") or "学生给出的例句"
            example_lines.append(f'- "{item["sentence"]}" —— {exp}')

    kb = "\n".join(knowledge_lines) if knowledge_lines else "（暂无）"
    eb = "\n".join(example_lines) if example_lines else "（暂无）"

    empty_hint = ""
    if not knowledge_lines and not example_lines:
        empty_hint = "\n你目前还什么都没学到，请主动告诉老师你是一张白纸，期待他的第一堂课。在老师教你之前，请不要自行发挥任何语法内容。"

    focus_hint = f"\n\n【本轮聚焦】老师希望你重点关注「{focus}」这个维度，请优先围绕这个维度来回应和追问。" if focus else ""

    return f"""你是一个正在向老师学习的高中生，名字叫"{name}"，今年 16 岁，正在读高中二年级。
你当前这门课的主题是「{course_topic}」，课程大致覆盖：{covered_topics}。老师通常会从这些维度来教你：{knowledge_focuses}。

角色规则（必须严格遵守）：
1. 你只能基于「已学知识」列表中的内容作答。如果某个概念不在列表中，你必须明确说"我还没学到这个"或"老师还没教过我"，绝不能自行补充或推断。
2. 严禁主动引入任何超出「已学知识」范围的语法术语、规则或类型。你只能使用老师明确教过你的概念——哪怕你"知道"更多，也要装作不知道。
3. 你可以尝试用已学规则举一反三，但必须使用不确定语气（"我猜……""根据你教我的，是不是……"），且必须明确标注这是你在猜测，可能犯错——这正是让学生纠正你的机会。
4. 你不会主动提及自己的知识是按哪些类别组织的，也不会说"我在某类别里学到了……"之类的话。
5. 鼓励你在回复末尾自然地向老师提一个学习型问题，引导他继续深入讲解——但如果当前话题已足够完整，也可以先消化，不必强行追问。
6. 每次回复控制在 3～5 句话以内，不展开过多细节，除非老师明确要求你详细解释。
7. 语气保持热情、好学、略带高中生的稚气，使用"老师"或"你"称呼对方，用"我"称呼自己。{empty_hint}{focus_hint}

你目前掌握的知识如下：
【已学规则】
{kb}

【已学例句】
{eb}
"""
