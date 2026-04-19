<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">Teach 区</span>
        <h2 class="page-title">{{ classInfo?.name || "教学对话" }}</h2>
        <p class="page-subtitle">
          这里的每条学生消息都会触发知识提取。Teach 区以外的测试不会写入记忆。
          <span v-if="aiName" class="ai-name-badge">当前对象：{{ aiName }}</span>
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
          <div class="chat-log__stack">
            <template v-if="messages.length">
              <ChatBubble
                v-for="message in messages"
                :key="message.id"
                :message="message"
                :ai-name="aiName"
              />
            </template>
            <div v-else class="empty-state">先告诉 {{ aiName || "这位同学" }} 一条规则、一个例句，或者你认为最容易混淆的点。</div>
          </div>
        </div>
        <div class="composer-shell">
          <div class="focus-chips">
            <span class="scope-label">本轮聚焦</span>
            <button
              v-for="topic in focusTopics"
              :key="topic"
              type="button"
              class="focus-chip"
              :class="{ 'focus-chip--active': activeFocus === topic }"
              @click="toggleFocus(topic)"
            >{{ topic }}</button>
          </div>
          <p class="focus-caption">当前讨论聚焦于：<strong>{{ activeFocus }}</strong>。</p>
          <el-form class="chat-form" @submit.prevent="submitMessage">
            <el-form-item label="教学输入">
              <el-input
                v-model="draft"
                type="textarea"
                :autosize="{ minRows: 4, maxRows: 7 }"
                :placeholder="inputPlaceholder"
                @keydown.ctrl.enter.prevent="submitMessage"
              />
            </el-form-item>
            <div class="chat-actions">
              <el-button plain @click="draft = correctionSeed">填入纠正提示</el-button>
              <el-button plain :loading="extracting" :disabled="chatStore.loading" @click="saveMemory">保存记忆</el-button>
              <el-button type="primary" :loading="chatStore.loading" native-type="submit">发送并教学</el-button>
            </div>
          </el-form>
        </div>
      </section>

      <KnowledgePanel :items="knowledgeItems" @refresh="loadKnowledge" @correct="seedCorrection" />
    </div>

    <!-- AI Naming Dialog -->
    <el-dialog v-model="nameDialog" title="给你的 AI 起名" width="380px">
      <p class="muted" style="margin-bottom: 16px">为这个班级里的学习伙伴起一个专属名字吧（如"小明"），系统会自动加上"同学"。</p>
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
import { manualExtract, renameClassAi } from "@/api/chat";
import { fetchFlatKnowledge } from "@/api/knowledge";
import ChatBubble from "@/components/ChatBubble.vue";
import KnowledgePanel from "@/components/KnowledgePanel.vue";
import { DEFAULT_KNOWLEDGE_FOCUSES, resolveKnowledgeFocuses } from "@/constants/classScope";
import { useAuthStore } from "@/stores/auth";
import { useChatStore } from "@/stores/chat";

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
});

// Keys are scoped by both userId and classId so students on the same device don't bleed into each other
const AI_NAME_KEY = (uid, cid) => `ai_name_${uid}_${cid}`;
const TEACH_FOCUS_KEY = (uid, cid) => `teach_focus_${uid}_${cid}`;

const authStore = useAuthStore();
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
const aiName = ref(localStorage.getItem(AI_NAME_KEY(authStore.user?.id, props.classId)) || "");
const activeFocus = ref("通用");
const extracting = ref(false);

const focusTopics = computed(() =>
  resolveKnowledgeFocuses(classInfo.value?.knowledge_focuses?.length ? classInfo.value.knowledge_focuses : DEFAULT_KNOWLEDGE_FOCUSES),
);

const messages = computed(() => chatStore.messagesBySession[session.value?.id] || []);
const inputPlaceholder = computed(() => {
  const focusHint = activeFocus.value && activeFocus.value !== "通用" ? `围绕“${activeFocus.value}”来教，` : "";
  return `例如：${focusHint}宾语从句常作动词的宾语；I think that he is honest. 这里 that 可以省略。Ctrl+Enter 发送`;
});

const syncFocusSelection = () => {
  // Only restore from localStorage if the saved value is still in the current topic list.
  // If it's not (e.g. teacher changed the focuses), fall back silently without overwriting storage.
  const saved = localStorage.getItem(TEACH_FOCUS_KEY(authStore.user?.id, props.classId)) || "通用";
  activeFocus.value = focusTopics.value.includes(saved) ? saved : (focusTopics.value[0] || "通用");
};

const toggleFocus = (topic) => {
  activeFocus.value = topic;
  localStorage.setItem(TEACH_FOCUS_KEY(authStore.user?.id, props.classId), topic);
};

const scrollToBottom = async () => {
  await nextTick();
  if (chatLogRef.value) {
    chatLogRef.value.scrollTo({
      top: chatLogRef.value.scrollHeight,
      behavior: "smooth",
    });
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
  syncFocusSelection();
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
  localStorage.setItem(AI_NAME_KEY(authStore.user?.id, props.classId), full);
  nameDialog.value = false;
  // Bulk-rename all teach sessions for this class so future sessions use the same name
  try {
    await renameClassAi(Number(props.classId), full);
  } catch {
    // non-critical: name is still stored in localStorage
  }
  ElMessage.success(`已将学习伙伴命名为"${full}"。`);
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
    await router.replace({ name: route.name, params: route.params, query: { session: newSession.id } });
  } catch {
    // cancelled
  }
};

const submitMessage = async () => {
  if (!draft.value.trim() || chatStore.loading) return;
  try {
    const focus = activeFocus.value && activeFocus.value !== "通用" ? activeFocus.value : null;
    const result = await chatStore.pushMessage({
      session_id: session.value.id,
      content: draft.value,
      focus,
    });
    draft.value = "";
    await loadKnowledge();
    await scrollToBottom();
    if (result?.knowledge_changed) {
      ElNotification({
        title: `${aiName.value || "这位同学"} 记住了新知识`,
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
  focusTopics,
  () => syncFocusSelection(),
);

watch(
  () => route.query.seed,
  () => hydrateCorrectionFromRoute(),
);

watch(
  () => route.query.session,
  async (newId) => {
    if (!newId) return;
    const id = Number(newId);
    let found = chatStore.sessions.find((s) => s.id === id);
    if (!found) {
      await chatStore.loadSessions({ class_id: Number(props.classId), session_type: "teach" });
      found = chatStore.sessions.find((s) => s.id === id);
    }
    if (found && found.id !== session.value?.id) {
      session.value = found;
      await chatStore.loadMessages(id);
      await scrollToBottom();
    }
  },
);
</script>

<style scoped>
.scope-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--aa-text-soft);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 72vh;
  padding: 20px;
}

.chat-log {
  display: flex;
  flex: 1;
  min-height: 280px;
  max-height: calc(72vh - 210px);
  overflow-y: auto;
  padding-right: 6px;
}

.chat-log__stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
  margin-top: auto;
}

.composer-shell {
  padding: 16px 18px 18px;
  border-radius: 22px;
  border: 1px solid rgba(13, 148, 136, 0.12);
  background: linear-gradient(180deg, rgba(244, 251, 249, 0.96) 0%, rgba(255, 255, 255, 0.96) 100%);
}

.chat-form {
  padding-top: 8px;
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
  align-items: center;
}

.focus-chip {
  appearance: none;
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid rgba(13, 148, 136, 0.2);
  background: rgba(255, 255, 255, 0.9);
  color: var(--aa-text-soft);
  font-size: 0.88rem;
  transition: all 180ms ease;
}

.focus-chip--active {
  background: rgba(13, 148, 136, 0.12);
  border-color: var(--aa-primary);
  color: var(--aa-primary-deep);
  font-weight: 600;
}

.focus-caption {
  margin: 8px 0 2px;
  color: var(--aa-text-soft);
  font-size: 0.88rem;
  line-height: 1.6;
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
