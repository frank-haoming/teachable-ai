<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">教师首页</span>
        <h2 class="page-title">班级、测试和学习分析都从这里开始。</h2>
        <p class="page-subtitle">教师可以创建班级、生成邀请码、统一出卷测试，并查看学生教出来的 AI 记忆。</p>
      </div>
      <el-button type="primary" @click="openCreate">创建新班级</el-button>
    </header>

    <section class="soft-grid three-col">
      <article v-for="item in classes" :key="item.id" class="section-card metric-card">
        <div class="class-card__header">
          <h3>{{ item.name }}</h3>
          <span v-if="item.subject_description" class="subject-badge">{{ item.subject_description }}</span>
        </div>
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

        <el-form-item>
          <template #label>
            <span>课程主题 <span class="muted">（可选，帮助 AI 理解学习范围）</span></span>
          </template>
          <div class="preset-chips">
            <span
              v-for="preset in subjectPresets"
              :key="preset.value"
              class="preset-chip"
              :class="{ active: subjectDescription === preset.value }"
              @click="togglePreset(preset.value)"
            >{{ preset.label }}</span>
          </div>
          <el-input
            v-model="subjectDescription"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            placeholder="例如：本课程讲授高中英语名词从句，包括主语从句、宾语从句、表语从句和同位语从句。"
            maxlength="300"
            show-word-limit
            class="subject-textarea"
          />
        </el-form-item>
      </el-form>

      <div v-if="subjectDescription" class="preview-hint">
        <span class="eyebrow">预览提示</span>
        <p>AI 学生将了解：「{{ subjectDescription }}」</p>
      </div>

      <template #footer>
        <el-button @click="createDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!className" @click="submitCreate">创建班级</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { createClass, fetchClasses } from "@/api/classes";

const classes = ref([]);
const createDialog = ref(false);
const className = ref("");
const subjectDescription = ref("");

const subjectPresets = [
  { label: "英语语法", value: "本课程讲授英语语法知识，包括名词从句、定语从句、状语从句等重要语法结构。" },
  { label: "数学", value: "本课程涵盖数学概念与定理，包括代数、几何、函数等核心知识点。" },
  { label: "物理", value: "本课程讲授高中物理，涵盖力学、电磁学、热学等基础定律与公式。" },
  { label: "编程", value: "本课程讲授编程基础，包括变量、条件、循环、函数与算法等核心概念。" },
  { label: "历史", value: "本课程讲授历史知识，包括重要历史事件、人物、时间线与因果关系。" },
  { label: "化学", value: "本课程讲授化学基础，涵盖元素、化学方程式、反应类型与化学计算。" },
  { label: "通用", value: "本课程为通识学习，AI 学生将记录并整理学生教授的各类知识点。" },
];

const openCreate = () => {
  createDialog.value = true;
};

const resetForm = () => {
  className.value = "";
  subjectDescription.value = "";
};

const togglePreset = (value) => {
  subjectDescription.value = subjectDescription.value === value ? "" : value;
};

const loadClasses = async () => {
  classes.value = await fetchClasses();
};

const submitCreate = async () => {
  if (!className.value) return;
  try {
    await createClass({
      name: className.value,
      subject_description: subjectDescription.value || null,
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
  flex-direction: column;
  gap: 6px;
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

.class-card__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 18px;
}

/* Preset chips */
.preset-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.preset-chip {
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid var(--aa-border);
  background: rgba(255, 255, 255, 0.9);
  font-size: 0.85rem;
  color: var(--aa-text-soft);
  cursor: pointer;
  transition: all 150ms ease;
  user-select: none;
}

.preset-chip:hover {
  border-color: var(--aa-primary);
  color: var(--aa-primary-deep);
  background: rgba(13, 148, 136, 0.06);
}

.preset-chip.active {
  border-color: var(--aa-primary);
  background: rgba(13, 148, 136, 0.12);
  color: var(--aa-primary-deep);
  font-weight: 500;
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
  margin: 0;
  font-size: 0.88rem;
  color: var(--aa-text-soft);
  line-height: 1.6;
}
</style>
