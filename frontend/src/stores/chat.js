import { defineStore } from "pinia";

import { answerStudentMcq, createSession, fetchMessages, listSessions, sendMessage } from "@/api/chat";

export const useChatStore = defineStore("chat", {
  state: () => ({
    sessions: [],
    messagesBySession: {},
    loading: false,
  }),
  actions: {
    async ensureSession({ classId, sessionType, title = null, aiName = null }) {
      const existing = this.sessions.find(
        (session) => session.class_id === classId && session.session_type === sessionType,
      );
      if (existing) {
        return existing;
      }
      const session = await createSession({
        class_id: classId,
        session_type: sessionType,
        title,
        ai_name: aiName,
      });
      this.sessions.unshift(session);
      return session;
    },
    async loadSessions(params) {
      this.sessions = await listSessions(params);
      return this.sessions;
    },
    async loadMessages(sessionId) {
      this.loading = true;
      try {
        const messages = await fetchMessages(sessionId);
        this.messagesBySession[sessionId] = messages;
        return messages;
      } finally {
        this.loading = false;
      }
    },
    async pushMessage(payload) {
      this.loading = true;
      try {
        const response = await sendMessage(payload);
        const stack = this.messagesBySession[payload.session_id] || [];
        this.messagesBySession[payload.session_id] = [...stack, response.user_message, response.assistant_message];
        return response;
      } finally {
        this.loading = false;
      }
    },
    async pushStudentMcq(payload) {
      this.loading = true;
      try {
        const response = await answerStudentMcq(payload);
        const stack = this.messagesBySession[payload.session_id] || [];
        this.messagesBySession[payload.session_id] = [...stack, response.user_message, response.assistant_message];
        return response;
      } finally {
        this.loading = false;
      }
    },
  },
});

