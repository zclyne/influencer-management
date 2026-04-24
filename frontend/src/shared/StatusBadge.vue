<script setup lang="ts">
defineProps<{
  label: string
  tone?: 'neutral' | 'active' | 'warning' | 'danger' | 'success'
}>()
</script>

<template>
  <span class="badge" :class="tone ?? 'neutral'">{{ label }}</span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  min-height: 24px;
  padding: 3px 8px;
  border: 1px solid #d9e0ea;
  border-radius: 8px;
  background: #f8fafc;
  color: #4d574f;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.3;
}

.active {
  border-color: #9fc7ba;
  background: #e8f5ef;
  color: #17634d;
}

.warning {
  border-color: #ead27a;
  background: #fff7d6;
  color: #806300;
}

.danger {
  border-color: #f1b4ae;
  background: #fff0ee;
  color: #9f2d20;
}

.success {
  border-color: #9fc7ba;
  background: #e8f5ef;
  color: #17634d;
}
</style>
