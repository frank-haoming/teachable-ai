<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">班级管理</span>
        <h2 class="page-title">{{ classInfo?.name || "班级详情" }}</h2>
        <p class="page-subtitle">查看学生列表与邀请码，调整这个班级的课程范围、知识维度与 AI 学习边界。</p>
      </div>
      <div class="hero-actions" style="display:flex;gap:10px;flex-wrap:wrap">
        <el-button plain @click="openEditScope">编辑范围</el-button>
        <router-link :to="{ name: 'teacher-test-manage', params: { classId } }">
          <el-button type="primary">去出卷</el-button>
        </router-link>
      </div>
    </header>

    <section class="soft-grid two-col">
      <article class="section-card metric-card">
        <h3>邀请码</h3>
        <strong>{{ classInfo?.invite_code || "--" }}</strong>
        <p class="muted">学生注册页支持自动填充邀请码。</p>
      </article>
      <article class="section-card metric-card">
        <h3>班级人数</h3>
        <strong>{{ classInfo?.student_count || 0 }}</strong>
        <p class="muted">所有学生都会拥有一份独立的学习伙伴知识库。</p>
      </article>
    </section>

    <section v-if="classInfo" class="section-card class-scope-card">
      <div class="class-scope-card__header">
        <div>
          <span class="eyebrow">AI 范围设定</span>
          <h3>{{ classInfo.course_topic }}</h3>
          <p class="muted">{{ classInfo.subject_description }}</p>
        </div>
      </div>

      <div class="scope-grid">
        <article class="scope-box">
          <h4>涵盖专题</h4>
          <div class="scope-chip-row">
            <span v-for="label in classInfo.covered_topic_labels || []" :key="label" class="data-chip">{{ label }}</span>
          </div>
        </article>
        <article class="scope-box">
          <h4>知识维度</h4>
          <div class="scope-chip-row">
            <span v-for="focus in classInfo.knowledge_focuses || []" :key="focus" class="data-chip">{{ focus }}</span>
          </div>
        </article>
      </div>
    </section>

    <section class="section-card" style="padding: 20px">
      <header class="page-header" style="margin-bottom: 12px">
        <div>
          <h3 style="margin: 0">学生列表</h3>
          <p class="muted" style="margin-top: 8px">点击“查看详情”进入该学生的知识、对话和测试记录。</p>
        </div>
      </header>
      <el-table :data="classInfo?.students || []">
        <el-table-column prop="display_name" label="学生姓名" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <router-link :to="{ name: 'teacher-student-detail', params: { classId, studentId: row.id } }">
              <el-button plain>查看详情</el-button>
            </router-link>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 编辑范围对话框 -->
    <el-dialog v-model="editScopeDialog" title="编辑课程范围与知识维度" width="560px">
      <el-form label-position="top">
        <el-form-item label="课程主题">
          <el-input v-model="scopeForm.course_topic" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="课程简介">
          <el-input v-model="scopeForm.subject_description" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" maxlength="300" show-word-limit />
        </el-form-item>
        <el-form-item label="涵盖专题（学生输入此处显示的专题名即可映射到对应知识桶）">
          <EditableTagField v-model="scopeForm.covered_topics" placeholder="添加专题标签" />
        </el-form-item>
        <el-form-item label="知识维度（聚焦按钮会用到这些）">
          <EditableTagField v-model="scopeForm.knowledge_focuses" placeholder="添加维度标签" :locked-values="['通用']" helper="「通用」维度不可删除，始终保留在首位。" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editScopeDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingScope" @click="saveScope">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { fetchClassDetail, updateClassConfig } from "@/api/classes";
import EditableTagField from "@/components/EditableTagField.vue";

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
});

const classInfo = ref(null);
const editScopeDialog = ref(false);
const savingScope = ref(false);
const scopeForm = reactive({
  course_topic: "",
  subject_description: "",
  covered_topics: [],
  knowledge_focuses: [],
});

const load = async () => {
  classInfo.value = await fetchClassDetail(props.classId);
};

const openEditScope = () => {
  if (!classInfo.value) return;
  scopeForm.course_topic = classInfo.value.course_topic || "";
  scopeForm.subject_description = classInfo.value.subject_description || "";
  scopeForm.covered_topics = [...(classInfo.value.covered_topics || [])];
  scopeForm.knowledge_focuses = [...(classInfo.value.knowledge_focuses || [])];
  editScopeDialog.value = true;
};

const saveScope = async () => {
  savingScope.value = true;
  try {
    await updateClassConfig(props.classId, {
      course_topic: scopeForm.course_topic,
      subject_description: scopeForm.subject_description,
      covered_topics: scopeForm.covered_topics,
      knowledge_focuses: scopeForm.knowledge_focuses,
    });
    editScopeDialog.value = false;
    await load();
    ElMessage.success("课程范围已更新，所有学生的知识库已同步。");
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "保存失败。");
  } finally {
    savingScope.value = false;
  }
};

onMounted(load);
</script>

<style scoped>
.class-scope-card {
  padding: 22px 24px;
}

.class-scope-card__header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.class-scope-card__header h3 {
  margin: 12px 0 8px;
}


.scope-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.scope-box {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(13, 148, 136, 0.1);
  background: rgba(244, 251, 249, 0.76);
}

.scope-box h4 {
  margin: 0 0 12px;
}

.scope-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 900px) {
  .class-scope-card__header,
  .scope-grid {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>
