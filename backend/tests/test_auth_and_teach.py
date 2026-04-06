from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_teacher_registration_requires_code(client):
    bad = await client.post(
        "/api/auth/register",
        json={
            "username": "teacher_bad",
            "password": "password123",
            "display_name": "Bad Teacher",
            "role": "teacher",
            "teacher_reg_code": "wrong-code",
        },
    )
    assert bad.status_code == 403

    good = await client.post(
        "/api/auth/register",
        json={
            "username": "teacher_ok",
            "password": "password123",
            "display_name": "Good Teacher",
            "role": "teacher",
            "teacher_reg_code": "APPRENTICE-TEACHER",
        },
    )
    assert good.status_code == 200
    assert good.json()["user"]["role"] == "teacher"


async def test_teach_session_updates_knowledge(client):
    teacher = (
        await client.post(
            "/api/auth/register",
            json={
                "username": "teacher_1",
                "password": "password123",
                "display_name": "Teacher One",
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
            json={"name": "Grammar Class"},
        )
    ).json()

    student = (
        await client.post(
            "/api/auth/register",
            json={
                "username": "student_1",
                "password": "password123",
                "display_name": "Student One",
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
            json={"class_id": classroom["id"], "session_type": "teach", "title": "Teach"},
        )
    ).json()

    response = await client.post(
        "/api/chat/send",
        headers=student_headers,
        json={
            "session_id": session["id"],
            "content": '宾语从句常常作动词的宾语，比如 "I think that he is honest."',
        },
    )
    assert response.status_code == 200
    assert response.json()["knowledge_changed"] is True

    knowledge = await client.get(f'/api/knowledge/{classroom["id"]}/flat', headers=student_headers)
    assert knowledge.status_code == 200
    assert len(knowledge.json()) >= 1
