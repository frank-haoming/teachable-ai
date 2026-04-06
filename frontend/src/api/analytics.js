import api from "./index";

export const fetchClassOverview = async (classId) => (await api.get(`/analytics/class/${classId}/overview`)).data;
export const fetchClassStudents = async (classId) => (await api.get(`/analytics/class/${classId}/students`)).data;
export const fetchStudentProgress = async (studentId, classId) =>
  (await api.get(`/analytics/student/${studentId}/progress`, { params: { class_id: classId } })).data;
export const fetchStudentDetail = async (classId, studentId) =>
  (await api.get(`/analytics/class/${classId}/students/${studentId}`)).data;

