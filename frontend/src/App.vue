<script setup lang="ts">
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
</script>

<template>
  <main class="shell">
    <section class="workspace">
      <p class="eyebrow">Desktop IRM</p>
      <h1>Campaign pipeline workspace</h1>
      <p class="summary">
        Import creators, build campaign deals, track deliverables, compensation, and email context.
      </p>
      <p class="api">API: {{ apiBaseUrl }}/api/v1</p>
    </section>
  </main>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  margin: 0;
  background: #f6f8fb;
  color: #172033;
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.workspace {
  width: min(720px, calc(100vw - 48px));
}

.eyebrow {
  margin: 0 0 12px;
  color: #0f766e;
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  font-size: 42px;
  line-height: 1.1;
}

.summary {
  max-width: 620px;
  margin: 20px 0 0;
  color: #46536a;
  font-size: 18px;
  line-height: 1.6;
}

.api {
  margin-top: 28px;
  font-size: 14px;
  color: #5f6f89;
}
</style>

