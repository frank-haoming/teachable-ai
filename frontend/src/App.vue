<template>
  <AppShell v-if="route.meta.layout === 'app'">
    <router-view />
  </AppShell>
  <router-view v-else />
</template>

<script setup>
import { useRoute } from "vue-router";

import AppShell from "@/components/AppShell.vue";

const route = useRoute();
</script>

