<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">测试结果</span>
        <h2 class="page-title">{{ classInfo?.name || "结果页" }}</h2>
        <p class="page-subtitle">查看全班学习伙伴的分数、每题作答和后台任务进度。</p>
      </div>
      <router-link :to="{ name: 'teacher-test-manage', params: { classId } }">
        <el-button plain>返回试卷管理</el-button>
      </router-link>
    </header>

    <section class="soft-grid two-col">
      <article class="section-card metric-card">
        <h3>任务状态</h3>
        <strong>{{ run?.status || "未选择" }}</strong>
        <p class="muted">{{ run ? `${run.progress_completed}/${run.progress_total} 名学生已完成` : "创建或选择一场测试运行以查看进度。" }}</p>
      </article>
      <article class="section-card metric-card">
        <h3>当前试卷</h3>
        <strong>{{ activePaper?.title || "未选择" }}</strong>
        <p class="muted">切换试卷可查看不同测试结果。</p>
      </article>
    </section>

    <section class="section-card" style="padding: 20px">
      <el-select v-model="selectedPaperId" class="full-width" placeholder="选择试卷" @change="loadResults">
        <el-option v-for="paper in papers" :key="paper.id" :label="paper.title" :value="paper.id" />
      </el-select>
      <el-table v-if="results.length" :data="results" style="margin-top: 16px">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="result-expand">
              <div
                v-for="item in row.detail?.items || []"
                :key="item.question_id"
                class="result-item"
              >
                <div class="result-item__meta">
                  <span class="data-chip" :class="item.is_correct ? 'is-correct' : 'is-wrong'">
                    {{ item.is_correct ? '✓ 正确' : '✗ 错误' }}
                  </span>
                  <span class="muted">Q{{ item.question_id }}</span>
                </div>
                <p><strong>作答选择：{{ item.ai_answer }}</strong>　正确答案：{{ item.correct_answer }}</p>
                <p class="muted result-reasoning">{{ item.reasoning }}</p>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="student_name" label="学生" />
        <el-table-column label="得分" width="120">
          <template #default="{ row }">{{ row.score }}/{{ row.total }}</template>
        </el-table-column>
      </el-table>
      <div v-else class="empty-state">当前没有测试结果。先在试卷管理页执行一次全班测试。</div>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { fetchClassDetail } from "@/api/classes";
import { fetchPapers, fetchResults, fetchRun } from "@/api/tests";

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
});

const route = useRoute();
const classInfo = ref(null);
const papers = ref([]);
const results = ref([]);
const run = ref(null);
const selectedPaperId = ref(Number(route.query.paperId) || null);
let pollHandle = null;

const activePaper = computed(() => papers.value.find((paper) => paper.id === selectedPaperId.value) || null);

const loadResults = async () => {
  if (!selectedPaperId.value) return;
  results.value = await fetchResults(selectedPaperId.value, route.query.runId ? { run_id: route.query.runId } : {});
};

const startPolling = () => {
  if (!route.query.runId) return;
  clearInterval(pollHandle);
  if (!run.value || ["completed", "failed"].includes(run.value.status)) {
    return;
  }
  pollHandle = setInterval(async () => {
    run.value = await fetchRun(route.query.runId);
    await loadResults();
    if (["completed", "failed"].includes(run.value.status)) {
      clearInterval(pollHandle);
    }
  }, 2500);
};

const load = async () => {
  classInfo.value = await fetchClassDetail(props.classId);
  papers.value = await fetchPapers({ class_id: props.classId });
  if (!selectedPaperId.value && papers.value.length) {
    selectedPaperId.value = papers.value[0].id;
  }
  if (route.query.runId) {
    run.value = await fetchRun(route.query.runId);
  }
  await loadResults();
  startPolling();
};

onMounted(load);
onBeforeUnmount(() => clearInterval(pollHandle));
</script>

<style scoped>
.result-expand {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-item {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(13, 148, 136, 0.1);
  background: rgba(255, 255, 255, 0.7);
}

.result-item__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.result-item p {
  margin: 4px 0;
  font-size: 0.95rem;
}

.result-reasoning {
  font-size: 0.88rem;
  line-height: 1.6;
}
</style>
