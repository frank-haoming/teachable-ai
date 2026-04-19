from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_class_scope_metadata_flows_to_teacher_and_student_views(client):
    teacher = (
        await client.post(
            "/api/auth/register",
            json={
                "username": "teacher_scope",
                "password": "password123",
                "display_name": "Teacher Scope",
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
            json={
                "name": "Scope Class",
                "course_topic": "名词从句综合辨析",
                "subject_description": "重点讲授主语从句、宾语从句与表语从句的辨析。",
                "covered_topics": ["subject_clause", "object_clause", "predicative_clause"],
                "knowledge_focuses": ["通用", "定义", "语法功能", "例子"],
            },
        )
    ).json()

    teacher_classes = await client.get("/api/classes", headers=teacher_headers)
    assert teacher_classes.status_code == 200
    teacher_payload = teacher_classes.json()[0]
    assert teacher_payload["course_topic"] == "名词从句综合辨析"
    assert teacher_payload["covered_topics"] == ["subject_clause", "object_clause", "predicative_clause"]
    assert teacher_payload["knowledge_focuses"] == ["通用", "定义", "语法功能", "例子"]

    student = (
        await client.post(
            "/api/auth/register",
            json={
                "username": "student_scope",
                "password": "password123",
                "display_name": "Student Scope",
                "role": "student",
                "invite_code": classroom["invite_code"],
            },
        )
    ).json()
    student_headers = {"Authorization": f'Bearer {student["access_token"]}'}

    student_detail = await client.get(f'/api/classes/{classroom["id"]}', headers=student_headers)
    assert student_detail.status_code == 200
    detail_payload = student_detail.json()
    assert detail_payload["course_topic"] == "名词从句综合辨析"
    assert detail_payload["covered_topic_labels"] == ["主语从句", "宾语从句", "表语从句"]
    assert detail_payload["knowledge_focuses"] == ["通用", "定义", "语法功能", "例子"]

