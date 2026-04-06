from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_student_self_test_does_not_change_knowledge(client):
    teacher = (
        await client.post(
            "/api/auth/register",
            json={
                "username": "teacher_2",
                "password": "password123",
                "display_name": "Teacher Two",
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
            json={"name": "Self Test Class"},
        )
    ).json()

    student = (
        await client.post(
            "/api/auth/register",
            json={
                "username": "student_2",
                "password": "password123",
                "display_name": "Student Two",
                "role": "student",
                "invite_code": classroom["invite_code"],
            },
        )
    ).json()
    student_headers = {"Authorization": f'Bearer {student["access_token"]}'}

    initial = await client.get(f'/api/knowledge/{classroom["id"]}', headers=student_headers)
    assert initial.status_code == 200
    assert initial.json()["version"] == 1

    session = (
        await client.post(
            "/api/chat/sessions",
            headers=student_headers,
            json={"class_id": classroom["id"], "session_type": "student_test_free", "title": "Free test"},
        )
    ).json()

    response = await client.post(
        "/api/chat/send",
        headers=student_headers,
        json={"session_id": session["id"], "content": "what can you do about appositive clauses?"},
    )
    assert response.status_code == 200
    assert response.json()["knowledge_changed"] is False

    after = await client.get(f'/api/knowledge/{classroom["id"]}', headers=student_headers)
    assert after.status_code == 200
    assert after.json()["version"] == 1
