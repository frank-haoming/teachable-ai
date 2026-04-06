import api from "./index";

export const fetchKnowledge = async (classId) => (await api.get(`/knowledge/${classId}`)).data;
export const fetchFlatKnowledge = async (classId) => (await api.get(`/knowledge/${classId}/flat`)).data;
export const correctKnowledge = async (classId, payload) => (await api.post(`/knowledge/${classId}/correct`, payload)).data;
export const updateKnowledgeItem = async (itemId, classId, payload) =>
  (await api.put(`/knowledge/items/${itemId}`, payload, { params: { class_id: classId } })).data;
export const deleteKnowledgeItem = async (itemId, classId) =>
  (await api.delete(`/knowledge/items/${itemId}`, { params: { class_id: classId } })).data;

