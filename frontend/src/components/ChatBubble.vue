<template>
  <article class="chat-bubble" :class="message.role">
    <header>
      <strong>{{ message.role === "assistant" ? (assistantLabel || aiName || "学习伙伴") : userLabel }}</strong>
      <time>{{ formatTime(message.created_at) }}</time>
    </header>
    <p>{{ message.content }}</p>
  </article>
</template>

<script setup>
const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
  aiName: {
    type: String,
    default: "",
  },
  assistantLabel: {
    type: String,
    default: "",
  },
  userLabel: {
    type: String,
    default: "你",
  },
});

const formatTime = (value) => {
  if (!value) return "";
  return new Date(value).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
};
</script>

<style scoped>
.chat-bubble {
  max-width: 85%;
  padding: 16px 18px;
  border-radius: 22px;
  border: 1px solid var(--aa-border);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 12px rgba(9, 68, 62, 0.06);
}

.chat-bubble.user {
  margin-left: auto;
  border-bottom-right-radius: 8px;
  background: rgba(13, 148, 136, 0.1);
  border-left: 3px solid var(--aa-primary);
}

.chat-bubble.assistant {
  border-bottom-left-radius: 8px;
  box-shadow: 0 6px 18px rgba(9, 68, 62, 0.09);
}

.chat-bubble header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  color: var(--aa-text-soft);
  font-size: 0.84rem;
}

.chat-bubble header time {
  opacity: 0;
  transition: opacity 180ms ease;
}

.chat-bubble:hover header time {
  opacity: 1;
}

.chat-bubble p {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.75;
  word-break: break-word;
  overflow-wrap: anywhere;
}
</style>
