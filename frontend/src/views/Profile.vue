<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">账号设置</span>
        <h2 class="page-title">个人资料</h2>
        <p class="page-subtitle">修改显示名称或登录密码。用户名不可更改。</p>
      </div>
    </header>

    <div class="soft-grid two-col">
      <article class="section-card" style="padding: 28px">
        <h3>修改显示名称</h3>
        <el-form label-position="top" style="margin-top: 16px" @submit.prevent="saveDisplayName">
          <el-form-item label="当前用户名">
            <el-input :value="authStore.user?.username" disabled />
          </el-form-item>
          <el-form-item label="新的显示名称">
            <el-input v-model.trim="displayName" placeholder="输入新的显示名称" />
          </el-form-item>
          <el-button type="primary" :loading="authStore.loading" native-type="submit">保存名称</el-button>
        </el-form>
      </article>

      <article class="section-card" style="padding: 28px">
        <h3>修改密码</h3>
        <el-form label-position="top" style="margin-top: 16px" @submit.prevent="savePassword">
          <el-form-item label="当前密码">
            <el-input v-model="currentPassword" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="newPassword" type="password" show-password placeholder="至少 6 位" />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="confirmPassword" type="password" show-password />
          </el-form-item>
          <el-button type="primary" :loading="authStore.loading" native-type="submit">更新密码</el-button>
        </el-form>
      </article>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";

import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const displayName = ref(authStore.user?.display_name || "");
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");

const saveDisplayName = async () => {
  if (!displayName.value) return;
  try {
    await authStore.updateProfile({ display_name: displayName.value });
    ElMessage.success("显示名称已更新。");
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "更新失败。");
  }
};

const savePassword = async () => {
  if (!currentPassword.value || !newPassword.value) return;
  if (newPassword.value !== confirmPassword.value) {
    ElMessage.error("两次输入的新密码不一致。");
    return;
  }
  try {
    await authStore.updateProfile({ current_password: currentPassword.value, new_password: newPassword.value });
    ElMessage.success("密码已更新，请重新登录。");
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "更新失败。");
  }
};
</script>
