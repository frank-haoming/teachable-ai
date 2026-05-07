from __future__ import annotations


def build_knowledge_edit_prompt(student_message: str, flat_knowledge: list[dict]) -> str:
    lines = []
    for item in flat_knowledge:
        tag = item.get("tag") or ""
        label = item.get("content") or ""
        tag_hint = f" [{tag}]" if tag else ""
        lines.append(f'- {item["id"]}{tag_hint}: {label}')
    joined = "\n".join(lines) or "(暂无可编辑知识)"
    return f"""你是一个知识管理助手。学生指出 AI 的某条记忆需要修改或删除。

学生消息：{student_message}

当前知识列表：
{joined}

请返回 JSON：
{{{{
  "action": "delete|update|unclear",
  "target_id": "k_xxx",
  "new_content": "仅 update 时提供"
}}}}
"""
