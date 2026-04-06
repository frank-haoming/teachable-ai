<template>
  <el-dialog :model-value="modelValue" title="班级邀请码二维码" width="420px" @close="$emit('update:modelValue', false)">
    <div class="qr-modal">
      <img :src="src" alt="班级邀请码二维码" />
      <p class="muted">{{ note }}</p>
    </div>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
      <a :href="src" target="_blank" rel="noreferrer">
        <el-button type="primary">新窗口打开</el-button>
      </a>
    </template>
  </el-dialog>
</template>

<script setup>
defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  src: {
    type: String,
    required: true,
  },
  note: {
    type: String,
    default: "学生扫码后会自动带上班级邀请码。",
  },
});

defineEmits(["update:modelValue"]);
</script>

<style scoped>
.qr-modal {
  display: grid;
  gap: 12px;
  justify-items: center;
  text-align: center;
}

.qr-modal img {
  width: 260px;
  height: 260px;
  object-fit: contain;
  border-radius: 20px;
  background: #fff;
  padding: 10px;
}
</style>
