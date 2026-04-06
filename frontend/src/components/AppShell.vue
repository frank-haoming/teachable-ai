<template>
  <div class="app-shell">
    <aside class="app-nav glass-card">
      <BrandLockup compact />
      <nav class="nav-links" aria-label="Primary">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          class="nav-link"
          :to="item.to"
        >
          <span>{{ item.label }}</span>
          <small>{{ item.caption }}</small>
        </router-link>
      </nav>
      <div class="nav-footer">
        <router-link :to="{ name: 'profile' }" class="nav-footer__user">
          <strong>{{ authStore.user?.display_name || "未登录用户" }}</strong>
          <p>{{ authStore.user?.role === "teacher" ? "教师端" : "学生端" }} · 点击设置</p>
        </router-link>
        <el-button plain @click="logout">退出</el-button>
      </div>
    </aside>
    <main class="app-main">
      <header class="app-topbar glass-card">
        <div>
          <span class="eyebrow">Apprentice AI</span>
          <h1>{{ route.meta.roles?.[0] === "teacher" ? "教师工作台" : "学生学习空间" }}</h1>
        </div>
        <router-link v-if="authStore.user?.role === 'teacher'" :to="{ name: 'teacher-dashboard' }">班级总览</router-link>
        <router-link v-else :to="{ name: 'student-dashboard' }">我的班级</router-link>
      </header>
      <section class="app-content">
        <slot />
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";
import BrandLockup from "./BrandLockup.vue";

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const classId = computed(() => route.params.classId || null);

const navItems = computed(() => {
  const cid = classId.value;
  if (authStore.user?.role === "teacher") {
    const base = [{ to: { name: "teacher-dashboard" }, label: "班级总览", caption: "所有班级" }];
    if (cid) {
      base.push(
        { to: { name: "teacher-class-manage", params: { classId: cid } }, label: "班级管理", caption: "学生与邀请码" },
        { to: { name: "teacher-test-manage", params: { classId: cid } }, label: "试卷出题", caption: "选择题与批量测试" },
        { to: { name: "teacher-test-results", params: { classId: cid } }, label: "测试结果", caption: "分数与作答详情" },
        { to: { name: "teacher-analytics", params: { classId: cid } }, label: "学习分析", caption: "覆盖率与进度" },
      );
    }
    return base;
  }
  const base = [{ to: { name: "student-dashboard" }, label: "我的班级", caption: "班级列表" }];
  if (cid) {
    base.push(
      { to: { name: "student-teach", params: { classId: cid } }, label: "Teach 区", caption: "教 AI 学语法" },
      { to: { name: "student-knowledge", params: { classId: cid } }, label: "知识库", caption: "查看 AI 记忆" },
      { to: { name: "student-self-test", params: { classId: cid } }, label: "自测", caption: "不写入记忆的测试" },
    );
  }
  return base;
});

const logout = async () => {
  authStore.clearSession();
  await router.push({ name: "landing" });
};
</script>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 320px 1fr;
  min-height: 100vh;
}

.app-nav {
  margin: 20px;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  position: sticky;
  top: 20px;
  height: calc(100vh - 40px);
}

.nav-links {
  display: grid;
  gap: 10px;
}

.nav-link {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid transparent;
  color: var(--aa-text);
  background: rgba(255, 255, 255, 0.52);
}

.nav-link span,
.nav-link small {
  display: block;
}

.nav-link small {
  margin-top: 4px;
  color: var(--aa-text-soft);
}

.nav-link.router-link-active {
  border-color: rgba(13, 148, 136, 0.16);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 10px 24px rgba(9, 68, 62, 0.08);
}

.nav-footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(13, 148, 136, 0.1);
}

.nav-footer__user {
  color: inherit;
  text-decoration: none;
  flex: 1;
  min-width: 0;
}

.nav-footer__user strong {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-footer p,
.app-topbar p {
  margin: 4px 0 0;
  color: var(--aa-text-soft);
}

.app-topbar {
  margin: 20px 20px 0 0;
  padding: 22px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-topbar h1 {
  margin: 10px 0 0;
  font-family: "Crimson Pro", serif;
  font-size: clamp(1.8rem, 1.4rem + 1vw, 2.5rem);
}

@media (max-width: 1024px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .app-nav {
    position: static;
    margin-bottom: 0;
    height: auto;
  }

  .app-topbar {
    margin: 16px;
  }
}
</style>

