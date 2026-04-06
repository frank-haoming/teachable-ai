<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">学生详情</span>
        <h2 class="page-title">{{ detail?.student_name || '学生 #' + studentId }}</h2>
        <p class="page-subtitle">这里汇总该学生在当前班级中的 AI 知识、所有 Teach/Test 会话与对话消息。</p>
      </div>
      <div style="display:flex; gap:10px">
        <el-button plain @click="exportMessages">导出对话记录</el-button>
        <router-link :to="{ name: 'teacher-analytics', params: { classId } }">
          <el-button plain>返回分析页</el-button>
        </router-link>
      </div>
    </header>

    <section class="soft-grid two-col">
      <article class="section-card" style="padding: 20px">
        <h3>知识库快照</h3>
        <div v-if="flatKnowledge.length" class="knowledge-grid">
          <KnowledgeCard v-for="item in flatKnowledge" :key="item.id" :item="item" />
        </div>
        <div v-else class="empty-state">该学生还没有知识记录。</div>
      </article>
      <article class="section-card" style="padding: 20px">
        <h3>会话列表</h3>
        <div class="session-list">
          <div
            v-for="session in detail?.sessions || []"
            :key="session.id"
            class="session-row"
            role="button"
            tabindex="0"
            @click="jumpToSession(session.id)"
            @keydown.enter="jumpToSession(session.id)"
          >
            <div>
              <strong>{{ session.title || session.type }}</strong>
              <p class="muted">{{ new Date(session.updated_at).toLocaleString("zh-CN") }}</p>
            </div>
            <span class="data-chip">{{ session.type }}</span>
          </div>
          <div v-if="!detail?.sessions?.length" class="empty-state">暂无会话。</div>
        </div>
      </article>
    </section>

    <section ref="messagesSection" class="section-card" style="padding: 20px">
      <h3>完整对话记录</h3>
      <div v-if="Object.keys(sessionMap).length">
        <el-collapse v-model="openSessions">
          <el-collapse-item
            v-for="(msgs, sid) in sessionMap"
            :key="sid"
            :name="String(sid)"
          >
            <template #title>
              <div class="session-collapse-header">
                <span class="data-chip">{{ sessionTypeLabel(sid) }}</span>
                <span class="muted">Session {{ sid }} · {{ msgs.length }} 条消息 · {{ formatTime(msgs[msgs.length - 1]?.created_at) }}</span>
              </div>
            </template>
            <div class="session-messages">
              <ChatBubble
                v-for="(message, index) in msgs"
                :key="`${sid}-${index}`"
                :message="message"
              />
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
      <div v-else class="empty-state">当前还没有对话记录。</div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";

import { fetchStudentDetail } from "@/api/analytics";
import ChatBubble from "@/components/ChatBubble.vue";
import KnowledgeCard from "@/components/KnowledgeCard.vue";

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
  studentId: {
    type: [String, Number],
    required: true,
  },
});

const detail = ref(null);
const openSessions = ref([]);
const messagesSection = ref(null);

const flatKnowledge = computed(() => {
  const data = detail.value?.knowledge;
  if (!data?.topics) return [];
  const items = [];
  for (const [topic, payload] of Object.entries(data.topics)) {
    for (const item of payload.knowledge || []) {
      items.push({ ...item, topic, item_type: "knowledge" });
    }
    for (const item of payload.examples || []) {
      items.push({ ...item, topic, item_type: "example" });
    }
  }
  return items.sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""));
});

const sessionMap = computed(() => {
  const map = {};
  for (const msg of detail.value?.messages || []) {
    if (!map[msg.session_id]) map[msg.session_id] = [];
    map[msg.session_id].push(msg);
  }
  return map;
});

const sessionTypeLabel = (sid) => {
  const session = detail.value?.sessions?.find((s) => s.id === Number(sid));
  return session?.type || "unknown";
};

const formatTime = (value) => {
  if (!value) return "";
  return new Date(value).toLocaleString("zh-CN");
};

const jumpToSession = async (sessionId) => {
  const key = String(sessionId);
  if (!openSessions.value.includes(key)) {
    openSessions.value = [...openSessions.value, key];
  }
  await nextTick();
  messagesSection.value?.scrollIntoView({ behavior: "smooth", block: "start" });
};

const exportMessages = () => {
  const student = detail.value?.student_name || `student_${props.studentId}`;
  const lines = [];
  lines.push(`学生：${student}　班级 ID：${props.classId}`);
  lines.push(`导出时间：${new Date().toLocaleString("zh-CN")}`);
  lines.push("=".repeat(60));

  for (const [sid, msgs] of Object.entries(sessionMap.value)) {
    lines.push(`\n【Session ${sid} · ${sessionTypeLabel(sid)}】`);
    for (const msg of msgs) {
      const role = msg.role === "assistant" ? "AI 学生" : "学生";
      const time = formatTime(msg.created_at);
      lines.push(`[${time}] ${role}：${msg.content}`);
    }
  }

  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `对话记录_${student}.txt`;
  a.click();
  URL.revokeObjectURL(url);
};

const load = async () => {
  detail.value = await fetchStudentDetail(props.classId, props.studentId);
  // Open all sessions by default
  openSessions.value = Object.keys(sessionMap.value);
};

onMounted(load);
</script>

<style scoped>
.knowledge-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 420px;
  overflow-y: auto;
}

.session-list {
  max-height: 340px;
  overflow-y: auto;
}

.session-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid rgba(13, 148, 136, 0.08);
  cursor: pointer;
  border-radius: 8px;
  transition: background 150ms ease;
  padding-inline: 8px;
}

.session-row:hover {
  background: rgba(13, 148, 136, 0.06);
}

.session-collapse-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.session-messages {
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
