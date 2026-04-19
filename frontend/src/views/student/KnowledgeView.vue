<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">已学知识查看</span>
        <h2 class="page-title">{{ classInfo?.name || "知识库" }}</h2>
        <p class="page-subtitle">这里展示这位学习伙伴当前掌握的规则与例句。你可以直接编辑，也可以回到 Teach 区对话修正。</p>
      </div>
      <router-link :to="{ name: 'student-teach', params: { classId } }">
        <el-button type="primary">回到 Teach</el-button>
      </router-link>
    </header>

    <div v-if="!items.length" class="empty-state section-card">这位学习伙伴还没有任何稳定记忆。先去 Teach 区开始教学。</div>
    <section v-else class="soft-grid two-col">
      <KnowledgeCard v-for="item in items" :key="item.id" :item="item">
        <template #actions="{ item: knowledgeItem }">
          <el-button text @click="openEdit(knowledgeItem)">编辑</el-button>
          <el-button text type="warning" @click="sendToTeach(knowledgeItem)">对话修正</el-button>
        </template>
      </KnowledgeCard>
    </section>

    <section v-if="changelog.length" class="section-card changelog-card">
      <h3>最近改动</h3>
      <div class="changelog-list">
        <div v-for="entry in changelog" :key="entry.id" class="changelog-row">
          <span :class="['action-chip', `action-chip--${entry.action}`]">{{ actionLabel(entry.action) }}</span>
          <span class="changelog-content">{{ changelogSummary(entry) }}</span>
          <span class="muted changelog-time">{{ new Date(entry.created_at).toLocaleString('zh-CN') }}</span>
        </div>
      </div>
    </section>

    <el-dialog v-model="editDialog" title="直接编辑知识条目" width="560px">
      <el-form label-position="top">
        <el-form-item label="内容">
          <el-input
            v-model="editForm.main"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </el-form-item>
        <el-form-item v-if="activeItem?.item_type === 'example'" label="解释">
          <el-input v-model="editForm.explanation" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import { fetchClassDetail } from "@/api/classes";
import { fetchFlatKnowledge, fetchKnowledgeChangelog, updateKnowledgeItem } from "@/api/knowledge";
import KnowledgeCard from "@/components/KnowledgeCard.vue";

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
});

const router = useRouter();
const classInfo = ref(null);
const items = ref([]);
const changelog = ref([]);
const editDialog = ref(false);
const activeItem = ref(null);
const editForm = ref({ main: "", explanation: "" });

const ACTION_LABELS = {
  create: "新增",
  update: "更新",
  delete: "删除",
  topic_migration: "迁移",
};
const actionLabel = (action) => ACTION_LABELS[action] || action;

const changelogSummary = (entry) => {
  const after = entry.after_data || entry.before_data || {};
  const text = after.content || after.sentence || entry.target_item_id;
  return text ? String(text).slice(0, 60) + (String(text).length > 60 ? "…" : "") : "—";
};

const load = async () => {
  classInfo.value = await fetchClassDetail(props.classId);
  [items.value, changelog.value] = await Promise.all([
    fetchFlatKnowledge(props.classId),
    fetchKnowledgeChangelog(props.classId).catch(() => []),
  ]);
};

const openEdit = (item) => {
  activeItem.value = item;
  editForm.value = {
    main: item.content || item.sentence || "",
    explanation: item.explanation || "",
  };
  editDialog.value = true;
};

const saveEdit = async () => {
  try {
    const payload =
      activeItem.value.item_type === "knowledge"
        ? { content: editForm.value.main }
        : { sentence: editForm.value.main, explanation: editForm.value.explanation };
    await updateKnowledgeItem(activeItem.value.id, props.classId, payload);
    editDialog.value = false;
    await load();
    ElMessage.success("知识条目已更新。");
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "更新失败。");
  }
};

const sendToTeach = async (item) => {
  await router.push({ name: "student-teach", params: { classId: props.classId }, query: { seed: item.id } });
};

onMounted(load);
</script>

<style scoped>
.changelog-card {
  padding: 20px;
  margin-top: 4px;
}

.changelog-card h3 {
  margin: 0 0 14px;
}

.changelog-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 260px;
  overflow-y: auto;
}

.changelog-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 8px 6px;
  border-radius: 10px;
  border-bottom: 1px solid rgba(13, 148, 136, 0.06);
}

.action-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
  white-space: nowrap;
}

.action-chip--create { background: rgba(22, 163, 74, 0.1); color: #166534; }
.action-chip--update { background: rgba(234, 179, 8, 0.12); color: #78350f; }
.action-chip--delete { background: rgba(220, 38, 38, 0.1); color: #991b1b; }
.action-chip--topic_migration { background: rgba(13, 148, 136, 0.08); color: var(--aa-primary-deep); }

.changelog-content {
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.changelog-time {
  font-size: 0.8rem;
  white-space: nowrap;
}
</style>
