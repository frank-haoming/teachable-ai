<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">学生首页</span>
        <h2 class="page-title">选择一个班级，继续教你的学习伙伴。</h2>
        <p class="page-subtitle">每个班级都会生成一份独立的已学知识库。Teach、自测和知识查看都围绕这份知识库展开。</p>
      </div>
      <el-button type="primary" @click="joinDialog = true">输入邀请码加入新班级</el-button>
    </header>

    <section class="soft-grid three-col">
      <article v-for="item in classes" :key="item.id" class="section-card metric-card class-card">
        <div class="class-card__header">
          <h3>{{ item.name }}</h3>
          <span class="data-chip">{{ item.course_topic || "英语名词从句" }}</span>
        </div>
        <p class="class-card__summary">{{ item.subject_description }}</p>
        <div class="class-card__chips">
          <span v-for="label in item.covered_topic_labels || []" :key="label" class="data-chip">{{ label }}</span>
        </div>
        <strong>{{ item.knowledge_item_count }}</strong>
        <p class="muted">当前已学条目</p>
        <div class="class-card__actions">
          <router-link :to="{ name: 'student-teach', params: { classId: item.id } }">
            <el-button type="primary">进入 Teach</el-button>
          </router-link>
          <router-link :to="{ name: 'student-knowledge', params: { classId: item.id } }">
            <el-button plain>知识库</el-button>
          </router-link>
          <router-link :to="{ name: 'student-self-test', params: { classId: item.id } }">
            <el-button plain>自测</el-button>
          </router-link>
        </div>
      </article>
    </section>

    <div v-if="!classes.length" class="empty-state section-card">你还没有加入任何班级。输入邀请码后即可开始教学。</div>

    <el-dialog v-model="joinDialog" title="加入班级" width="420px">
      <el-form label-position="top" @submit.prevent="submitJoin">
        <el-form-item label="邀请码">
          <el-input v-model.trim="joinCode" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="joinDialog = false">取消</el-button>
        <el-button type="primary" @click="submitJoin">加入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { fetchClasses, joinClass } from "@/api/classes";

const classes = ref([]);
const joinDialog = ref(false);
const joinCode = ref("");

const loadClasses = async () => {
  classes.value = await fetchClasses();
};

const submitJoin = async () => {
  try {
    await joinClass({ invite_code: joinCode.value });
    ElMessage.success("已加入班级。");
    joinDialog.value = false;
    joinCode.value = "";
    await loadClasses();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "加入班级失败。");
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
}

.class-card__summary {
  margin: 10px 0 12px;
  color: var(--aa-text-soft);
  line-height: 1.6;
}

.class-card__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.class-card__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 18px;
}
</style>
