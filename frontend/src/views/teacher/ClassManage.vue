<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">班级管理</span>
        <h2 class="page-title">{{ classInfo?.name || "班级详情" }}</h2>
        <p class="page-subtitle">查看学生列表、邀请码与二维码，并快速跳转到单个学生的完整记录。</p>
      </div>
      <div class="hero-actions">
        <el-button plain @click="qrVisible = true">显示二维码</el-button>
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
        <p class="muted">所有学生都会拥有一份独立的 AI 记忆。</p>
      </article>
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

    <QrCodeModal v-model="qrVisible" :src="qrCodeUrl" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import { fetchClassDetail, getQrCodeUrl } from "@/api/classes";
import QrCodeModal from "@/components/QrCodeModal.vue";

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
});

const classInfo = ref(null);
const qrVisible = ref(false);
const qrCodeUrl = computed(() => getQrCodeUrl(props.classId));

const load = async () => {
  classInfo.value = await fetchClassDetail(props.classId);
};

onMounted(load);
</script>

