<template>
  <div class="brand-lockup" :class="{ compact }">
    <BrandMark :size="compact ? 42 : 52" />
    <div>
      <div class="brand-title-row">
        <strong>Apprentice AI</strong>
        <span class="brand-tagline">Teach an AI student. Learn by teaching.</span>
      </div>
      <p>以教促学智能学习平台</p>
    </div>
  </div>
</template>

<script setup>
import BrandMark from "./BrandMark.vue";

defineProps({
  compact: {
    type: Boolean,
    default: false,
  },
});
</script>

<style scoped>
.brand-lockup {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-lockup strong {
  display: block;
  font-family: "Crimson Pro", serif;
  font-size: 1.55rem;
  line-height: 1;
}

.brand-lockup p {
  margin: 4px 0 0;
  color: var(--aa-text-soft);
  font-size: 0.92rem;
}

.brand-title-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}

.brand-tagline {
  color: var(--aa-primary-deep);
  font-size: 0.82rem;
}

.compact strong {
  font-size: 1.4rem;
}

.compact p {
  font-size: 0.85rem;
}
</style>

