<script setup lang="ts">
import StatusBadge from '../shared/StatusBadge.vue'
import type { WorkbenchDeal } from '../api/types'

defineProps<{
  open: boolean
  campaignName?: string
  deal: WorkbenchDeal | null
}>()

defineEmits<{
  close: []
}>()
</script>

<template>
  <aside v-if="open" class="drawer" aria-label="Deal detail">
    <div class="drawer-header">
      <div>
        <p class="eyebrow">{{ campaignName ?? 'Campaign deal' }}</p>
        <h2>{{ deal?.influencerName ?? 'Deal detail' }}</h2>
      </div>
      <button class="icon-button" type="button" aria-label="Close deal detail" @click="$emit('close')">
        X
      </button>
    </div>

    <section class="panel">
      <div class="panel-row">
        <span>Status</span>
        <StatusBadge :label="deal?.status ?? 'DRAFT'" tone="active" />
      </div>
      <div class="panel-row">
        <span>Next action</span>
        <strong>{{ deal?.nextAction ?? 'Open once deal pipeline endpoints are available.' }}</strong>
      </div>
      <div class="panel-row">
        <span>Labels</span>
        <div class="tag-row">
          <StatusBadge
            v-for="label in deal?.labels ?? ['campaign-specific']"
            :key="label"
            :label="label"
          />
        </div>
      </div>
    </section>

    <section class="panel">
      <h3>Contacts</h3>
      <p class="muted">
        Known contacts and manager relationships will load from the Influencer Library subresources.
      </p>
    </section>

    <section class="panel">
      <h3>Deliverables</h3>
      <div class="empty-line">Deliverable rows will appear here with status, due date, post URL, and notes.</div>
    </section>

    <section class="panel">
      <h3>Compensation</h3>
      <div class="empty-line">
        CompensationItem rows will track cash, gifts, samples, reimbursements, travel, meals, and other costs.
      </div>
    </section>

    <section class="panel">
      <h3>Email context</h3>
      <div class="empty-line">
        Manual thread links and contact-based candidates will appear here without changing status automatically.
      </div>
    </section>
  </aside>
</template>

<style scoped>
.drawer {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 10;
  width: min(440px, 100vw);
  height: 100vh;
  overflow-y: auto;
  border-left: 1px solid #d7dee8;
  background: #fbfcfe;
  box-shadow: -12px 0 32px rgb(22 32 51 / 12%);
}

.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
}

.eyebrow {
  margin: 0 0 6px;
  color: #667066;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

h2,
h3 {
  margin: 0;
  color: #242826;
}

h2 {
  font-size: 22px;
}

h3 {
  font-size: 14px;
}

.icon-button {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
  color: #3d443f;
  cursor: pointer;
}

.panel {
  display: grid;
  gap: 14px;
  margin: 16px;
  padding: 16px;
  border: 1px solid #e1e7ef;
  border-radius: 8px;
  background: #ffffff;
}

.panel-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  align-items: start;
  gap: 12px;
  color: #566058;
  font-size: 13px;
}

.panel-row strong {
  color: #242826;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.muted,
.empty-line {
  margin: 0;
  color: #657068;
  font-size: 13px;
  line-height: 1.5;
}
</style>
