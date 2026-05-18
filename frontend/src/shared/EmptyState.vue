<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<template>
  <a-empty class="empty-state" :description="null">
    <template #image>
      <div class="empty-state-icon" aria-hidden="true" />
    </template>
    <div class="empty-state-copy">
      <strong>{{ title }}</strong>
      <p>{{ description }}</p>
      <div v-if="$slots.actions" class="empty-state-actions">
        <slot name="actions" />
      </div>
    </div>
  </a-empty>
</template>

<style scoped>
.empty-state {
  padding: 28px 16px;
}

.empty-state-icon {
  width: 54px;
  height: 42px;
  margin: 0 auto;
  border: 1px solid #cdd6df;
  border-radius: 8px;
  background:
    linear-gradient(#eef3f6, #eef3f6) 12px 12px / 30px 4px no-repeat,
    linear-gradient(#d7e0e7, #d7e0e7) 12px 23px / 22px 4px no-repeat,
    #f8fafc;
}

.empty-state-copy {
  display: grid;
  justify-items: center;
  gap: 6px;
  max-width: 420px;
  margin: 0 auto;
}

.empty-state-copy strong {
  color: #20262d;
  font-size: 15px;
}

.empty-state-copy p {
  margin: 0;
  color: #697582;
  line-height: 1.45;
}

.empty-state-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
}
</style>
