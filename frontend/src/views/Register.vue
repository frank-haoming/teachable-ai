<template>
  <div class="auth-page">
    <section class="auth-card glass-card">
      <BrandLockup />
      <div>
        <span class="eyebrow">注册</span>
        <h1 class="page-title">创建你的 Apprentice AI 账号</h1>
        <p class="page-subtitle">学生可通过班级邀请码加入课堂；教师需要教师注册码。</p>
      </div>
      <el-form label-position="top" @submit.prevent="handleRegister">
        <div class="soft-grid two-col">
          <el-form-item label="用户名">
            <el-input v-model.trim="form.username" autocomplete="username" />
          </el-form-item>
          <el-form-item label="显示名称">
            <el-input v-model.trim="form.display_name" />
          </el-form-item>
        </div>
        <div class="soft-grid two-col">
          <el-form-item label="密码">
            <el-input v-model="form.password" show-password type="password" autocomplete="new-password" />
          </el-form-item>
          <el-form-item label="身份">
            <el-select v-model="form.role" class="full-width">
              <el-option label="学生" value="student" />
              <el-option label="教师" value="teacher" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item v-if="form.role === 'student'" label="班级邀请码（可选）">
          <el-input v-model.trim="form.invite_code" />
        </el-form-item>
        <el-form-item v-if="form.role === 'teacher'" label="教师注册码">
          <el-input v-model.trim="form.teacher_reg_code" />
        </el-form-item>
        <el-button class="full-width" type="primary" :loading="authStore.loading" native-type="submit">
          注册并进入平台
        </el-button>
      </el-form>
      <div class="auth-footer">
        <span class="muted">已有账号？</span>
        <router-link :to="{ name: 'login' }">去登录</router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import BrandLockup from "@/components/BrandLockup.vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const form = reactive({
  username: "",
  password: "",
  display_name: "",
  role: "student",
  invite_code: route.query.code || "",
  teacher_reg_code: "",
});

const handleRegister = async () => {
  try {
    const result = await authStore.register(form);
    await router.push(result.user.role === "teacher" ? { name: "teacher-dashboard" } : { name: "student-dashboard" });
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "注册失败。");
  }
};
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}

.auth-card {
  width: min(680px, 100%);
  padding: 28px;
  display: grid;
  gap: 20px;
}

.auth-footer {
  display: flex;
  gap: 8px;
}
</style>

