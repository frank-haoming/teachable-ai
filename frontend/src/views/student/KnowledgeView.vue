<template>
  <div class="page-shell surface-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">AI 知识查看</span>
        <h2 class="page-title">{{ classInfo?.name || "知识库" }}</h2>
        <p class="page-subtitle">这里展示 AI 当前掌握的规则与例句。你可以直接编辑，也可以回到 Teach 区对话修正。</p>
      </div>
      <router-link :to="{ name: 'student-teach', params: { classId } }">
        <el-button type="primary">回到 Teach</el-button>
      </router-link>
    </header>

    <div v-if="!items.length" class="empty-state section-card">AI 还没有任何稳定记忆。先去 Teach 区开始教学。</div>
    <section v-else class="soft-grid two-col">
      <KnowledgeCard v-for="item in items" :key="item.id" :item="item">
        <template #actions="{ item: knowledgeItem }">
          <el-button text @click="openEdit(knowledgeItem)">编辑</el-button>
          <el-button text type="warning" @click="sendToTeach(knowledgeItem)">对话修正</el-button>
        </template>
      </KnowledgeCard>
    </section>

    <el-dialog v-model="editDialog" title="直接编辑知识条目" width="560px">
      <el-form label-position="top">
        <el-form-item label="内容">
          <el-input
            v-model="editForm.main"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </el-form-item>
        <el-form-item v-if="activeItem?.item_type === 'example'" label="解释">
          <el-input v-model="editForm.explanation" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import { fetchClassDetail } from "@/api/classes";
import { fetchFlatKnowledge, updateKnowledgeItem } from "@/api/knowledge";
import KnowledgeCard from "@/components/KnowledgeCard.vue";

const props = defineProps({
  classId: {
    type: [String, Number],
    required: true,
  },
});

const router = useRouter();
const classInfo = ref(null);
const items = ref([]);
const editDialog = ref(false);
const activeItem = ref(null);
const editForm = ref({ main: "", explanation: "" });

const load = async () => {
  classInfo.value = await fetchClassDetail(props.classId);
  items.value = await fetchFlatKnowledge(props.classId);
};

const openEdit = (item) => {
  activeItem.value = item;
  editForm.value = {
    main: item.content || item.sentence || "",
    explanation: item.explanation || "",
  };
  editDialog.value = true;
};

const saveEdit = async () => {
  try {
    const payload =
      activeItem.value.item_type === "knowledge"
        ? { content: editForm.value.main }
        : { sentence: editForm.value.main, explanation: editForm.value.explanation };
    await updateKnowledgeItem(activeItem.value.id, props.classId, payload);
    editDialog.value = false;
    await load();
    ElMessage.success("知识条目已更新。");
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "更新失败。");
  }
};

const sendToTeach = async (item) => {
  await router.push({ name: "student-teach", params: { classId: props.classId }, query: { seed: item.id } });
};

onMounted(load);
</script>

