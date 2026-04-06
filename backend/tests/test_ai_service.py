from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.ai_service import AIService

pytestmark = pytest.mark.asyncio


def _live_settings() -> SimpleNamespace:
    return SimpleNamespace(
        deepseek_api_key="test-key",
        mock_ai_enabled=False,
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
    )


class CapturingAIService(AIService):
    def __init__(self) -> None:
        super().__init__(settings=_live_settings())
        self.captured_messages: list[dict[str, str]] = []

    async def _chat_completion(self, messages, response_format=None):  # noqa: ANN001
        self.captured_messages = messages
        return "ok"


async def test_live_conversational_answer_does_not_duplicate_current_user_message():
    service = CapturingAIService()

    current_question = "请再用一句话总结一下。"
    history = [
        {"role": "user", "content": "我刚刚教了你什么？"},
        {"role": "assistant", "content": "你教了我宾语从句的基本作用。"},
        {"role": "user", "content": current_question},
    ]

    result = await service._live_conversational_answer([], current_question, history)

    assert result == "ok"
    assert service.captured_messages[1:] == history
    repeated_questions = [
        message
        for message in service.captured_messages
        if message["role"] == "user" and message["content"] == current_question
    ]
    assert len(repeated_questions) == 1


async def test_live_conversational_answer_appends_current_message_when_missing():
    service = CapturingAIService()
    history = [
        {"role": "user", "content": "我刚刚教了你什么？"},
        {"role": "assistant", "content": "你教了我宾语从句的基本作用。"},
    ]

    result = await service._live_conversational_answer([], "请再用一句话总结一下。", history)

    assert result == "ok"
    assert service.captured_messages[1:-1] == history
    assert service.captured_messages[-1] == {"role": "user", "content": "请再用一句话总结一下。"}
