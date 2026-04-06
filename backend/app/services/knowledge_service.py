from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models import AIKnowledge, ClassRoom, KnowledgeChangeLog
from app.services.ai_service import AIService
from app.utils.constants import TOPIC_META, clone_knowledge_template


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeService:
    def __init__(self, ai_service: AIService | None = None) -> None:
        self.ai_service = ai_service or AIService.build()

    async def get_or_create_knowledge(
        self,
        db: AsyncSession,
        student_id: int,
        class_id: int,
        template: dict | None = None,
    ) -> AIKnowledge:
        result = await db.execute(
            select(AIKnowledge).where(AIKnowledge.student_id == student_id, AIKnowledge.class_id == class_id)
        )
        record = result.scalar_one_or_none()
        if record:
            return record
        if template is None:
            class_result = await db.execute(select(ClassRoom).where(ClassRoom.id == class_id))
            classroom = class_result.scalar_one()
            template = classroom.knowledge_template
        record = AIKnowledge(
            student_id=student_id,
            class_id=class_id,
            knowledge_data=clone_knowledge_template(template),
            version=1,
        )
        db.add(record)
        await db.flush()
        return record

    def flatten_knowledge(self, knowledge_data: dict) -> list[dict]:
        flattened: list[dict] = []
        topics = knowledge_data.get("topics", {})
        for topic, payload in topics.items():
            for item in payload.get("knowledge", []):
                flattened.append(
                    {
                        "id": item["id"],
                        "topic": topic,
                        "topic_name": TOPIC_META.get(topic, topic),
                        "item_type": "knowledge",
                        "content": item.get("content"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                    }
                )
            for item in payload.get("examples", []):
                flattened.append(
                    {
                        "id": item["id"],
                        "topic": topic,
                        "topic_name": TOPIC_META.get(topic, topic),
                        "item_type": "example",
                        "sentence": item.get("sentence"),
                        "explanation": item.get("explanation"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                    }
                )
        flattened.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return flattened

    def count_items(self, knowledge_data: dict) -> int:
        return len(self.flatten_knowledge(knowledge_data))

    async def apply_extractions(
        self,
        db: AsyncSession,
        knowledge: AIKnowledge,
        items: list[dict],
        actor_user_id: int,
        source: str = "dialogue",
    ) -> bool:
        changed = False
        data = deepcopy(knowledge.knowledge_data)
        for item in items:
            topic = item.get("topic") or "general"
            if topic not in data["topics"]:
                topic = "general"
            bucket_key = "knowledge" if item["type"] == "knowledge" else "examples"
            bucket = data["topics"][topic][bucket_key]
            merge_target = []
            for existing in bucket:
                merge_target.append(
                    {
                        "id": existing["id"],
                        "content": existing.get("content"),
                        "sentence": existing.get("sentence"),
                        "explanation": existing.get("explanation"),
                    }
                )
            decision = await self.ai_service.decide_merge(item, merge_target)
            action = decision.get("action", "add")
            if action == "ignore":
                continue
            # "revise" is a synonym for "update" from the 4-action prompt
            if action == "revise":
                action = "update"
                if decision.get("new_content"):
                    key_field = "content" if bucket_key == "knowledge" else "sentence"
                    decision[key_field] = decision["new_content"]
            if action == "supplement" and decision.get("target_id"):
                target = next((e for e in bucket if e["id"] == decision["target_id"]), None)
                if target:
                    before_data = deepcopy(target)
                    append_text = decision.get("appended_content") or item.get("content") or item.get("sentence")
                    if append_text:
                        key_field = "content" if bucket_key == "knowledge" else "sentence"
                        existing_val = target.get(key_field) or ""
                        target[key_field] = f"{existing_val}；{append_text}" if existing_val else append_text
                        target["updated_at"] = _now_iso()
                        db.add(KnowledgeChangeLog(
                            knowledge_id=knowledge.id,
                            target_item_id=target["id"],
                            item_type=item["type"],
                            action="update",
                            source=source,
                            before_data=before_data,
                            after_data=deepcopy(target),
                            actor_user_id=actor_user_id,
                        ))
                        changed = True
                continue
            if action == "update" and decision.get("target_id"):
                target = next((entry for entry in bucket if entry["id"] == decision["target_id"]), None)
                if target is None:
                    action = "add"
                else:
                    before_data = deepcopy(target)
                    if bucket_key == "knowledge":
                        target["content"] = decision.get("content") or item.get("content") or target.get("content")
                    else:
                        target["sentence"] = decision.get("sentence") or item.get("sentence") or target.get("sentence")
                        target["explanation"] = (
                            decision.get("explanation")
                            or item.get("explanation")
                            or target.get("explanation")
                        )
                    target["updated_at"] = _now_iso()
                    db.add(
                        KnowledgeChangeLog(
                            knowledge_id=knowledge.id,
                            target_item_id=target["id"],
                            item_type=item["type"],
                            action="update",
                            source=source,
                            before_data=before_data,
                            after_data=deepcopy(target),
                            actor_user_id=actor_user_id,
                        )
                    )
                    changed = True
                    continue
            if action == "add":
                entry = {
                    "id": f'{"k" if item["type"] == "knowledge" else "e"}_{uuid4().hex[:8]}',
                    "created_at": _now_iso(),
                    "updated_at": _now_iso(),
                }
                if bucket_key == "knowledge":
                    entry["content"] = item.get("content")
                else:
                    entry["sentence"] = item.get("sentence")
                    entry["explanation"] = item.get("explanation")
                bucket.append(entry)
                db.add(
                    KnowledgeChangeLog(
                        knowledge_id=knowledge.id,
                        target_item_id=entry["id"],
                        item_type=item["type"],
                        action="create",
                        source=source,
                        before_data=None,
                        after_data=deepcopy(entry),
                        actor_user_id=actor_user_id,
                    )
                )
                changed = True

        if changed:
            data["version"] = knowledge.version + 1
            data["updated_at"] = _now_iso()
            knowledge.version += 1
            knowledge.knowledge_data = data
            flag_modified(knowledge, "knowledge_data")
            knowledge.updated_at = datetime.now(timezone.utc)
            await db.flush()
        return changed

    async def apply_dialogue_correction(
        self,
        db: AsyncSession,
        knowledge: AIKnowledge,
        message: str,
        actor_user_id: int,
    ) -> dict:
        flat = self.flatten_knowledge(knowledge.knowledge_data)
        decision = await self.ai_service.interpret_correction(message, flat)
        action = decision.get("action", "unclear")
        if action == "unclear":
            return {"action": "unclear", "target_item_id": None, "version": knowledge.version}
        if action == "delete":
            await self.delete_item(db, knowledge, decision["target_id"], actor_user_id, source="dialogue")
            return {"action": "delete", "target_item_id": decision["target_id"], "version": knowledge.version}
        await self.update_item(
            db,
            knowledge,
            decision["target_id"],
            {"content": decision.get("new_content"), "sentence": decision.get("new_content")},
            actor_user_id,
            source="dialogue",
        )
        return {"action": "update", "target_item_id": decision["target_id"], "version": knowledge.version}

    async def update_item(
        self,
        db: AsyncSession,
        knowledge: AIKnowledge,
        item_id: str,
        payload: dict,
        actor_user_id: int,
        source: str = "direct_edit",
    ) -> None:
        topic, bucket_key, item = self.find_item(knowledge.knowledge_data, item_id)
        if item is None or bucket_key is None:
            raise ValueError("Knowledge item not found.")
        before_data = deepcopy(item)
        if bucket_key == "knowledge":
            item["content"] = payload.get("content") or item.get("content")
        else:
            item["sentence"] = payload.get("sentence") or payload.get("content") or item.get("sentence")
            item["explanation"] = payload.get("explanation") or item.get("explanation")
        item["updated_at"] = _now_iso()
        self._touch(knowledge)
        db.add(
            KnowledgeChangeLog(
                knowledge_id=knowledge.id,
                target_item_id=item_id,
                item_type="knowledge" if bucket_key == "knowledge" else "example",
                action="update",
                source=source,
                before_data=before_data,
                after_data=deepcopy(item),
                actor_user_id=actor_user_id,
            )
        )
        await db.flush()

    async def delete_item(
        self,
        db: AsyncSession,
        knowledge: AIKnowledge,
        item_id: str,
        actor_user_id: int,
        source: str = "direct_edit",
    ) -> None:
        topic, bucket_key, item = self.find_item(knowledge.knowledge_data, item_id)
        if item is None or bucket_key is None or topic is None:
            raise ValueError("Knowledge item not found.")
        bucket = knowledge.knowledge_data["topics"][topic][bucket_key]
        bucket[:] = [entry for entry in bucket if entry["id"] != item_id]
        self._touch(knowledge)
        db.add(
            KnowledgeChangeLog(
                knowledge_id=knowledge.id,
                target_item_id=item_id,
                item_type="knowledge" if bucket_key == "knowledge" else "example",
                action="delete",
                source=source,
                before_data=deepcopy(item),
                after_data=None,
                actor_user_id=actor_user_id,
            )
        )
        await db.flush()

    def find_item(self, knowledge_data: dict, item_id: str) -> tuple[str | None, str | None, dict | None]:
        for topic, payload in knowledge_data.get("topics", {}).items():
            for key in ("knowledge", "examples"):
                for item in payload.get(key, []):
                    if item["id"] == item_id:
                        return topic, key, item
        return None, None, None

    def _touch(self, knowledge: AIKnowledge) -> None:
        knowledge.version += 1
        knowledge.updated_at = datetime.now(timezone.utc)
        knowledge.knowledge_data["version"] = knowledge.version
        knowledge.knowledge_data["updated_at"] = _now_iso()
        flag_modified(knowledge, "knowledge_data")

