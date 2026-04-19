<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">试卷管理</span>
        <h2 class="page-title">{{ classInfo?.name || "试卷管理" }}</h2>
        <p class="page-subtitle">为全班学习伙伴统一创建选择题并发起后台异步测试。这里调用的也是每个学生当前那一份 Teach 形成的知识库。</p>
      </div>
      <el-button type="primary" @click="paperDialog = true">创建试卷</el-button>
    </header>

    <section class="soft-grid two-col">
      <article class="section-card" style="padding: 20px">
        <h3>试卷列表</h3>
        <div v-if="!papers.length" class="empty-state">还没有试卷。先创建一个。</div>
        <div v-else class="surface-stack">
          <article v-for="paper in papers" :key="paper.id" class="section-card" style="padding: 16px">
            <div class="page-header" style="margin-bottom: 0">
              <div>
                <strong>{{ paper.title }}</strong>
                <p class="muted">创建于 {{ new Date(paper.created_at).toLocaleString("zh-CN") }}</p>
              </div>
              <div class="hero-actions">
                <el-button plain @click="selectPaper(paper)">编辑题目</el-button>
                <el-button plain @click="viewResults(paper)">查看结果</el-button>
                <el-button type="warning" @click="runPaper(paper)">执行测试</el-button>
              </div>
            </div>
          </article>
        </div>
      </article>

      <article class="section-card" style="padding: 20px">
        <h3>{{ activePaper ? `编辑题目 · ${activePaper.title}` : "选择一张试卷开始编辑" }}</h3>
        <el-form v-if="activePaper" label-position="top" @submit.prevent="submitQuestion">
          <el-form-item label="题目">
            <el-input v-model="question.question_text" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" />
          </el-form-item>
          <div class="soft-grid two-col">
            <el-form-item label="A"><el-input v-model="question.option_a" /></el-form-item>
            <el-form-item label="B"><el-input v-model="question.option_b" /></el-form-item>
            <el-form-item label="C"><el-input v-model="question.option_c" /></el-form-item>
            <el-form-item label="D"><el-input v-model="question.option_d" /></el-form-item>
          </div>
          <el-form-item label="正确答案" style="max-width: 200px">
            <el-select v-model="question.correct_answer" class="full-width">
              <el-option label="A" value="A" />
              <el-option label="B" value="B" />
              <el-option label="C" value="C" />
              <el-option label="D" value="D" />
            </el-select>
          </el-form-item>
          <el-button type="primary" native-type="submit">添加题目</el-button>
        </el-form>

        <el-table v-if="questions.length" :data="questions" style="margin-top: 16px">
          <el-table-column label="序号" width="70" type="index" />
          <el-table-column prop="question_text" label="题目" show-overflow-tooltip />
          <el-table-column prop="correct_answer" label="答案" width="80" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button text type="danger" @click="removeQuestion(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </article>
    </section>

    <el-dialog v-model="paperDialog" title="创建试卷" width="420px">
      <el-form label-position="top">
        <el-form-item label="试卷标题">
          <el-input v-model.trim="paperTitle" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="paperDialog = false">取消</el-button>
        <el-button type="primary" @click="submitPaper">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import { fetchClassDetail } from "@/api/classes";
import { addQuestion, createPaper, deleteQuestion, executePaper, fetchPapers } from "@/api/tests";

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
});

const router = useRouter();
const classInfo = ref(null);
const papers = ref([]);
const questions = ref([]);
const activePaper = ref(null);
const paperDialog = ref(false);
const paperTitle = ref("");
const question = reactive({
  question_text: "",
  option_a: "",
  option_b: "",
  option_c: "",
  option_d: "",
  correct_answer: "A",
});

const load = async () => {
  classInfo.value = await fetchClassDetail(props.classId);
  papers.value = await fetchPapers({ class_id: props.classId });
};

const selectPaper = (paper) => {
  activePaper.value = paper;
  questions.value = paper.questions || [];
};

const submitPaper = async () => {
  try {
    const paper = await createPaper({ class_id: Number(props.classId), title: paperTitle.value });
    papers.value.unshift({ ...paper, questions: [] });
    paperDialog.value = false;
    paperTitle.value = "";
    selectPaper(papers.value[0]);
    ElMessage.success("试卷已创建。");
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "创建试卷失败。");
  }
};

const submitQuestion = async () => {
  try {
    const added = await addQuestion(activePaper.value.id, question);
    questions.value = [...questions.value, added].sort((left, right) => left.sort_order - right.sort_order);
    activePaper.value.questions = questions.value;
    Object.assign(question, {
      question_text: "",
      option_a: "",
      option_b: "",
      option_c: "",
      option_d: "",
      correct_answer: "A",
    });
    ElMessage.success("题目已添加。");
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "添加题目失败。");
  }
};

const removeQuestion = async (row) => {
  try {
    await deleteQuestion(row.id);
    questions.value = questions.value.filter((item) => item.id !== row.id);
    ElMessage.success("题目已删除。");
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "删除失败。");
  }
};

const viewResults = (paper) => {
  router.push({ name: "teacher-test-results", params: { classId: props.classId }, query: { paperId: paper.id } });
};

const runPaper = async (paper) => {
  try {
    const run = await executePaper(paper.id);
    ElMessage.success("测试任务已进入后台队列。");
    await router.push({ name: "teacher-test-results", params: { classId: props.classId }, query: { paperId: paper.id, runId: run.id } });
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "执行失败。");
  }
};

onMounted(load);
</script>
