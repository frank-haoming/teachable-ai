<template>
  <div class="editable-tag-field">
    <div class="tag-list">
      <el-tag
        v-for="item in items"
        :key="item"
        :closable="!lockedSet.has(item)"
        :class="['tag-item', { 'tag-item--locked': lockedSet.has(item) }]"
        :title="lockedSet.has(item) ? '此项为必选，不可删除' : undefined"
        @close="removeItem(item)"
      >
        <span v-if="lockedSet.has(item)" class="tag-lock-icon" aria-hidden="true">🔒 </span>{{ item }}
      </el-tag>
    </div>
    <div class="tag-input-row">
      <el-input
        v-model.trim="draft"
        :placeholder="placeholder"
        @keydown.enter.prevent="addItem"
      />
      <el-button plain @click="addItem">添加</el-button>
    </div>
    <p v-if="helper" class="muted tag-helper">{{ helper }}</p>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";

import { dedupeNonEmpty } from "@/constants/classScope";

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: "",
  },
  helper: {
    type: String,
    default: "",
  },
  lockedValues: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update:modelValue"]);

const draft = ref("");
const items = computed(() => dedupeNonEmpty(props.modelValue));
const lockedSet = computed(() => new Set(props.lockedValues));

const pushItems = (values) => {
  emit("update:modelValue", dedupeNonEmpty(values));
};

const addItem = () => {
  if (!draft.value) return;
  const next = dedupeNonEmpty([...items.value, draft.value]);
  if (next.length === items.value.length) {
    ElMessage.info("该项已存在。");
  } else {
    pushItems(next);
  }
  draft.value = "";
};

const removeItem = (item) => {
  if (lockedSet.value.has(item)) return;
  pushItems(items.value.filter((value) => value !== item));
};
</script>

<style scoped>
.editable-tag-field {
  display: grid;
  gap: 10px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  padding-inline: 10px;
}

.tag-item--locked {
  opacity: 0.75;
  cursor: not-allowed;
}

.tag-lock-icon {
  font-size: 0.78rem;
  margin-right: 2px;
}

.tag-input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.tag-helper {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.6;
}
</style>
