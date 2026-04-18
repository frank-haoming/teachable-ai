<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">Teach 区</span>
        <h2 class="page-title">{{ classInfo?.name || "教学对话" }}</h2>
        <p class="page-subtitle">
          这里的每条学生消息都会触发知识提取。Teach 区以外的测试不会写入记忆。
          <span v-if="aiName" class="ai-name-badge">正在教：{{ aiName }}</span>
        </p>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <el-button plain @click="nameDialog = true">给 AI 起名</el-button>
        <el-button plain @click="confirmNewSession">新建对话</el-button>
        <router-link :to="{ name: 'student-self-test', params: { classId } }">
          <el-button plain>前往自测</el-button>
        </router-link>
      </div>
    </header>

    <div class="split-layout">
      <section class="section-card chat-panel">
        <div ref="chatLogRef" class="chat-log">
          <template v-if="messages.length">
            <ChatBubble
              v-for="message in messages"
              :key="message.id"
              :message="message"
              :ai-name="aiName"
            />
          </template>
          <div v-else class="empty-state">先告诉 {{ aiName || 'AI' }} 一条规则、一个例句，或者你认为最容易混淆的点。</div>
        </div>
        <div class="focus-chips">
          <span
            v-for="topic in focusTopics"
            :key="topic"
            class="focus-chip"
            :class="{ 'focus-chip--active': activeFocus === topic }"
            @click="toggleFocus(topic)"
          >{{ topic }}</span>
        </div>
        <el-form class="chat-form" @submit.prevent="submitMessage">
          <el-form-item label="教学输入">
            <el-input
              v-model="draft"
              type="textarea"
              :autosize="{ minRows: 4, maxRows: 7 }"
              :placeholder="`例如：宾语从句常作动词的宾语；I think that he is honest. 这里 that 可以省略。Ctrl+Enter 发送`"
              @keydown.ctrl.enter.prevent="submitMessage"
            />
          </el-form-item>
          <div class="chat-actions">
            <el-button plain @click="draft = correctionSeed">填入纠正提示</el-button>
            <el-button plain :loading="extracting" :disabled="chatStore.loading" @click="saveMemory">保存记忆</el-button>
            <el-button type="primary" :loading="chatStore.loading" native-type="submit">发送并教学</el-button>
          </div>
        </el-form>
      </section>

      <KnowledgePanel :items="knowledgeItems" @refresh="loadKnowledge" @correct="seedCorrection" />
    </div>

    <!-- AI Naming Dialog -->
    <el-dialog v-model="nameDialog" title="给你的 AI 起名" width="380px">
      <p class="muted" style="margin-bottom: 16px">为这个班级的 AI 同学起一个专属名字吧（如"小明"），系统会自动加上"同学"。</p>
      <el-input v-model.trim="aiNameInput" placeholder="输入名字，如：小明" maxlength="10" show-word-limit />
      <template #footer>
        <el-button @click="nameDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAiName">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox, ElNotification } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { fetchClassDetail } from "@/api/classes";
import { manualExtract, updateSession } from "@/api/chat";
import { fetchFlatKnowledge } from "@/api/knowledge";
import ChatBubble from "@/components/ChatBubble.vue";
import KnowledgePanel from "@/components/KnowledgePanel.vue";
import { useChatStore } from "@/stores/chat";

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
});

const AI_NAME_KEY = (cid) => `ai_name_${cid}`;

const chatStore = useChatStore();
const route = useRoute();
const router = useRouter();
const classInfo = ref(null);
const knowledgeItems = ref([]);
const draft = ref("");
const session = ref(null);
const correctionSeed = ref("我发现你有一条知识需要修正：");
const chatLogRef = ref(null);
const nameDialog = ref(false);
const aiNameInput = ref("");
const aiName = ref(localStorage.getItem(AI_NAME_KEY(props.classId)) || "");

const focusTopics = ["定义", "基本结构", "常见引导词", "语法功能", "例子"];
const activeFocus = ref(null);
const extracting = ref(false);

const toggleFocus = (topic) => {
  activeFocus.value = activeFocus.value === topic ? null : topic;
};

const messages = computed(() => chatStore.messagesBySession[session.value?.id] || []);

const scrollToBottom = async () => {
  await nextTick();
  if (chatLogRef.value) {
    chatLogRef.value.lastElementChild?.scrollIntoView({ behavior: "smooth" });
  }
};

const loadKnowledge = async () => {
  knowledgeItems.value = await fetchFlatKnowledge(props.classId);
};

const hydrateCorrectionFromRoute = () => {
  const seedId = route.query.seed;
  if (!seedId) return;
  const target = knowledgeItems.value.find((item) => item.id === seedId);
  if (target) seedCorrection(target);
};

const bootstrap = async () => {
  classInfo.value = await fetchClassDetail(props.classId);
  await chatStore.loadSessions({ class_id: Number(props.classId), session_type: "teach" });

  const sessionIdFromQuery = route.query.session ? Number(route.query.session) : null;
  if (sessionIdFromQuery) {
    session.value = chatStore.sessions.find((s) => s.id === sessionIdFromQuery) || null;
  }
  if (!session.value) {
    session.value = await chatStore.ensureSession({
      classId: Number(props.classId),
      sessionType: "teach",
      title: "Teach Session",
      aiName: aiName.value || null,
    });
  }

  await chatStore.loadMessages(session.value.id);
  await loadKnowledge();
  hydrateCorrectionFromRoute();
  await scrollToBottom();
};

const seedCorrection = (item) => {
  const content = item.content || item.sentence;
  correctionSeed.value = `我发现你关于"${content}"的理解似乎有误，应该改成：`;
  draft.value = correctionSeed.value;
};

const saveAiName = async () => {
  const raw = aiNameInput.value.trim().replace(/同学$/, "");
  if (!raw) return;
  const full = `${raw}同学`;
  aiName.value = full;
  localStorage.setItem(AI_NAME_KEY(props.classId), full);
  nameDialog.value = false;
  if (session.value?.id) {
    try {
      await updateSession(session.value.id, { ai_name: full });
    } catch {
      // non-critical: name is still stored in localStorage
    }
  }
  ElMessage.success(`已将 AI 命名为"${full}"。`);
};

const confirmNewSession = async () => {
  try {
    await ElMessageBox.confirm(
      "新建对话不会清除已学知识，只会开启一段新的聊天记录。确定继续吗？",
      "新建对话",
      { confirmButtonText: "确定", cancelButtonText: "取消", type: "info" }
    );
    const { createSession } = await import("@/api/chat");
    const newSession = await createSession({
      class_id: Number(props.classId),
      session_type: "teach",
      title: "Teach Session",
      ai_name: aiName.value || null,
    });
    chatStore.sessions.unshift(newSession);
    session.value = newSession;
    chatStore.messagesBySession[newSession.id] = [];
    await router.replace({ ...route, query: { ...route.query, session: newSession.id } });
  } catch {
    // cancelled
  }
};

const submitMessage = async () => {
  if (!draft.value.trim() || chatStore.loading) return;
  try {
    const content = activeFocus.value
      ? `[聚焦：${activeFocus.value}] ${draft.value}`
      : draft.value;
    const result = await chatStore.pushMessage({
      session_id: session.value.id,
      content,
    });
    draft.value = "";
    activeFocus.value = null;
    await loadKnowledge();
    await scrollToBottom();
    if (result?.knowledge_changed) {
      ElNotification({
        title: `${aiName.value || "AI"} 记住了新知识`,
        message: `知识库已更新 · 版本 ${result.knowledge_version}`,
        type: "success",
        duration: 2500,
      });
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "发送失败。");
  }
};

const saveMemory = async () => {
  if (!session.value?.id || extracting.value) return;
  extracting.value = true;
  try {
    const result = await manualExtract(session.value.id);
    await loadKnowledge();
    ElNotification({
      title: "记忆已保存",
      message: result.changed
        ? `知识库已更新 · 版本 ${result.knowledge_version}`
        : "当前对话没有新知识需要保存。",
      type: result.changed ? "success" : "info",
      duration: 3000,
    });
  } catch {
    ElMessage.error("保存失败，请稍后重试。");
  } finally {
    extracting.value = false;
  }
};

onMounted(bootstrap);

watch(
  () => route.query.seed,
  () => hydrateCorrectionFromRoute(),
);

watch(
  () => route.query.session,
  async (newId) => {
    if (!newId) return;
    const id = Number(newId);
    const found = chatStore.sessions.find((s) => s.id === id);
    if (found && found.id !== session.value?.id) {
      session.value = found;
      await chatStore.loadMessages(id);
      await scrollToBottom();
    }
  },
);
</script>

<style scoped>
.chat-panel {
  display: grid;
  grid-template-rows: 1fr auto;
  min-height: 72vh;
  padding: 20px;
}

.chat-log {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-bottom: 16px;
  max-height: calc(72vh - 160px);
  overflow-y: auto;
}

.chat-form {
  border-top: 1px solid rgba(13, 148, 136, 0.1);
  padding-top: 16px;
}

.chat-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.focus-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 0 4px;
  border-top: 1px solid rgba(13, 148, 136, 0.08);
}

.focus-chip {
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid rgba(13, 148, 136, 0.2);
  background: rgba(255, 255, 255, 0.7);
  color: var(--aa-text-soft);
  font-size: 0.88rem;
  cursor: pointer;
  user-select: none;
  transition: all 180ms ease;
}

.focus-chip--active {
  background: rgba(13, 148, 136, 0.12);
  border-color: var(--aa-primary);
  color: var(--aa-primary-deep);
  font-weight: 600;
}

.ai-name-badge {
  display: inline-flex;
  align-items: center;
  margin-left: 10px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(13, 148, 136, 0.1);
  color: var(--aa-primary-deep);
  font-size: 0.85rem;
}
</style>
