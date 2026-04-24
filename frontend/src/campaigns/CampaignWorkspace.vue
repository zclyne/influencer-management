<script setup lang="ts">
import { computed, reactive } from 'vue'
import type { CampaignCreateRequest, CampaignResponse, CampaignStatus, WorkbenchDeal } from '../api/types'
import StatusBadge from '../shared/StatusBadge.vue'

const props = defineProps<{
  campaigns: CampaignResponse[]
  selectedCampaignId: string | null
  loading: boolean
  error: string | null
}>()

const emit = defineEmits<{
  refresh: []
  selectCampaign: [campaignId: string]
  createCampaign: [payload: CampaignCreateRequest]
  importForCampaign: [campaignId: string]
  openDeal: [deal: WorkbenchDeal | null]
}>()

const newCampaign = reactive({
  name: '',
  status: 'PLANNING' as CampaignStatus,
  budget: '',
})

const selectedCampaign = computed(
  () => props.campaigns.find((campaign) => campaign.id === props.selectedCampaignId) ?? null,
)

const statusTone = (status: CampaignStatus) => {
  if (status === 'ACTIVE') return 'active'
  if (status === 'CLOSED') return 'neutral'
  if (status === 'EVALUATING') return 'warning'
  return 'neutral'
}

const submitCampaign = () => {
  const name = newCampaign.name.trim()
  if (!name) return

  emit('createCampaign', {
    name,
    status: newCampaign.status,
    budget: newCampaign.budget ? newCampaign.budget : null,
  })

  newCampaign.name = ''
  newCampaign.status = 'PLANNING'
  newCampaign.budget = ''
}
</script>

<template>
  <section class="workspace-grid">
    <aside class="campaign-rail" aria-label="Campaign list">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Campaign Workspace</p>
          <h1>Pipeline</h1>
        </div>
        <button type="button" class="secondary-button" @click="$emit('refresh')">Refresh</button>
      </div>

      <div v-if="error" class="error-box">{{ error }}</div>
      <div v-else-if="loading" class="loading-box">Loading campaigns...</div>

      <div class="campaign-list">
        <button
          v-for="campaign in campaigns"
          :key="campaign.id"
          class="campaign-item"
          :class="{ selected: campaign.id === selectedCampaignId }"
          type="button"
          @click="$emit('selectCampaign', campaign.id)"
        >
          <span>{{ campaign.name }}</span>
          <StatusBadge :label="campaign.status" :tone="statusTone(campaign.status)" />
        </button>
      </div>

      <form class="create-form" @submit.prevent="submitCampaign">
        <h2>New campaign</h2>
        <label>
          Name
          <input v-model="newCampaign.name" type="text" placeholder="Spring launch" />
        </label>
        <div class="form-row">
          <label>
            Status
            <select v-model="newCampaign.status">
              <option value="PLANNING">Planning</option>
              <option value="ACTIVE">Active</option>
              <option value="EVALUATING">Evaluating</option>
              <option value="CLOSED">Closed</option>
            </select>
          </label>
          <label>
            Budget
            <input v-model="newCampaign.budget" type="number" min="0" step="0.01" placeholder="0" />
          </label>
        </div>
        <button type="submit" class="primary-button">Create campaign</button>
      </form>
    </aside>

    <section class="deal-workspace" aria-label="Campaign deals">
      <div class="workspace-header">
        <div>
          <p class="eyebrow">Selected campaign</p>
          <h2>{{ selectedCampaign?.name ?? 'Choose a campaign' }}</h2>
        </div>
        <div class="header-actions">
          <button
            type="button"
            class="secondary-button"
            :disabled="!selectedCampaign"
            @click="selectedCampaign && $emit('importForCampaign', selectedCampaign.id)"
          >
            Import CSV
          </button>
          <button type="button" class="secondary-button" @click="$emit('openDeal', null)">
            Deal detail
          </button>
        </div>
      </div>

      <div class="status-strip">
        <div class="metric">
          <span>Draft</span>
          <strong>0</strong>
        </div>
        <div class="metric">
          <span>Outreached</span>
          <strong>0</strong>
        </div>
        <div class="metric">
          <span>Negotiating</span>
          <strong>0</strong>
        </div>
        <div class="metric">
          <span>Active</span>
          <strong>0</strong>
        </div>
        <div class="metric">
          <span>Completed</span>
          <strong>0</strong>
        </div>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Influencer</th>
              <th>Status</th>
              <th>Labels</th>
              <th>Next action</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colspan="5">
                <div class="empty-state">
                  <strong>Deal query endpoint pending</strong>
                  <span>
                    Imported influencers can already create campaign deals on confirm. Once the Campaign
                    Workspace API lands, this table will load real Deal rows for the selected campaign.
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<style scoped>
.workspace-grid {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 20px;
}

.campaign-rail,
.deal-workspace {
  min-width: 0;
}

.section-heading,
.workspace-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #667066;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

h1,
h2 {
  margin: 0;
  color: #242826;
}

h1 {
  font-size: 28px;
}

h2 {
  font-size: 20px;
}

.campaign-list {
  display: grid;
  gap: 8px;
  max-height: 42vh;
  overflow-y: auto;
}

.campaign-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  min-height: 48px;
  padding: 10px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
  color: #303632;
  text-align: left;
  cursor: pointer;
}

.campaign-item.selected {
  border-color: #2d7f67;
  box-shadow: inset 3px 0 0 #2d7f67;
}

.create-form {
  display: grid;
  gap: 12px;
  margin-top: 18px;
  padding: 14px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

label {
  display: grid;
  gap: 6px;
  color: #515b54;
  font-size: 12px;
  font-weight: 700;
}

input,
select {
  width: 100%;
  min-width: 0;
  height: 36px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0 10px;
  background: #ffffff;
  color: #242826;
  font: inherit;
}

.primary-button,
.secondary-button {
  min-height: 36px;
  border-radius: 8px;
  padding: 0 12px;
  font-weight: 800;
  cursor: pointer;
}

.primary-button {
  border: 1px solid #215f4e;
  background: #215f4e;
  color: #ffffff;
}

.secondary-button {
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #303632;
}

.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(96px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.metric {
  display: grid;
  gap: 4px;
  padding: 12px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
}

.metric span {
  color: #626b64;
  font-size: 12px;
  font-weight: 700;
}

.metric strong {
  color: #242826;
  font-size: 22px;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
}

table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
}

th,
td {
  padding: 11px 12px;
  border-bottom: 1px solid #edf1f6;
  text-align: left;
}

th {
  background: #f8fafc;
  color: #626b64;
  font-size: 12px;
  text-transform: uppercase;
}

.empty-state {
  display: grid;
  gap: 6px;
  padding: 36px 12px;
  color: #657068;
  text-align: center;
}

.empty-state strong {
  color: #303632;
}

.error-box,
.loading-box {
  margin-bottom: 12px;
  padding: 10px;
  border-radius: 8px;
  font-size: 13px;
}

.error-box {
  border: 1px solid #f1b4ae;
  background: #fff0ee;
  color: #9f2d20;
}

.loading-box {
  border: 1px solid #dbe3ee;
  background: #ffffff;
  color: #566058;
}

@media (max-width: 920px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .status-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
