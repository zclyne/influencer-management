<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { type TableColumnsType, type UploadProps } from 'ant-design-vue'
import { FileText, Import, UploadCloud, X } from '@lucide/vue'
import { confirmImport, errorMessage, previewModashImport } from '../api/client'
import type {
  CampaignResponse,
  IngestionConfirmAction,
  IngestionConfirmResponse,
  IngestionRowResult,
  IngestionPreviewResponse,
  IngestionPreviewRow,
  ImportSourceType,
} from '../api/types'
import { platformColor, platformOptions } from '../influencers/useInfluencers'

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
const targetCampaignId = ref<string | undefined>()
const actions = reactive<Record<number, IngestionConfirmAction>>({})

const selectedCampaignName = computed(
  () => props.campaigns.find((campaign) => campaign.id === targetCampaignId.value)?.name ?? null,
)

const campaignOptions = computed(() =>
  props.campaigns.map((campaign) => ({
    label: campaign.name,
    value: campaign.id,
  })),
)

const campaignImportHelp = computed(() =>
  selectedCampaignName.value
    ? `Influencers will be imported into the library and added to ${selectedCampaignName.value} when a campaign deal does not already exist.`
    : 'No campaign selected. Influencers will only be imported into the library.',
)

const actionCounts = computed(() => {
  const counts = { create: 0, merge: 0, skip: 0 }
  Object.values(actions).forEach((action) => {
    counts[action] += 1
  })
  return counts
})

const previewErrorCount = computed(() => {
  if (!preview.value) return 0
  return (
    preview.value.fatal_errors.length +
    preview.value.rows.reduce((count, row) => count + row.row.parse_errors.length, 0)
  )
})

const uploadFileList = computed<UploadProps['fileList']>(() =>
  file.value
    ? [
        {
          uid: 'selected-csv',
          name: file.value.name,
          status: 'done',
          size: file.value.size,
          type: file.value.type,
        },
      ]
    : [],
)

const previewColumns: TableColumnsType<IngestionPreviewRow> = [
  {
    title: '#',
    key: 'row',
    width: 70,
  },
  {
    title: 'Influencer',
    key: 'influencer',
    width: 260,
  },
  {
    title: 'Platforms',
    key: 'platforms',
    width: 280,
  },
  {
    title: 'Contact',
    key: 'contact',
    width: 220,
  },
  {
    title: 'Location',
    key: 'location',
    width: 180,
  },
  {
    title: 'Import status',
    key: 'importStatus',
    width: 180,
  },
  {
    title: 'Action',
    key: 'action',
    width: 160,
  },
  {
    title: 'Import notes',
    key: 'importNotes',
    width: 280,
  },
]

const resultColumns: TableColumnsType<IngestionRowResult> = [
  {
    title: 'Row',
    key: 'row',
    width: 80,
  },
  {
    title: 'Action',
    key: 'action',
    width: 140,
  },
  {
    title: 'Result',
    key: 'status',
    width: 150,
  },
  {
    title: 'Result notes',
    key: 'resultNotes',
  },
]

const defaultActionForRow = (row: IngestionPreviewRow): IngestionConfirmAction => {
  if (row.status === 'invalid') return 'skip'
  if (row.status === 'matched_existing' && row.dedup.influencer_id) return 'merge'
  if (row.status === 'new') return 'create'
  return 'skip'
}

const previewStatusColor = (row: IngestionPreviewRow) => {
  if (row.status === 'invalid') return 'red'
  if (row.status === 'possible_duplicate') return 'gold'
  if (row.status === 'new') return 'green'
  if (row.status === 'matched_existing') return 'orange'
  return 'default'
}

const previewStatusLabel = (row: IngestionPreviewRow) => {
  if (row.status === 'matched_existing') return 'Duplicate'
  if (row.status === 'possible_duplicate') return 'Possible duplicate'
  if (row.status === 'new') return 'New'
  if (row.status === 'invalid') return 'Invalid'
  return row.status
}

const actionColor = (action: IngestionConfirmAction) => {
  if (action === 'create') return 'green'
  if (action === 'merge') return 'blue'
  return 'default'
}

const resultStatusColor = (status: IngestionRowResult['status']) => {
  if (status === 'failed' || status === 'invalid' || status === 'conflict') return 'red'
  if (status === 'created' || status === 'merged') return 'green'
  return 'default'
}

const rowTitle = (row: IngestionPreviewRow) =>
  row.row.display_name || row.row.full_name || row.row.username || `Row ${row.row.source_row_number}`

const csvRowNumber = (row: { source_row_number: number }) => Math.max(1, row.source_row_number - 1)

const formatNumber = (value?: number | null) =>
  value === null || value === undefined ? null : new Intl.NumberFormat('en-US').format(value)

const platformLabel = (platform: string) =>
  platformOptions.find((option) => option.value === platform)?.label ?? platform

const previewPlatforms = (row: IngestionPreviewRow) => {
  const platforms = new Map<string, { platform: string; username?: string | null; followers?: number | null }>()
  if (row.row.platform) {
    platforms.set(row.row.platform, {
      platform: row.row.platform,
      username: row.row.username,
      followers: row.row.follower_count,
    })
  }
  row.row.social_links.forEach((link) => {
    if (!platforms.has(link.platform)) {
      platforms.set(link.platform, {
        platform: link.platform,
        username: link.username,
      })
    }
  })
  return Array.from(platforms.values())
}

const platformDisplayName = (platform: {
  platform: string
  username?: string | null
  followers?: number | null
}) => {
  const username = platform.username ? ` @${platform.username.replace(/^@/, '')}` : ''
  const followers = formatNumber(platform.followers)
  return `${platformLabel(platform.platform)}${username}${followers ? ` - ${followers}` : ''}`
}

const previewContact = (row: IngestionPreviewRow) => row.row.contacts[0] ?? null

const previewLocation = (row: IngestionPreviewRow) =>
  [row.row.country, row.row.city].filter(Boolean).join(', ') || 'No location'

const formatFileSize = (size?: number) => {
  if (!size) return '0 KB'
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

const resetImportState = () => {
  preview.value = null
  result.value = null
  error.value = null
  Object.keys(actions).forEach((key) => {
    delete actions[Number(key)]
  })
}

const setSelectedFile = (nextFile: File | null) => {
  file.value = nextFile
  resetImportState()
}

const beforeUpload: UploadProps['beforeUpload'] = (selectedFile) => {
  setSelectedFile(selectedFile)
  return false
}

const clearFile = () => {
  setSelectedFile(null)
}

const setTargetCampaign = (value?: string) => {
  targetCampaignId.value = value
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
    const confirmResult = await confirmImport({
      source_type: preview.value.source_type as ImportSourceType,
      file_name: file.value.name,
      target_campaign_id: targetCampaignId.value ?? null,
      rows: preview.value.rows.map((previewRow) => {
        const action = actions[previewRow.row.source_row_number] ?? defaultActionForRow(previewRow)
        return {
          row: previewRow.row,
          action,
          existing_influencer_id: action === 'merge' ? previewRow.dedup.influencer_id ?? null : null,
        }
      }),
    })
    result.value = confirmResult
    if (targetCampaignId.value && confirmResult.created_deals > 0) {
      emit('campaignChanged', targetCampaignId.value)
    }
  } catch (confirmError) {
    error.value = errorMessage(confirmError)
  } finally {
    confirming.value = false
  }
}
</script>

<template>
  <section class="import-page">
    <div class="page-heading">
      <div>
        <a-breadcrumb>
          <a-breadcrumb-item>
            <RouterLink :to="{ name: 'influencers' }">Influencers</RouterLink>
          </a-breadcrumb-item>
          <a-breadcrumb-item>Import CSV</a-breadcrumb-item>
        </a-breadcrumb>
        <h1>Import influencers</h1>
        <p class="page-description">
          Import Modash CSV rows into the Influencer Library, then optionally create campaign deal rows
          for the selected campaign.
        </p>
      </div>
    </div>

    <a-alert v-if="error" class="page-alert" type="error" :message="error" show-icon />

    <a-card class="setup-card" title="Upload and setup">
      <div class="setup-grid">
        <div class="upload-panel">
          <a-upload-dragger
            accept=".csv,text/csv"
            :before-upload="beforeUpload"
            :file-list="uploadFileList"
            :max-count="1"
            :show-upload-list="false"
          >
            <p class="upload-icon">
              <UploadCloud aria-hidden="true" />
            </p>
            <p class="upload-title">Drop a Modash CSV here or select a file</p>
            <p class="upload-help">CSV files are parsed in preview before anything is written.</p>
          </a-upload-dragger>

          <div v-if="file" class="selected-file">
            <FileText class="selected-file-icon" aria-hidden="true" />
            <div>
              <strong>{{ file.name }}</strong>
              <span>{{ file.type || 'text/csv' }} - {{ formatFileSize(file.size) }}</span>
            </div>
            <a-button type="text" title="Clear selected file" aria-label="Clear selected file" @click="clearFile">
              <X aria-hidden="true" />
            </a-button>
          </div>
        </div>

        <div class="setup-controls">
          <label class="field-label" for="target-campaign">Target campaign</label>
          <a-select
            id="target-campaign"
            allow-clear
            placeholder="Optional: choose a campaign"
            :value="targetCampaignId"
            :options="campaignOptions"
            @change="setTargetCampaign"
          />
          <p class="field-help">{{ campaignImportHelp }}</p>
          <a-button type="primary" :disabled="!file || previewing" :loading="previewing" @click="runPreview">
            <Import class="button-leading-icon" aria-hidden="true" />
            Preview CSV
          </a-button>
        </div>
      </div>
    </a-card>

    <a-card v-if="preview" class="review-card" :body-style="{ padding: '0' }">
      <template #title>
        <div class="card-title-block">
          <span>Review rows</span>
          <small>
            {{
              selectedCampaignName
                ? `Rows will update the library and create missing deals in ${selectedCampaignName}.`
                : 'Rows will update the global library only. No campaign deals will be created.'
            }}
          </small>
        </div>
      </template>
      <div class="review-body">
        <div class="summary-grid">
          <div class="summary-item">
            <span>Parsed rows</span>
            <strong>{{ preview.row_count }}</strong>
          </div>
          <div class="summary-item">
            <span>Create</span>
            <strong>{{ actionCounts.create }}</strong>
          </div>
          <div class="summary-item">
            <span>Merge</span>
            <strong>{{ actionCounts.merge }}</strong>
          </div>
          <div class="summary-item">
            <span>Skip</span>
            <strong>{{ actionCounts.skip }}</strong>
          </div>
          <div class="summary-item">
            <span>Errors</span>
            <strong>{{ previewErrorCount }}</strong>
          </div>
        </div>

        <a-alert v-if="preview.fatal_errors.length" class="page-alert" type="error" show-icon>
          <template #message>Fatal import errors</template>
          <template #description>
            <ul class="alert-list">
              <li v-for="fatalError in preview.fatal_errors" :key="fatalError">{{ fatalError }}</li>
            </ul>
          </template>
        </a-alert>
      </div>

      <a-table
        :columns="previewColumns"
        :data-source="preview.rows"
        :pagination="{ pageSize: 10, showSizeChanger: true }"
        :row-key="(record: IngestionPreviewRow) => record.row.source_row_number"
        :scroll="{ x: 1460 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'row'">
            {{ csvRowNumber(record.row) }}
          </template>

          <template v-else-if="column.key === 'influencer'">
            <div class="influencer-cell">
              <strong>{{ rowTitle(record) }}</strong>
              <span v-if="record.row.full_name && record.row.full_name !== rowTitle(record)">
                {{ record.row.full_name }}
              </span>
            </div>
          </template>

          <template v-else-if="column.key === 'platforms'">
            <div v-if="previewPlatforms(record).length" class="platform-stack">
              <a-tag
                v-for="platform in previewPlatforms(record)"
                :key="`${record.row.source_row_number}:${platform.platform}:${platform.username ?? ''}`"
                :color="platformColor(platform.platform)"
              >
                {{ platformDisplayName(platform) }}
              </a-tag>
            </div>
            <span v-else class="muted">No platforms</span>
          </template>

          <template v-else-if="column.key === 'contact'">
            <div v-if="previewContact(record)" class="contact-cell">
              <span>{{ previewContact(record)?.email }}</span>
              <small>{{ previewContact(record)?.source }}</small>
            </div>
            <span v-else class="muted">No contact</span>
          </template>

          <template v-else-if="column.key === 'location'">
            <span>{{ previewLocation(record) }}</span>
          </template>

          <template v-else-if="column.key === 'importStatus'">
            <div class="stacked-cell">
              <a-tag :color="previewStatusColor(record)">{{ previewStatusLabel(record) }}</a-tag>
              <span>{{ record.dedup.reason || 'No match found' }}</span>
            </div>
          </template>

          <template v-else-if="column.key === 'action'">
            <a-select v-model:value="actions[record.row.source_row_number]" class="row-action-select">
              <a-select-option value="create">Create</a-select-option>
              <a-select-option :disabled="!record.dedup.influencer_id" value="merge">Merge</a-select-option>
              <a-select-option value="skip">Skip</a-select-option>
            </a-select>
          </template>

          <template v-else-if="column.key === 'importNotes'">
            <div class="message-list">
              <span v-for="message in record.row.parse_errors" :key="message" class="danger-text">
                {{ message }}
              </span>
              <span v-for="message in record.row.warnings" :key="message">{{ message }}</span>
              <span v-if="!record.row.parse_errors.length && !record.row.warnings.length">Ready</span>
            </div>
          </template>
        </template>
      </a-table>

      <div class="review-actions">
        <a-button type="primary" :disabled="!preview || confirming" :loading="confirming" @click="runConfirm">
          Confirm import
        </a-button>
      </div>

      <div v-if="result" class="result-section">
        <a-alert class="page-alert" type="success" show-icon>
          <template #message>Import complete</template>
          <template #description>
            {{ result.imported_count }} imported, {{ result.skipped_count }} skipped,
            {{ result.conflict_count }} conflicts, {{ result.created_deals }} campaign deals created.
          </template>
        </a-alert>

        <a-table
          size="small"
          :columns="resultColumns"
          :data-source="result.rows"
          :pagination="{ pageSize: 8, size: 'small' }"
          :row-key="(record: IngestionRowResult) => record.source_row_number"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'row'">
              {{ csvRowNumber(record) }}
            </template>

            <template v-else-if="column.key === 'action'">
              <a-tag :color="actionColor(record.action)">{{ record.action }}</a-tag>
            </template>

            <template v-else-if="column.key === 'status'">
              <a-tag :color="resultStatusColor(record.status)">{{ record.status }}</a-tag>
            </template>

            <template v-else-if="column.key === 'resultNotes'">
              <div class="message-list">
                <span v-for="message in record.errors" :key="message" class="danger-text">
                  {{ message }}
                </span>
                <span v-for="message in record.warnings" :key="message">{{ message }}</span>
                <span v-if="!record.errors.length && !record.warnings.length">Ready</span>
              </div>
            </template>
          </template>
        </a-table>
      </div>
    </a-card>
  </section>
</template>

<style scoped>
.import-page {
  display: grid;
  gap: 18px;
}

.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-heading :deep(.ant-breadcrumb) {
  margin-bottom: 8px;
}

h1 {
  margin: 0;
  color: #20262d;
  font-size: 30px;
}

.page-description {
  max-width: 760px;
  margin: 8px 0 0;
  color: #58636f;
  line-height: 1.5;
}

.page-alert {
  border-radius: 8px;
}

.setup-card,
.review-card {
  overflow: hidden;
}

.setup-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 340px);
  gap: 18px;
  align-items: start;
}

.upload-panel {
  display: grid;
  gap: 12px;
}

.upload-icon {
  margin: 0 0 8px;
  color: #215f4e;
}

.upload-icon svg {
  width: 32px;
  height: 32px;
}

.upload-title {
  margin: 0;
  color: #20262d;
  font-weight: 700;
}

.upload-help {
  margin: 4px 0 0;
  color: #697582;
}

.selected-file {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #e4e9f1;
  border-radius: 8px;
  background: #f8fafc;
}

.selected-file-icon {
  width: 18px;
  height: 18px;
  color: #215f4e;
}

.selected-file strong,
.summary-item strong,
.stacked-cell strong {
  display: block;
  color: #20262d;
}

.selected-file span,
.field-help,
.card-title-block small,
.summary-item span,
.stacked-cell span,
.message-list {
  color: #697582;
  font-size: 12px;
}

.selected-file :deep(.ant-btn) {
  width: 30px;
  height: 30px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.selected-file :deep(.ant-btn svg) {
  width: 16px;
  height: 16px;
}

.setup-controls {
  display: grid;
  gap: 10px;
}

.field-label {
  color: #38414a;
  font-size: 12px;
  font-weight: 700;
}

.field-help {
  margin: -2px 0 4px;
  line-height: 1.5;
}

.button-leading-icon {
  width: 16px;
  height: 16px;
  margin-right: 6px;
  vertical-align: -3px;
}

.influencer-cell,
.card-title-block,
.stacked-cell,
.message-list {
  display: grid;
  gap: 4px;
}

.influencer-cell span,
.contact-cell small,
.muted {
  color: #697582;
}

.platform-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.contact-cell {
  display: grid;
  gap: 2px;
}

.review-body {
  display: grid;
  gap: 14px;
  padding: 16px;
  border-bottom: 1px solid #edf0f5;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(120px, 1fr));
  gap: 10px;
}

.summary-item {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid #e4e9f1;
  border-radius: 8px;
  background: #f8fafc;
}

.summary-item strong {
  font-size: 22px;
}

.alert-list {
  margin: 0;
  padding-left: 18px;
}

.row-action-select {
  width: 130px;
}

.danger-text {
  color: #b42318;
}

.review-card :deep(.ant-table-wrapper) {
  max-width: 100%;
  min-width: 0;
}

.review-card :deep(.ant-table-pagination) {
  padding-inline: 14px;
}

.review-actions {
  display: flex;
  justify-content: flex-end;
  padding: 14px 16px;
  border-top: 1px solid #edf0f5;
}

.result-section {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid #edf0f5;
}

@media (max-width: 1080px) {
  .setup-grid,
  .summary-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .review-card :deep(.ant-card-head) {
    align-items: flex-start;
  }

  .review-card :deep(.ant-card-head-wrapper) {
    display: grid;
    gap: 12px;
  }

  .review-card :deep(.ant-card-extra) {
    margin-left: 0;
  }
}
</style>
