<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">教师首页</span>
        <h2 class="page-title">班级、测试和学习分析都从这里开始。</h2>
        <p class="page-subtitle">教师可以创建班级、生成邀请码、统一出卷测试，并查看学生教出来的知识轨迹。Teach、自测和教师批测共用每个学生自己的同一份知识库。</p>
      </div>
      <el-button type="primary" @click="openCreate">创建新班级</el-button>
    </header>

    <section class="soft-grid three-col">
      <article v-for="item in classes" :key="item.id" class="section-card metric-card">
        <div class="class-card__header">
          <h3>{{ item.name }}</h3>
          <span class="subject-badge">{{ item.course_topic || defaultCourseTopic }}</span>
        </div>
        <p class="class-card__summary">{{ item.subject_description }}</p>
        <div class="class-card__chips">
          <span v-for="label in item.covered_topic_labels || []" :key="label" class="data-chip">{{ label }}</span>
        </div>
        <p class="class-card__focuses">跟踪维度：{{ (item.knowledge_focuses || []).join(" / ") }}</p>
        <strong>{{ item.student_count || 0 }}</strong>
        <p class="muted">当前学生人数</p>
        <div class="class-card__actions">
          <router-link :to="{ name: 'teacher-class-manage', params: { classId: item.id } }">
            <el-button type="primary">班级管理</el-button>
          </router-link>
          <router-link :to="{ name: 'teacher-test-manage', params: { classId: item.id } }">
            <el-button plain>试卷管理</el-button>
          </router-link>
          <router-link :to="{ name: 'teacher-analytics', params: { classId: item.id } }">
            <el-button plain>学习分析</el-button>
          </router-link>
        </div>
      </article>
    </section>

    <div v-if="!classes.length" class="empty-state section-card">还没有班级。先创建一个班级并分享邀请码。</div>

    <!-- Create Class Dialog -->
    <el-dialog v-model="createDialog" title="创建新班级" width="480px" @closed="resetForm">
      <el-form label-position="top" @submit.prevent="submitCreate">
        <el-form-item label="班级名称" required>
          <el-input v-model.trim="className" placeholder="如：高一英语 3 班" maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="课程主题">
          <el-input
            v-model.trim="courseTopic"
            placeholder="例如：英语名词从句总览 / 高一函数基础 / 平面向量专题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="涵盖范围说明">
          <el-input
            v-model="subjectDescription"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 5 }"
            placeholder="例如：本班重点讲授名词从句的定义、结构、引导词、语法功能及典型例句，强调四类从句的辨析。"
            maxlength="300"
            show-word-limit
            class="subject-textarea"
          />
        </el-form-item>

        <el-form-item label="涵盖专题">
          <EditableTagField
            v-model="coveredTopics"
            placeholder="输入一个专题后回车，例如：主语从句 / 函数定义域 / 二次函数图像"
            helper="这里定义这门课的知识结构分块。可以完全自定义，不限制学科。"
          />
        </el-form-item>

        <el-form-item label="知识维度">
          <EditableTagField
            v-model="knowledgeFocuses"
            :locked-values="['通用']"
            placeholder="输入一个维度后回车，例如：定义 / 方法 / 易错点 / 证明思路"
            helper="“通用”会始终保留；其他维度由教师自定义，供学生在 Teach 时聚焦。"
          />
        </el-form-item>
      </el-form>

      <div class="preview-hint">
        <span class="eyebrow">预览提示</span>
        <p>课程主题：{{ courseTopic || defaultCourseTopic }}</p>
        <p>涵盖专题：{{ selectedCoveredLabels.join("、") }}</p>
        <p>跟踪维度：{{ resolvedKnowledgeFocuses.join("、") }}</p>
        <p class="muted" style="margin-top: 8px">{{ subjectDescription || fallbackSubjectDescription }}</p>
      </div>

      <template #footer>
        <el-button @click="createDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!className" @click="submitCreate">创建班级</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { createClass, fetchClasses } from "@/api/classes";
import EditableTagField from "@/components/EditableTagField.vue";
import {
  DEFAULT_COURSE_TOPIC,
  DEFAULT_COVERED_TOPICS,
  DEFAULT_KNOWLEDGE_FOCUSES,
  resolveCoveredTopics,
  resolveKnowledgeFocuses,
} from "@/constants/classScope";

const classes = ref([]);
const createDialog = ref(false);
const className = ref("");
const courseTopic = ref(DEFAULT_COURSE_TOPIC);
const subjectDescription = ref("");
const coveredTopics = ref([...DEFAULT_COVERED_TOPICS]);
const knowledgeFocuses = ref([...DEFAULT_KNOWLEDGE_FOCUSES]);
const defaultCourseTopic = DEFAULT_COURSE_TOPIC;

const resolvedCoveredTopics = computed(() => resolveCoveredTopics(coveredTopics.value));
const selectedCoveredLabels = computed(() => resolvedCoveredTopics.value);
const resolvedKnowledgeFocuses = computed(() => resolveKnowledgeFocuses(knowledgeFocuses.value));
const fallbackSubjectDescription = computed(
  () => `本班围绕“${courseTopic.value || defaultCourseTopic}”展开，当前重点覆盖：${selectedCoveredLabels.value.join("、")}。`,
);

const openCreate = () => {
  createDialog.value = true;
};

const resetForm = () => {
  className.value = "";
  subjectDescription.value = "";
  courseTopic.value = defaultCourseTopic;
  coveredTopics.value = [...DEFAULT_COVERED_TOPICS];
  knowledgeFocuses.value = [...DEFAULT_KNOWLEDGE_FOCUSES];
};

const loadClasses = async () => {
  classes.value = await fetchClasses();
};

const submitCreate = async () => {
  if (!className.value) return;
  try {
    await createClass({
      name: className.value,
      course_topic: courseTopic.value || defaultCourseTopic,
      subject_description: subjectDescription.value || null,
      covered_topics: resolvedCoveredTopics.value,
      knowledge_focuses: resolvedKnowledgeFocuses.value,
    });
    ElMessage.success("班级已创建。");
    createDialog.value = false;
    await loadClasses();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "创建失败。");
  }
};

onMounted(loadClasses);
</script>

<style scoped>
.class-card__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
}

.subject-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(13, 148, 136, 0.08);
  border: 1px solid rgba(13, 148, 136, 0.2);
  color: var(--aa-primary-deep);
  font-size: 0.8rem;
  line-height: 1.5;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.class-card__summary {
  margin: 0 0 12px;
  color: var(--aa-text-soft);
  line-height: 1.6;
}

.class-card__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.class-card__focuses {
  margin: 0 0 14px;
  color: var(--aa-text-soft);
  font-size: 0.9rem;
}

.class-card__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 18px;
}

.subject-textarea {
  width: 100%;
}

/* Preview hint */
.preview-hint {
  margin-top: 4px;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(13, 148, 136, 0.06);
  border: 1px solid rgba(13, 148, 136, 0.15);
}

.preview-hint .eyebrow {
  display: block;
  margin-bottom: 6px;
}

.preview-hint p {
  margin: 0 0 6px;
  font-size: 0.88rem;
  color: var(--aa-text-soft);
  line-height: 1.6;
}
</style>
