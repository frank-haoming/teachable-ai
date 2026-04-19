<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">学生自测</span>
        <h2 class="page-title">{{ classInfo?.name || "自测区" }}</h2>
        <p class="page-subtitle">这里的对话和选择题测试都会保存历史，但不会写入学习伙伴的记忆。</p>
      </div>
      <router-link :to="{ name: 'student-teach', params: { classId } }">
        <el-button plain>回到 Teach</el-button>
      </router-link>
    </header>

    <div class="split-layout">
      <section class="section-card test-panel">
        <div class="test-panel__content">
          <div>
            <span class="eyebrow">自由问答</span>
            <h3>问 AI 一个没把握的问题，看看它会怎么回答。</h3>
          </div>
          <div ref="freeLogRef" class="chat-log">
            <div class="chat-log__stack">
              <ChatBubble v-for="message in freeMessages" :key="message.id" :message="message" />
              <div v-if="!freeMessages.length" class="empty-state compact-empty">这里会保留你的自由问答历史，方便你连续追问。</div>
            </div>
          </div>
          <el-form class="test-form" @submit.prevent="submitFree">
            <el-form-item label="自由问题">
              <el-input
                v-model="freeDraft"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 5 }"
                placeholder="例如：如果把宾语从句换成表语从句，你现在能区分吗？"
              />
            </el-form-item>
            <el-button type="primary" :loading="chatStore.loading" native-type="submit">发送自由测试</el-button>
          </el-form>
        </div>
      </section>

      <section class="section-card test-panel">
        <div class="test-panel__content">
          <div>
            <span class="eyebrow">自建选择题</span>
            <h3>学生自己出题，观察 AI 会选哪个选项。</h3>
          </div>
          <div ref="mcqLogRef" class="chat-log">
            <div class="chat-log__stack">
              <ChatBubble v-for="message in mcqMessages" :key="message.id" :message="message" />
              <div v-if="!mcqMessages.length" class="empty-state compact-empty">这里会保留你的选择题历史，便于比较它在不同题目上的表现。</div>
            </div>
          </div>
          <el-form class="test-form" label-position="top" @submit.prevent="submitMcq">
            <el-form-item label="题目">
              <el-input
                v-model="mcq.question_text"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 4 }"
                placeholder="例如：下列哪一句中，that 引导的是宾语从句？"
              />
            </el-form-item>
            <div class="soft-grid two-col">
              <el-form-item label="A">
                <el-input v-model="mcq.option_a" />
              </el-form-item>
              <el-form-item label="B">
                <el-input v-model="mcq.option_b" />
              </el-form-item>
              <el-form-item label="C">
                <el-input v-model="mcq.option_c" />
              </el-form-item>
              <el-form-item label="D">
                <el-input v-model="mcq.option_d" />
              </el-form-item>
            </div>
            <el-button type="warning" :loading="chatStore.loading" native-type="submit">让 AI 选择</el-button>
          </el-form>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { fetchClassDetail } from "@/api/classes";
import ChatBubble from "@/components/ChatBubble.vue";
import { useChatStore } from "@/stores/chat";

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
});

const chatStore = useChatStore();
const classInfo = ref(null);
const freeDraft = ref("");
const freeSession = ref(null);
const mcqSession = ref(null);
const freeLogRef = ref(null);
const mcqLogRef = ref(null);
const mcq = reactive({
  question_text: "",
  option_a: "",
  option_b: "",
  option_c: "",
  option_d: "",
});

const freeMessages = computed(() => chatStore.messagesBySession[freeSession.value?.id] || []);
const mcqMessages = computed(() => chatStore.messagesBySession[mcqSession.value?.id] || []);

const scrollLogToBottom = async (targetRef) => {
  await nextTick();
  if (!targetRef.value) return;
  targetRef.value.scrollTo({
    top: targetRef.value.scrollHeight,
    behavior: "smooth",
  });
};

const bootstrap = async () => {
  classInfo.value = await fetchClassDetail(props.classId);
  freeSession.value = await chatStore.ensureSession({
    classId: Number(props.classId),
    sessionType: "student_test_free",
    title: "Free Student Test",
  });
  mcqSession.value = await chatStore.ensureSession({
    classId: Number(props.classId),
    sessionType: "student_test_mcq",
    title: "MCQ Student Test",
  });
  await Promise.all([chatStore.loadMessages(freeSession.value.id), chatStore.loadMessages(mcqSession.value.id)]);
  await Promise.all([scrollLogToBottom(freeLogRef), scrollLogToBottom(mcqLogRef)]);
};

const submitFree = async () => {
  if (!freeDraft.value.trim()) return;
  try {
    await chatStore.pushMessage({
      session_id: freeSession.value.id,
      content: freeDraft.value,
    });
    freeDraft.value = "";
    await scrollLogToBottom(freeLogRef);
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "发送失败。");
  }
};

const submitMcq = async () => {
  if (!mcq.question_text.trim()) {
    ElMessage.warning("请先填写题目内容。");
    return;
  }
  if (!mcq.option_a.trim() || !mcq.option_b.trim() || !mcq.option_c.trim() || !mcq.option_d.trim()) {
    ElMessage.warning("请填写全部四个选项（A、B、C、D）。");
    return;
  }
  try {
    await chatStore.pushStudentMcq({
      session_id: mcqSession.value.id,
      ...mcq,
    });
    mcq.question_text = "";
    mcq.option_a = "";
    mcq.option_b = "";
    mcq.option_c = "";
    mcq.option_d = "";
    await scrollLogToBottom(mcqLogRef);
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "提交失败。");
  }
};

onMounted(bootstrap);
</script>

<style scoped>
.test-panel {
  padding: 20px;
}

.test-panel__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 70vh;
}

.chat-log {
  display: flex;
  flex: 1;
  min-height: 260px;
  max-height: 380px;
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

.test-form {
  padding-top: 10px;
  border-top: 1px solid rgba(13, 148, 136, 0.08);
}

.compact-empty {
  padding: 22px 18px;
  font-size: 0.92rem;
}
</style>
