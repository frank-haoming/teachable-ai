from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import get_settings
from app.prompts.extract import build_extract_prompt
from app.prompts.knowledge_edit import build_knowledge_edit_prompt
from app.prompts.self_test import build_student_test_system_prompt
from app.prompts.summary import build_summary_prompt
from app.prompts.teach import build_teach_system_prompt
from app.prompts.test_answer import build_test_prompt


TOPIC_KEYWORDS = {
    "subject_clause": ["主语从句", "subject clause", "subject"],
    "object_clause": ["宾语从句", "object clause", "宾语"],
    "predicative_clause": ["表语从句", "predicative clause", "表语"],
    "appositive_clause": ["同位语从句", "appositive clause", "同位语"],
}

GRAMMAR_HINTS = [
    "从句",
    "clause",
    "that",
    "whether",
    "what",
    "which",
    "who",
    "if",
    "grammar",
    "语法",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def _token_overlap(left: str, right: str) -> int:
    left_tokens = {token for token in re.findall(r"[a-zA-Z\u4e00-\u9fff]+", left.lower()) if len(token) > 1}
    right_tokens = {token for token in re.findall(r"[a-zA-Z\u4e00-\u9fff]+", right.lower()) if len(token) > 1}
    return len(left_tokens & right_tokens)


@dataclass(slots=True)
class AIService:
    settings: Any

    @classmethod
    def build(cls) -> "AIService":
        return cls(settings=get_settings())

    def refresh_settings(self) -> None:
        self.settings = get_settings()

    async def extract_knowledge(self, student_message: str) -> dict[str, Any]:
        self.refresh_settings()
        if self._use_live_model:
            payload = await self._json_completion(
                system_prompt="你是一个严格的知识提取助手，只返回 JSON。",
                user_prompt=build_extract_prompt(student_message),
            )
            if payload:
                return payload
        return self._mock_extract_knowledge(student_message)

    async def decide_merge(self, item: dict[str, Any], existing_items: list[dict[str, Any]]) -> dict[str, Any]:
        self.refresh_settings()
        if self._use_live_model and existing_items:
            prompt = f"""你是一个语义记忆合并助手。请判断「新知识」应如何融入「现有记忆列表」。

新知识：
{json.dumps(item, ensure_ascii=False)}

现有记忆：
{json.dumps(existing_items, ensure_ascii=False)}

规则：
- add：新知识涵盖的概念在现有记忆中完全没有 → 新增一条独立条目
- supplement：现有某条记忆已涉及同一主题，但新知识补充了额外细节或角度 → 追加到那条记忆末尾
- revise：现有某条记忆存在错误或被新知识取代 → 用新内容替换
- ignore：与现有某条记忆完全重复或更不具体

返回 JSON（不要输出其他内容）：
{{
  "action": "add | supplement | revise | ignore",
  "target_id": "现有条目 ID（add 时省略）",
  "appended_content": "追加内容（supplement 时提供）",
  "new_content": "替换内容（revise 时提供）"
}}"""
            payload = await self._json_completion(
                system_prompt="你是一个语义记忆合并助手。只返回 JSON。",
                user_prompt=prompt,
            )
            if payload:
                return payload
        return self._mock_merge(item, existing_items)

    async def generate_teach_reply(
        self,
        flat_knowledge: list[dict[str, Any]],
        summary: str | None,
        recent_messages: list[dict[str, str]],
    ) -> str:
        self.refresh_settings()
        if self._use_live_model:
            messages = [{"role": "system", "content": build_teach_system_prompt(flat_knowledge)}]
            if summary:
                messages.append({"role": "system", "content": f"历史摘要：{summary}"})
            messages.extend(recent_messages)
            content = await self._chat_completion(messages)
            if content:
                return content
        return self._mock_teach_reply(flat_knowledge, recent_messages)

    async def interpret_correction(self, student_message: str, flat_knowledge: list[dict[str, Any]]) -> dict[str, Any]:
        self.refresh_settings()
        if self._use_live_model:
            payload = await self._json_completion(
                system_prompt="你是一个知识修正助手，只返回 JSON。",
                user_prompt=build_knowledge_edit_prompt(student_message, flat_knowledge),
            )
            if payload:
                return payload
        return self._mock_correction(student_message, flat_knowledge)

    async def answer_question(
        self,
        flat_knowledge: list[dict[str, Any]],
        question_text: str,
        options: dict[str, str] | None = None,
        conversational: bool = False,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        self.refresh_settings()
        if self._use_live_model:
            if options:
                payload = await self._json_completion(
                    system_prompt="You are a careful AI student. Return JSON only.",
                    user_prompt=build_test_prompt(flat_knowledge, question_text, options),
                )
                if payload:
                    return payload
            elif conversational:
                content = await self._live_conversational_answer(flat_knowledge, question_text, history or [])
                if content:
                    return {
                        "answer": None,
                        "reasoning": "Generated from the current conversation history and learned knowledge.",
                        "content": content,
                    }
        return self._mock_answer(flat_knowledge, question_text, options=options, conversational=conversational)

    async def summarize_messages(self, messages: list[dict[str, str]]) -> str:
        self.refresh_settings()
        if self._use_live_model:
            content = await self._chat_completion(
                [
                    {"role": "system", "content": "你是一个教学对话摘要助手。"},
                    {"role": "user", "content": build_summary_prompt(messages)},
                ]
            )
            if content:
                return content
        return self._mock_summary(messages)

    @property
    def _use_live_model(self) -> bool:
        return bool(self.settings.deepseek_api_key and not self.settings.mock_ai_enabled)

    async def _chat_completion(self, messages: list[dict[str, str]], response_format: dict[str, str] | None = None) -> str:
        url = f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.settings.deepseek_model,
            "messages": messages,
            "temperature": 0.4,
        }
        if response_format:
            payload["response_format"] = response_format
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    async def _json_completion(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        try:
            content = await self._chat_completion(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
        except Exception:  # noqa: BLE001
            return {}
        return _extract_json(content)

    async def _live_conversational_answer(
        self,
        flat_knowledge: list[dict[str, Any]],
        question_text: str,
        history: list[dict[str, str]],
    ) -> str:
        try:
            messages = [
                {
                    "role": "system",
                    "content": build_student_test_system_prompt(flat_knowledge),
                }
            ]
            messages.extend(history)
            last_history = history[-1] if history else None
            if last_history != {"role": "user", "content": question_text}:
                messages.append({"role": "user", "content": question_text})
            return await self._chat_completion(messages)
        except Exception:  # noqa: BLE001
            return ""

    def _mock_extract_knowledge(self, student_message: str) -> dict[str, Any]:
        lowered = student_message.lower()
        quoted = re.findall(r'"([^"]{6,})"', student_message) + re.findall(r"“([^”]{6,})”", student_message)
        topic = "general"
        for candidate, keywords in TOPIC_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                topic = candidate
                break
        items: list[dict[str, Any]] = []
        if any(hint in lowered for hint in GRAMMAR_HINTS) or quoted:
            if student_message.strip():
                items.append(
                    {
                        "type": "knowledge",
                        "topic": topic,
                        "content": student_message.strip()[:240],
                        "created_at": _now_iso(),
                    }
                )
        for sentence in quoted:
            items.append(
                {
                    "type": "example",
                    "topic": topic,
                    "sentence": sentence.strip(),
                    "explanation": "学生提供的例句",
                    "created_at": _now_iso(),
                }
            )
        return {
            "has_knowledge": bool(items),
            "items": items,
        }

    def _mock_merge(self, item: dict[str, Any], existing_items: list[dict[str, Any]]) -> dict[str, Any]:
        key = "content" if item["type"] == "knowledge" else "sentence"
        new_text = _normalize(item.get(key))
        if not new_text:
            return {"action": "ignore"}
        for existing in existing_items:
            existing_text = _normalize(existing.get(key))
            if not existing_text:
                continue
            if new_text == existing_text:
                return {"action": "ignore", "target_id": existing["id"]}
            if new_text in existing_text or existing_text in new_text:
                merged_text = item.get(key) if len(new_text) > len(existing_text) else existing.get(key)
                return {
                    "action": "update",
                    "target_id": existing["id"],
                    key: merged_text,
                    "explanation": item.get("explanation") or existing.get("explanation"),
                }
            if _token_overlap(new_text, existing_text) >= 4:
                return {
                    "action": "update",
                    "target_id": existing["id"],
                    key: item.get(key),
                    "explanation": item.get("explanation") or existing.get("explanation"),
                }
            overlap = _token_overlap(new_text, existing_text)
            if 2 <= overlap <= 3:
                return {
                    "action": "supplement",
                    "target_id": existing["id"],
                    "appended_content": item.get(key),
                }
        return {"action": "add"}

    def _mock_teach_reply(self, flat_knowledge: list[dict[str, Any]], recent_messages: list[dict[str, str]]) -> str:
        last_user = next((msg["content"] for msg in reversed(recent_messages) if msg["role"] == "user"), "")
        if not flat_knowledge:
            return "我现在还是一张白纸，只记住了你刚刚开始教我的内容。你能先告诉我名词从句最基本的判断方法吗？"

        rules = [item["content"] for item in flat_knowledge if item["item_type"] == "knowledge" and item.get("content")]
        examples = [item["sentence"] for item in flat_knowledge if item["item_type"] == "example" and item.get("sentence")]
        remembered = "；".join(rules[:2]) if rules else "一些你刚刚教给我的规则"
        if "?" in last_user or "？" in last_user:
            return f"根据你之前教我的，我会先从这些规则理解：{remembered}。如果这个问题超出了我学过的范围，我就还不太确定。你能再给我一个对应的例句让我确认吗？"
        if examples:
            return f"我先记住了：{remembered}。我也看到你给了例句，比如 “{examples[0]}”。我理解得对吗：我下次遇到类似结构时，应该先看从句在整句里充当什么成分？"
        return f"我记下来了：{remembered}。不过我还想再学得更稳一点，你能再给我一个例句或者一个容易混淆的情况吗？"

    def _mock_correction(self, student_message: str, flat_knowledge: list[dict[str, Any]]) -> dict[str, Any]:
        lowered = student_message.lower()
        action = "update"
        if any(word in lowered for word in ["删除", "forget", "删掉", "remove", "去掉"]):
            action = "delete"

        target = None
        for item in flat_knowledge:
            label = item.get("content") or item.get("sentence") or ""
            if label and (label[:8] in student_message or _token_overlap(label, student_message) >= 3):
                target = item
                break

        if target is None and flat_knowledge:
            target = flat_knowledge[-1]

        if target is None:
            return {"action": "unclear"}

        if action == "delete":
            return {"action": "delete", "target_id": target["id"]}

        new_content = student_message
        for marker in ["应该是", "改成", "应改为", "而是"]:
            if marker in student_message:
                new_content = student_message.split(marker, 1)[-1].strip("：: ")
                break
        return {"action": "update", "target_id": target["id"], "new_content": new_content}

    def _mock_answer(
        self,
        flat_knowledge: list[dict[str, Any]],
        question_text: str,
        options: dict[str, str] | None = None,
        conversational: bool = False,
    ) -> dict[str, Any]:
        learned_text = " ".join(
            filter(
                None,
                [item.get("content") or item.get("sentence") for item in flat_knowledge],
            )
        )
        if conversational or options is None:
            if _token_overlap(question_text, learned_text) == 0:
                return {
                    "answer": None,
                    "reasoning": "这超出了我目前学到的内容。",
                    "content": "我还没学到这个，所以只能说我不太确定。你可以先教我相关规则，再来考我一次吗？",
                }
            snippet = next(
                (item.get("content") or item.get("sentence") for item in flat_knowledge if _token_overlap(question_text, item.get("content") or item.get("sentence") or "") >= 2),
                None,
            )
            return {
                "answer": None,
                "reasoning": f"我根据已学知识匹配到了：{snippet or '已学内容中的相关规则'}。",
                "content": f"根据你之前教我的，我会优先想到：{snippet or '相关从句的判断规则'}。如果你愿意，可以继续追问我为什么这样判断。",
            }

        option_scores = {key: _token_overlap(question_text + " " + learned_text, value) for key, value in options.items()}
        best_answer = max(option_scores, key=option_scores.get)
        score = option_scores[best_answer]
        if score == 0:
            reasoning = "我没有学到足够相关的内容，所以这是基于非常有限信息的猜测。"
        else:
            reasoning = "我根据你教过我的知识和题干里的关键词做了最接近的匹配。"
        return {"answer": best_answer, "reasoning": reasoning}

    def _mock_summary(self, messages: list[dict[str, str]]) -> str:
        user_points = [msg["content"] for msg in messages if msg["role"] == "user"]
        assistant_points = [msg["content"] for msg in messages if msg["role"] == "assistant"]
        summary = []
        if user_points:
            summary.append(f"学生主要讲了 {min(len(user_points), 3)} 个知识片段。")
        if assistant_points:
            summary.append("AI 一直在追问例句、判断依据和易错点。")
        if not summary:
            return "当前还没有足够内容可摘要。"
        return " ".join(summary)
