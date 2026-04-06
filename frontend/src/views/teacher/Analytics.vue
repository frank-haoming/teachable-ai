<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">学习分析</span>
        <h2 class="page-title">{{ classInfo?.name || "学习分析" }}</h2>
        <p class="page-subtitle">从班级层面的知识覆盖率到单个学生的修正次数和测试分数，都在这里汇总。</p>
      </div>
      <router-link :to="{ name: 'teacher-class-manage', params: { classId } }">
        <el-button plain>返回班级</el-button>
      </router-link>
    </header>

    <section class="soft-grid three-col">
      <article class="section-card metric-card">
        <h3>学生人数</h3>
        <strong>{{ overview?.student_count || 0 }}</strong>
      </article>
      <article class="section-card metric-card">
        <h3>平均知识条目</h3>
        <strong>{{ overview?.average_knowledge_items || 0 }}</strong>
      </article>
      <article class="section-card metric-card">
        <h3>最近测试均分</h3>
        <strong>{{ overview?.latest_test_average ?? "--" }}</strong>
      </article>
    </section>

    <section class="soft-grid two-col">
      <article class="section-card" style="padding: 20px">
        <h3>Topic 覆盖率</h3>
        <div v-if="overview" class="surface-stack">
          <div v-for="(count, topic) in overview.topic_coverage" :key="topic" class="coverage-row">
            <span class="coverage-label">{{ TOPIC_LABELS[topic] || topic }}</span>
            <el-progress
              :percentage="overview.student_count ? Math.round((count / overview.student_count) * 100) : 0"
              :format="() => `${count} 人`"
              :stroke-width="10"
              color="var(--aa-primary)"
            />
          </div>
        </div>
      </article>

      <article class="section-card" style="padding: 20px">
        <h3>学生维度概览</h3>
        <el-table :data="students">
          <el-table-column prop="student_name" label="学生" />
          <el-table-column prop="knowledge_items" label="知识数" width="100" />
          <el-table-column label="最近测试" width="160">
            <template #default="{ row }">
              <el-progress
                v-if="row.latest_total"
                :percentage="Math.round((row.latest_score / row.latest_total) * 100)"
                :format="() => `${row.latest_score}/${row.latest_total}`"
                :stroke-width="8"
                :color="row.latest_score / row.latest_total >= 0.7 ? '#0d9488' : '#f97316'"
              />
              <span v-else class="muted">--</span>
            </template>
          </el-table-column>
          <el-table-column prop="corrections" label="修正次数" width="120" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <router-link :to="{ name: 'teacher-student-detail', params: { classId, studentId: row.student_id } }">
                <el-button text>查看</el-button>
              </router-link>
            </template>
          </el-table-column>
        </el-table>
      </article>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";

import { fetchClassDetail } from "@/api/classes";
import { fetchClassOverview, fetchClassStudents } from "@/api/analytics";

const TOPIC_LABELS = {
  subject_clause: "主语从句",
  object_clause: "宾语从句",
  predicative_clause: "表语从句",
  appositive_clause: "同位语从句",
  general: "通用知识",
  other: "偏好与其他",
};

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
});

const classInfo = ref(null);
const overview = ref(null);
const students = ref([]);

const load = async () => {
  classInfo.value = await fetchClassDetail(props.classId);
  overview.value = await fetchClassOverview(props.classId);
  students.value = await fetchClassStudents(props.classId);
};

onMounted(load);
</script>

<style scoped>
.coverage-row {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 12px;
  align-items: center;
  padding: 8px 0;
}

.coverage-label {
  font-size: 0.9rem;
  color: var(--aa-text-soft);
}
</style>

