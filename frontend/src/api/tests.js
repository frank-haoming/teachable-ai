import api from "./index";

export const createPaper = async (payload) => (await api.post("/tests/papers", payload)).data;
export const fetchPapers = async (params) => (await api.get("/tests/papers", { params })).data;
export const addQuestion = async (paperId, payload) => (await api.post(`/tests/papers/${paperId}/questions`, payload)).data;
export const updateQuestion = async (questionId, payload) => (await api.put(`/tests/questions/${questionId}`, payload)).data;
export const deleteQuestion = async (questionId) => (await api.delete(`/tests/questions/${questionId}`)).data;
export const executePaper = async (paperId) => (await api.post(`/tests/papers/${paperId}/execute`)).data;
export const fetchRun = async (runId) => (await api.get(`/tests/runs/${runId}`)).data;
export const fetchResults = async (paperId, params) => (await api.get(`/tests/papers/${paperId}/results`, { params })).data;

