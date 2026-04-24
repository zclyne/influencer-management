<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { confirmImport, errorMessage, previewModashImport } from '../api/client'
import type {
  CampaignResponse,
  IngestionConfirmAction,
  IngestionConfirmResponse,
  IngestionPreviewResponse,
  IngestionPreviewRow,
  ImportSourceType,
} from '../api/types'
import StatusBadge from '../shared/StatusBadge.vue'

const props = defineProps<{
  campaigns: CampaignResponse[]
  selectedCampaignId: string | null
}>()

const emit = defineEmits<{
  campaignChanged: [campaignId: string]
}>()

const file = ref<File | null>(null)
const preview = ref<IngestionPreviewResponse | null>(null)
const result = ref<IngestionConfirmResponse | null>(null)
const previewing = ref(false)
const confirming = ref(false)
const error = ref<string | null>(null)
const targetCampaignId = ref(props.selectedCampaignId ?? '')
const actions = reactive<Record<number, IngestionConfirmAction>>({})

const selectedCampaignName = computed(
  () => props.campaigns.find((campaign) => campaign.id === targetCampaignId.value)?.name ?? null,
)

watch(
  () => props.selectedCampaignId,
  (campaignId) => {
    targetCampaignId.value = campaignId ?? ''
  },
)

const actionCounts = computed(() => {
  const counts = { create: 0, merge: 0, skip: 0 }
  Object.values(actions).forEach((action) => {
    counts[action] += 1
  })
  return counts
})

const defaultActionForRow = (row: IngestionPreviewRow): IngestionConfirmAction => {
  if (row.status === 'invalid') return 'skip'
  if (row.status === 'matched_existing' && row.dedup.influencer_id) return 'merge'
  if (row.status === 'new') return 'create'
  return 'skip'
}

const badgeTone = (row: IngestionPreviewRow) => {
  if (row.status === 'invalid') return 'danger'
  if (row.status === 'possible_duplicate') return 'warning'
  if (row.status === 'new') return 'success'
  if (row.status === 'matched_existing') return 'active'
  return 'neutral'
}

const rowTitle = (row: IngestionPreviewRow) =>
  row.row.display_name || row.row.full_name || row.row.username || `Row ${row.row.source_row_number}`

const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  file.value = input.files?.[0] ?? null
  preview.value = null
  result.value = null
  error.value = null
  Object.keys(actions).forEach((key) => {
    delete actions[Number(key)]
  })
}

const setTargetCampaign = (event: Event) => {
  const value = (event.target as HTMLSelectElement).value
  targetCampaignId.value = value
  if (value) emit('campaignChanged', value)
}

const runPreview = async () => {
  if (!file.value) return

  previewing.value = true
  error.value = null
  result.value = null

  try {
    const nextPreview = await previewModashImport(file.value)
    preview.value = nextPreview
    Object.keys(actions).forEach((key) => {
      delete actions[Number(key)]
    })
    nextPreview.rows.forEach((row) => {
      actions[row.row.source_row_number] = defaultActionForRow(row)
    })
  } catch (previewError) {
    error.value = errorMessage(previewError)
  } finally {
    previewing.value = false
  }
}

const runConfirm = async () => {
  if (!preview.value || !file.value) return

  confirming.value = true
  error.value = null
  result.value = null

  try {
    result.value = await confirmImport({
      source_type: preview.value.source_type as ImportSourceType,
      file_name: file.value.name,
      target_campaign_id: targetCampaignId.value || null,
      rows: preview.value.rows.map((previewRow) => {
        const action = actions[previewRow.row.source_row_number] ?? defaultActionForRow(previewRow)
        return {
          row: previewRow.row,
          action,
          existing_influencer_id: action === 'merge' ? previewRow.dedup.influencer_id ?? null : null,
        }
      }),
    })
  } catch (confirmError) {
    error.value = errorMessage(confirmError)
  } finally {
    confirming.value = false
  }
}
</script>

<template>
  <section class="import-layout">
    <section class="import-main">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Influencer Imports</p>
          <h1>Modash CSV wizard</h1>
        </div>
        <StatusBadge label="Real preview + confirm API" tone="active" />
      </div>

      <div class="setup-row">
        <label>
          CSV file
          <input type="file" accept=".csv,text/csv" @change="handleFileChange" />
        </label>
        <label>
          Target campaign
          <select :value="targetCampaignId" @change="setTargetCampaign">
            <option value="">Library only</option>
            <option v-for="campaign in campaigns" :key="campaign.id" :value="campaign.id">
              {{ campaign.name }}
            </option>
          </select>
        </label>
        <button type="button" class="primary-button" :disabled="!file || previewing" @click="runPreview">
          {{ previewing ? 'Previewing...' : 'Preview CSV' }}
        </button>
      </div>

      <div v-if="error" class="error-box">{{ error }}</div>

      <div v-if="preview?.fatal_errors.length" class="error-box">
        <strong>Fatal import errors</strong>
        <span v-for="fatalError in preview.fatal_errors" :key="fatalError">{{ fatalError }}</span>
      </div>

      <div v-if="preview" class="preview-tools">
        <div>
          <strong>{{ preview.row_count }} row(s) parsed</strong>
          <span>{{ selectedCampaignName ? `Deals will be added to ${selectedCampaignName}.` : 'Rows will update the global library only.' }}</span>
        </div>
        <div class="action-summary">
          <StatusBadge :label="`${actionCounts.create} create`" tone="success" />
          <StatusBadge :label="`${actionCounts.merge} merge`" tone="active" />
          <StatusBadge :label="`${actionCounts.skip} skip`" />
        </div>
      </div>

      <div v-if="preview" class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Row</th>
              <th>Influencer</th>
              <th>Platform</th>
              <th>Dedup</th>
              <th>Action</th>
              <th>Messages</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="previewRow in preview.rows" :key="previewRow.row.source_row_number">
              <td>{{ previewRow.row.source_row_number }}</td>
              <td>
                <strong>{{ rowTitle(previewRow) }}</strong>
                <span class="subtext">{{ previewRow.row.country }} {{ previewRow.row.city }}</span>
              </td>
              <td>
                <strong>{{ previewRow.row.platform ?? 'Unknown' }}</strong>
                <span class="subtext">{{ previewRow.row.username ?? previewRow.row.profile_url }}</span>
              </td>
              <td>
                <StatusBadge :label="previewRow.status" :tone="badgeTone(previewRow)" />
                <span class="subtext">{{ previewRow.dedup.reason }}</span>
              </td>
              <td>
                <select v-model="actions[previewRow.row.source_row_number]">
                  <option value="create">Create</option>
                  <option :disabled="!previewRow.dedup.influencer_id" value="merge">Merge</option>
                  <option value="skip">Skip</option>
                </select>
              </td>
              <td>
                <div class="message-list">
                  <span v-for="message in previewRow.row.parse_errors" :key="message" class="danger-text">
                    {{ message }}
                  </span>
                  <span v-for="message in previewRow.row.warnings" :key="message">{{ message }}</span>
                  <span v-if="!previewRow.row.parse_errors.length && !previewRow.row.warnings.length">-</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <aside class="confirm-panel">
      <h2>Confirm write</h2>
      <p>
        Preview keeps parsing and dedup decisions server-side. Confirm sends your row actions back through
        the source-agnostic import endpoint.
      </p>
      <button type="button" class="primary-button" :disabled="!preview || confirming" @click="runConfirm">
        {{ confirming ? 'Confirming...' : 'Confirm import' }}
      </button>

      <div v-if="result" class="result-box">
        <strong>Import session {{ result.import_session_id }}</strong>
        <span>{{ result.imported_count }} imported, {{ result.skipped_count }} skipped, {{ result.conflict_count }} conflicts</span>
        <span>{{ result.created_deals }} campaign deal(s) created</span>
      </div>

      <div v-if="result" class="result-list">
        <div v-for="row in result.rows" :key="row.source_row_number" class="result-row">
          <span>Row {{ row.source_row_number }}</span>
          <StatusBadge :label="row.status" :tone="row.status === 'failed' ? 'danger' : 'neutral'" />
        </div>
      </div>
    </aside>
  </section>
</template>

<style scoped>
.import-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 340px);
  gap: 20px;
}

.section-heading,
.preview-tools {
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

.setup-row {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(220px, 300px) auto;
  align-items: end;
  gap: 12px;
  margin-bottom: 14px;
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

.primary-button {
  min-height: 36px;
  border: 1px solid #215f4e;
  border-radius: 8px;
  padding: 0 12px;
  background: #215f4e;
  color: #ffffff;
  font-weight: 800;
  cursor: pointer;
}

.primary-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.error-box,
.result-box,
.confirm-panel {
  border-radius: 8px;
}

.error-box {
  display: grid;
  gap: 4px;
  margin-bottom: 12px;
  padding: 10px;
  border: 1px solid #f1b4ae;
  background: #fff0ee;
  color: #9f2d20;
  font-size: 13px;
}

.preview-tools {
  align-items: center;
  padding: 12px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
}

.preview-tools div {
  display: grid;
  gap: 4px;
}

.preview-tools span {
  color: #657068;
  font-size: 13px;
}

.action-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
}

table {
  width: 100%;
  min-width: 980px;
  border-collapse: collapse;
}

th,
td {
  padding: 11px 12px;
  border-bottom: 1px solid #edf1f6;
  vertical-align: top;
  text-align: left;
}

th {
  background: #f8fafc;
  color: #626b64;
  font-size: 12px;
  text-transform: uppercase;
}

td strong,
.result-box strong {
  display: block;
  color: #242826;
}

.subtext {
  display: block;
  margin-top: 4px;
  color: #657068;
  font-size: 12px;
}

.message-list {
  display: grid;
  gap: 4px;
  color: #657068;
  font-size: 12px;
}

.danger-text {
  color: #9f2d20;
}

.confirm-panel {
  display: grid;
  align-content: start;
  gap: 14px;
  padding: 16px;
  border: 1px solid #dbe3ee;
  background: #ffffff;
}

.confirm-panel p {
  margin: 0;
  color: #657068;
  font-size: 13px;
  line-height: 1.5;
}

.result-box {
  display: grid;
  gap: 5px;
  padding: 10px;
  border: 1px solid #9fc7ba;
  background: #e8f5ef;
  color: #17634d;
  font-size: 13px;
}

.result-list {
  display: grid;
  gap: 8px;
}

.result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 34px;
  padding: 8px;
  border: 1px solid #e1e7ef;
  border-radius: 8px;
}

@media (max-width: 1080px) {
  .import-layout,
  .setup-row {
    grid-template-columns: 1fr;
  }
}
</style>
