export const DEFAULT_COURSE_TOPIC = "英语名词从句";

export const DEFAULT_COVERED_TOPICS = [
  "主语从句",
  "宾语从句",
  "表语从句",
  "同位语从句",
];

export const DEFAULT_KNOWLEDGE_FOCUSES = [
  "通用",
  "定义",
  "基本结构",
  "常见引导词",
  "语法功能",
  "例子",
];

export const SESSION_TYPE_LABELS = {
  teach: "Teach 对话",
  student_test_free: "自由问答自测",
  student_test_mcq: "选择题自测",
};

export const dedupeNonEmpty = (values = []) => [...new Set(values.map((value) => value.trim()).filter(Boolean))];

export const resolveCoveredTopics = (values = []) => {
  const deduped = dedupeNonEmpty(values);
  return deduped.length ? deduped : [...DEFAULT_COVERED_TOPICS];
};

export const resolveKnowledgeFocuses = (values = []) => {
  const deduped = dedupeNonEmpty(values);
  if (!deduped.length) return [...DEFAULT_KNOWLEDGE_FOCUSES];
  return deduped.includes("通用") ? deduped : ["通用", ...deduped];
};

