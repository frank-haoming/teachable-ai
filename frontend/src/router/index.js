import { createRouter, createWebHistory } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const Landing = () => import("@/views/Landing.vue");
const Login = () => import("@/views/Login.vue");
const Register = () => import("@/views/Register.vue");
const StudentDashboard = () => import("@/views/student/Dashboard.vue");
const TeachChat = () => import("@/views/student/TeachChat.vue");
const KnowledgeView = () => import("@/views/student/KnowledgeView.vue");
const SelfTest = () => import("@/views/student/SelfTest.vue");
const TeacherDashboard = () => import("@/views/teacher/Dashboard.vue");
const ClassManage = () => import("@/views/teacher/ClassManage.vue");
const TestManage = () => import("@/views/teacher/TestManage.vue");
const TestResults = () => import("@/views/teacher/TestResults.vue");
const Analytics = () => import("@/views/teacher/Analytics.vue");
const StudentDetail = () => import("@/views/teacher/StudentDetail.vue");
const Profile = () => import("@/views/Profile.vue");

const routes = [
  { path: "/", name: "landing", component: Landing },
  { path: "/login", name: "login", component: Login },
  { path: "/register", name: "register", component: Register },
  {
    path: "/student",
    name: "student-dashboard",
    component: StudentDashboard,
    meta: { layout: "app", requiresAuth: true, roles: ["student"] },
  },
  {
    path: "/student/class/:classId/teach",
    name: "student-teach",
    component: TeachChat,
    props: true,
    meta: { layout: "app", requiresAuth: true, roles: ["student"] },
  },
  {
    path: "/student/class/:classId/knowledge",
    name: "student-knowledge",
    component: KnowledgeView,
    props: true,
    meta: { layout: "app", requiresAuth: true, roles: ["student"] },
  },
  {
    path: "/student/class/:classId/self-test",
    name: "student-self-test",
    component: SelfTest,
    props: true,
    meta: { layout: "app", requiresAuth: true, roles: ["student"] },
  },
  {
    path: "/teacher",
    name: "teacher-dashboard",
    component: TeacherDashboard,
    meta: { layout: "app", requiresAuth: true, roles: ["teacher"] },
  },
  {
    path: "/teacher/class/:classId",
    name: "teacher-class-manage",
    component: ClassManage,
    props: true,
    meta: { layout: "app", requiresAuth: true, roles: ["teacher"] },
  },
  {
    path: "/teacher/class/:classId/tests",
    name: "teacher-test-manage",
    component: TestManage,
    props: true,
    meta: { layout: "app", requiresAuth: true, roles: ["teacher"] },
  },
  {
    path: "/teacher/class/:classId/results",
    name: "teacher-test-results",
    component: TestResults,
    props: true,
    meta: { layout: "app", requiresAuth: true, roles: ["teacher"] },
  },
  {
    path: "/teacher/class/:classId/analytics",
    name: "teacher-analytics",
    component: Analytics,
    props: true,
    meta: { layout: "app", requiresAuth: true, roles: ["teacher"] },
  },
  {
    path: "/teacher/class/:classId/student/:studentId",
    name: "teacher-student-detail",
    component: StudentDetail,
    props: true,
    meta: { layout: "app", requiresAuth: true, roles: ["teacher"] },
  },
  {
    path: "/profile",
    name: "profile",
    component: Profile,
    meta: { layout: "app", requiresAuth: true, roles: ["teacher", "student"] },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  if (authStore.token && !authStore.user) {
    await authStore.hydrate();
  }
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (to.meta.roles && authStore.user && !to.meta.roles.includes(authStore.user.role)) {
    return authStore.user.role === "teacher" ? { name: "teacher-dashboard" } : { name: "student-dashboard" };
  }
  if ((to.name === "login" || to.name === "register") && authStore.isAuthenticated) {
    return authStore.user.role === "teacher" ? { name: "teacher-dashboard" } : { name: "student-dashboard" };
  }
  return true;
});

export default router;
