<template>
  <aside class="knowledge-panel glass-card">
    <div class="knowledge-panel__header">
      <div>
        <span class="eyebrow">AI 当前记忆</span>
        <h3>Teach 区实时知识面板 <span v-if="items.length" class="data-chip count-badge">{{ items.length }}</span></h3>
      </div>
      <el-button text @click="$emit('refresh')">刷新</el-button>
    </div>
    <div v-if="!items.length" class="empty-state">
      AI 还没有学到稳定的知识。先从定义、判断方法或例句开始教它。
    </div>
    <div v-else class="surface-stack items-list">
      <KnowledgeCard v-for="item in items" :key="item.id" :item="item">
        <template #actions="{ item: knowledgeItem }">
          <el-button text @click="$emit('correct', knowledgeItem)">纠正</el-button>
        </template>
      </KnowledgeCard>
    </div>
  </aside>
</template>

<script setup>
import KnowledgeCard from "./KnowledgeCard.vue";

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["refresh", "correct"]);
</script>

<style scoped>
.knowledge-panel {
  padding: 20px;
  align-self: start;
}

.knowledge-panel__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.knowledge-panel h3 {
  margin: 12px 0 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.count-badge {
  font-size: 0.8rem;
  padding: 4px 10px;
}

.items-list {
  max-height: calc(100vh - 140px);
  overflow-y: auto;
  transition: max-height 300ms ease;
}
</style>

