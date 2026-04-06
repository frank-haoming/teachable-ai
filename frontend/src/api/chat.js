import api from "./index";

export const createSession = async (payload) => (await api.post("/chat/sessions", payload)).data;
export const listSessions = async (params) => (await api.get("/chat/sessions", { params })).data;
export const fetchMessages = async (sessionId) => (await api.get(`/chat/sessions/${sessionId}/messages`)).data;
export const sendMessage = async (payload) => (await api.post("/chat/send", payload)).data;
export const answerStudentMcq = async (payload) => (await api.post("/chat/student-test/mcq", payload)).data;

