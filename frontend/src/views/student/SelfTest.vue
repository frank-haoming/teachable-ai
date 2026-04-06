<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">学生自测</span>
        <h2 class="page-title">{{ classInfo?.name || "自测区" }}</h2>
        <p class="page-subtitle">这里的对话和选择题测试都会保存历史，但不会写入 AI 记忆。</p>
      </div>
      <router-link :to="{ name: 'student-teach', params: { classId } }">
        <el-button plain>回到 Teach</el-button>
      </router-link>
    </header>

    <div class="split-layout">
      <section class="section-card test-panel">
        <div class="surface-stack">
          <div>
            <span class="eyebrow">自由问答</span>
            <h3>问 AI 一个没把握的问题，看看它会怎么回答。</h3>
          </div>
          <div class="chat-log">
            <ChatBubble v-for="message in freeMessages" :key="message.id" :message="message" />
          </div>
          <el-form @submit.prevent="submitFree">
            <el-form-item label="自由问题">
              <el-input v-model="freeDraft" type="textarea" :autosize="{ minRows: 3, maxRows: 5 }" />
            </el-form-item>
            <el-button type="primary" :loading="chatStore.loading" native-type="submit">发送自由测试</el-button>
          </el-form>
        </div>
      </section>

      <section class="section-card test-panel">
        <div class="surface-stack">
          <div>
            <span class="eyebrow">自建选择题</span>
            <h3>学生自己出题，观察 AI 会选哪个选项。</h3>
          </div>
          <div class="chat-log">
            <ChatBubble v-for="message in mcqMessages" :key="message.id" :message="message" />
          </div>
          <el-form label-position="top" @submit.prevent="submitMcq">
            <el-form-item label="题目">
              <el-input v-model="mcq.question_text" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" />
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
import { computed, onMounted, reactive, ref } from "vue";
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
const mcq = reactive({
  question_text: "",
  option_a: "",
  option_b: "",
  option_c: "",
  option_d: "",
});

const freeMessages = computed(() => chatStore.messagesBySession[freeSession.value?.id] || []);
const mcqMessages = computed(() => chatStore.messagesBySession[mcqSession.value?.id] || []);

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
};

const submitFree = async () => {
  if (!freeDraft.value.trim()) return;
  try {
    await chatStore.pushMessage({
      session_id: freeSession.value.id,
      content: freeDraft.value,
    });
    freeDraft.value = "";
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "发送失败。");
  }
};

const submitMcq = async () => {
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

.chat-log {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 220px;
}
</style>

