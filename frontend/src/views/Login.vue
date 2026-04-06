<template>
  <div class="auth-page">
    <section class="auth-card glass-card">
      <BrandLockup />
      <div>
        <span class="eyebrow">登录</span>
        <h1 class="page-title">回到你的 Apprentice AI 空间</h1>
        <p class="page-subtitle">登录后会根据你的身份进入学生端或教师端。</p>
      </div>
      <el-form label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="用户名">
          <el-input v-model.trim="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" show-password type="password" autocomplete="current-password" />
        </el-form-item>
        <el-button class="full-width" type="primary" :loading="authStore.loading" native-type="submit">
          登录
        </el-button>
      </el-form>
      <div class="auth-footer">
        <span class="muted">还没有账号？</span>
        <router-link :to="{ name: 'register' }">去注册</router-link>
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
});

const handleLogin = async () => {
  try {
    const result = await authStore.login(form);
    const fallback = result.user.role === "teacher" ? { name: "teacher-dashboard" } : { name: "student-dashboard" };
    await router.push(route.query.redirect || fallback);
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "登录失败。");
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
  width: min(560px, 100%);
  padding: 28px;
  display: grid;
  gap: 20px;
}

.auth-footer {
  display: flex;
  gap: 8px;
}
</style>

