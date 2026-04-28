<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<template>
  <a-empty class="placeholder-page" :description="description">
    <template #image>
      <div class="placeholder-mark" aria-hidden="true">{{ title.slice(0, 2).toUpperCase() }}</div>
    </template>
    <h1>{{ title }}</h1>
  </a-empty>
</template>

<style scoped>
.placeholder-page {
  display: grid;
  place-items: center;
  min-height: 420px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #ffffff;
}

.placeholder-mark {
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  margin: 0 auto;
  border: 1px solid #b7cdc4;
  border-radius: 8px;
  background: #f1f8f5;
  color: #1d6b55;
  font-weight: 900;
}

h1 {
  margin: 0;
  color: #20262d;
  font-size: 28px;
}
</style>
