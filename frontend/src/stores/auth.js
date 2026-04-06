import { defineStore } from "pinia";

import { fetchMe, login as loginApi, register as registerApi, updateProfile as updateProfileApi } from "@/api/auth";

const TOKEN_KEY = "apprentice_ai_token";
const USER_KEY = "apprentice_ai_user";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY),
    user: JSON.parse(localStorage.getItem(USER_KEY) || "null"),
    loading: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
    role: (state) => state.user?.role || null,
  },
  actions: {
    persistSession(token, user) {
      this.token = token;
      this.user = user;
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    },
    clearSession() {
      this.token = null;
      this.user = null;
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    },
    async login(payload) {
      this.loading = true;
      try {
        const data = await loginApi(payload);
        this.persistSession(data.access_token, data.user);
        return data;
      } finally {
        this.loading = false;
      }
    },
    async register(payload) {
      this.loading = true;
      try {
        const data = await registerApi(payload);
        this.persistSession(data.access_token, data.user);
        return data;
      } finally {
        this.loading = false;
      }
    },
    async updateProfile(payload) {
      this.loading = true;
      try {
        const user = await updateProfileApi(payload);
        this.user = user;
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        return user;
      } finally {
        this.loading = false;
      }
    },
    async hydrate() {
      if (!this.token) {
        return null;
      }
      try {
        const user = await fetchMe();
        this.user = user;
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        return user;
      } catch (error) {
        this.clearSession();
        return null;
      }
    },
  },
});

