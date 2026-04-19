from __future__ import annotations

import pytest

from app.prompts.self_test import build_student_test_system_prompt
from app.prompts.teach import build_teach_system_prompt
from app.prompts.test_answer import build_test_prompt

pytestmark = pytest.mark.asyncio


async def test_teacher_student_detail_includes_session_preview_and_scope(client):
    teacher = (
        await client.post(
            "/api/auth/register",
            json={
                "username": "teacher_detail",
                "password": "password123",
                "display_name": "Teacher Detail",
                "role": "teacher",
                "teacher_reg_code": "APPRENTICE-TEACHER",
            },
        )
    ).json()
    teacher_headers = {"Authorization": f'Bearer {teacher["access_token"]}'}

    classroom = (
        await client.post(
            "/api/classes",
            headers=teacher_headers,
            json={"name": "Detail Class", "course_topic": "英语名词从句总览"},
        )
    ).json()

    student = (
        await client.post(
            "/api/auth/register",
            json={
                "username": "student_detail",
                "password": "password123",
                "display_name": "Student Detail",
                "role": "student",
                "invite_code": classroom["invite_code"],
            },
        )
    ).json()
    student_headers = {"Authorization": f'Bearer {student["access_token"]}'}

    session = (
        await client.post(
            "/api/chat/sessions",
            headers=student_headers,
            json={"class_id": classroom["id"], "session_type": "teach", "title": "Teach Session"},
        )
    ).json()

    send = await client.post(
        "/api/chat/send",
        headers=student_headers,
        json={
            "session_id": session["id"],
            "content": '宾语从句常作动词的宾语，比如 "I think that he is honest."',
        },
    )
    assert send.status_code == 200

    detail = await client.get(
        f'/api/analytics/class/{classroom["id"]}/students/{student["user"]["id"]}',
        headers=teacher_headers,
    )
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["class_scope"]["course_topic"] == "英语名词从句总览"
    assert payload["sessions"][0]["type_label"] == "Teach 对话"
    assert payload["sessions"][0]["message_count"] == 2
    assert "宾语从句常作动词的宾语" in payload["sessions"][0]["preview"]


async def test_prompts_frame_the_agent_as_student_not_ai():
    teach_prompt = build_teach_system_prompt([], learning_scope={"course_topic": "英语名词从句", "covered_topic_labels": ["宾语从句"], "knowledge_focuses": ["通用", "定义"]})
    self_test_prompt = build_student_test_system_prompt([], learning_scope={"course_topic": "英语名词从句"})
    test_prompt = build_test_prompt([], "这是什么从句？", {"A": "主语从句", "B": "宾语从句", "C": "表语从句", "D": "同位语从句"})

    assert "AI 学生" not in teach_prompt
    assert "AI学生" not in self_test_prompt
    assert "AI 学生" not in test_prompt
    assert "高中生" in teach_prompt
    assert "学生" in self_test_prompt
    assert "学生" in test_prompt

