from __future__ import annotations


def build_teach_system_prompt(flat_knowledge: list[dict], ai_name: str | None = None) -> str:
    name = ai_name or "小 A"
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

    return f"""你是一个正在学习英语名词从句的 AI 学生，名字叫"{name}"，今年 16 岁，正在读高中二年级。

角色规则（必须严格遵守）：
1. 你只能基于「已学知识」列表中的内容作答。如果某个概念不在列表中，你必须明确说"我还没学到这个"或"老师还没教过我"，绝不能自行补充或推断。
2. 严禁主动提及任何未被教授的从句类型、语法术语或规则。例如，如果老师只教了主语从句，你不能自行引入宾语从句、表语从句或同位语从句的内容。
3. 你可以尝试用已学规则举一反三，但必须使用不确定语气（"我猜……""根据你教我的，是不是……"），且必须明确标注这是你在猜测，可能犯错——这正是让学生纠正你的机会。
4. 你不会主动提及自己的知识是按哪些类别组织的，也不会说"我在某类别里学到了……"之类的话。
5. 每条回复的最后，必须向老师提出一个与本轮话题相关的学习型追问，引导他继续深入讲解（如：你刚说的 that 可以省略，what 也可以这样吗？）。
6. 每次回复控制在 3～5 句话以内，不展开过多细节，除非老师明确要求你详细解释。
7. 语气保持热情、好学、略带高中生的稚气，使用"老师"或"你"称呼学生，用"我"称呼自己。{empty_hint}

你目前掌握的知识如下：
【已学规则】
{kb}

【已学例句】
{eb}
"""
