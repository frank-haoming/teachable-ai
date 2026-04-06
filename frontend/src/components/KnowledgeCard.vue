<template>
  <article class="knowledge-card section-card">
    <div class="knowledge-card__header">
      <span class="data-chip">{{ item.item_type === "knowledge" ? "规则" : "例句" }}</span>
      <span class="muted">{{ item.topic_name }}</span>
    </div>
    <h3>{{ item.content || item.sentence }}</h3>
    <p v-if="item.explanation" class="muted">{{ item.explanation }}</p>
    <footer>
      <small>{{ item.updated_at ? `更新于 ${formatDate(item.updated_at)}` : `记录于 ${formatDate(item.created_at)}` }}</small>
      <div class="knowledge-card__actions">
        <slot name="actions" :item="item" />
      </div>
    </footer>
  </article>
</template>

<script setup>
defineProps({
  item: {
    type: Object,
    required: true,
  },
});

const formatDate = (value) => {
  if (!value) return "刚刚";
  return new Date(value).toLocaleString("zh-CN");
};
</script>

<style scoped>
.knowledge-card {
  padding: 18px;
}

.knowledge-card h3 {
  margin: 14px 0 8px;
  font-size: 1rem;
  line-height: 1.65;
}

.knowledge-card__header,
.knowledge-card footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.knowledge-card__actions {
  display: flex;
  gap: 8px;
}
</style>

