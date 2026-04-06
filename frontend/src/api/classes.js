import api from "./index";

export const fetchClasses = async () => (await api.get("/classes")).data;
export const createClass = async (payload) => (await api.post("/classes", payload)).data;
export const fetchClassDetail = async (classId) => (await api.get(`/classes/${classId}`)).data;
export const joinClass = async (payload) => (await api.post("/classes/join", payload)).data;
export const getQrCodeUrl = (classId) => `${api.defaults.baseURL}/classes/${classId}/invite-qrcode`;

