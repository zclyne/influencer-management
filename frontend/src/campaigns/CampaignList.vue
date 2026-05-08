<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal, type FormInstance, type TableColumnsType } from 'ant-design-vue'
import type { CampaignCreateRequest, CampaignResponse, CampaignStatus } from '../api/types'
import { normalizeTags } from '../shared/tags'
import { campaignStatusLabels, campaignStatuses, useCampaigns } from './useCampaigns'

interface CampaignCreateForm {
  name: string
  status: CampaignStatus
  budget: number | null
  startDate: string | null
  endDate: string | null
  brief: string
  notes: string
  tags: string[]
}

const router = useRouter()
const formRef = ref<FormInstance>()
const createModalOpen = ref(false)
const createForm = reactive<CampaignCreateForm>({
  name: '',
  status: 'PLANNING',
  budget: null,
  startDate: null,
  endDate: null,
  brief: '',
  notes: '',
  tags: [],
})

const {
  visibleCampaigns,
  loading,
  creating,
  archiving,
  error,
  searchText,
  statusFilter,
  tagFilter,
  includeArchived,
  selectedRowKeys,
  activeCampaignCount,
  planningCampaignCount,
  liveCampaignCount,
  archivedCampaignCount,
  tagOptions,
  loadCampaigns,
  createNewCampaign,
  archiveCampaign,
  archiveSelectedCampaigns,
} = useCampaigns()

const columns: TableColumnsType<CampaignResponse> = [
  {
    title: 'Campaign',
    key: 'campaign',
    dataIndex: 'name',
    width: 280,
  },
  {
    title: 'Brands',
    key: 'brands',
    width: 240,
  },
  {
    title: 'Tags',
    key: 'tags',
    width: 220,
  },
  {
    title: 'Status',
    key: 'status',
    dataIndex: 'status',
    width: 160,
    filters: campaignStatuses.map((status) => ({
      text: campaignStatusLabels[status],
      value: status,
    })),
    onFilter: (value, record) => record.status === value,
  },
  {
    title: 'Budget',
    key: 'budget',
    dataIndex: 'budget',
    align: 'right',
    width: 140,
  },
  {
    title: 'Updated',
    key: 'updated',
    dataIndex: 'updated_at',
    width: 140,
    sorter: (left, right) =>
      new Date(left.updated_at).getTime() - new Date(right.updated_at).getTime(),
  },
  {
    title: 'Actions',
    key: 'actions',
    fixed: 'right',
    width: 140,
  },
]

const statusOptions = computed(() =>
  campaignStatuses.map((status) => ({
    label: campaignStatusLabels[status],
    value: status,
  })),
)

const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: (string | number)[]) => {
    selectedRowKeys.value = keys.map(String)
  },
  getCheckboxProps: (record: CampaignResponse) => ({
    disabled: Boolean(record.archived_at),
  }),
}))

const formatCurrency = (value: CampaignResponse['budget']) => {
  if (value === null || value === undefined || value === '') return 'Not set'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return String(value)

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount)
}

const formatDate = (value: string) =>
  new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))

const statusColor = (status: CampaignStatus) => {
  if (status === 'ACTIVE') return 'green'
  if (status === 'EVALUATING') return 'gold'
  if (status === 'CLOSED') return 'default'
  return 'blue'
}

const statusLabel = (status: CampaignStatus) => campaignStatusLabels[status]

const resetCreateForm = () => {
  createForm.name = ''
  createForm.status = 'PLANNING'
  createForm.budget = null
  createForm.startDate = null
  createForm.endDate = null
  createForm.brief = ''
  createForm.notes = ''
  createForm.tags = []
  formRef.value?.clearValidate()
}

const buildCreatePayload = (): CampaignCreateRequest => {
  const tags = normalizeTags(createForm.tags)
  return {
    name: createForm.name.trim(),
    status: createForm.status,
    budget: createForm.budget,
    start_date: createForm.startDate,
    end_date: createForm.endDate,
    brief: createForm.brief.trim() || null,
    notes: createForm.notes.trim() || null,
    tags,
  }
}

const openCreateModal = () => {
  createModalOpen.value = true
}

const submitCreate = async () => {
  await formRef.value?.validate()

  try {
    const created = await createNewCampaign(buildCreatePayload())
    message.success('Campaign created.')
    createModalOpen.value = false
    resetCreateForm()
    await router.push({ name: 'campaignWorkspace', params: { campaignId: created.id } })
  } catch (createError) {
    message.error(
      createError instanceof Error ? createError.message : 'Campaign could not be created.',
    )
  }
}

const archiveOne = async (campaign: CampaignResponse) => {
  try {
    await archiveCampaign(campaign.id)
    message.success(`${campaign.name} deleted.`)
  } catch {
    message.error(`${campaign.name} could not be deleted.`)
  }
}

const confirmBulkArchive = () => {
  if (!selectedRowKeys.value.length) return

  Modal.confirm({
    title: 'Delete selected campaigns?',
    content: 'Deleted campaigns are hidden unless Include deleted is turned on.',
    okText: 'Delete selected',
    okType: 'danger',
    cancelText: 'Cancel',
    onOk: async () => {
      const result = await archiveSelectedCampaigns()
      if (result.failed) {
        message.error(`${result.failed} campaign(s) could not be deleted.`)
      }
      if (result.archived) {
        message.success(`${result.archived} campaign(s) deleted.`)
      }
    },
  })
}

watch(createModalOpen, (open) => {
  if (!open) resetCreateForm()
})

void loadCampaigns()
</script>

<template>
  <section class="campaign-list-page">
    <div class="page-heading">
      <div>
        <h1>Campaign list</h1>
        <p class="page-description">
          Open campaigns to manage deals, add influencers from the library, and use campaign-scoped export.
        </p>
      </div>
    </div>

    <a-alert v-if="error" class="page-alert" type="error" :message="error" show-icon />

    <div class="summary-grid">
      <a-card size="small">
        <span>Current campaigns</span>
        <strong>{{ activeCampaignCount }}</strong>
      </a-card>
      <a-card size="small">
        <span>Planning</span>
        <strong>{{ planningCampaignCount }}</strong>
      </a-card>
      <a-card size="small">
        <span>Active</span>
        <strong>{{ liveCampaignCount }}</strong>
      </a-card>
      <a-card v-if="includeArchived" size="small">
        <span>Deleted</span>
        <strong>{{ archivedCampaignCount }}</strong>
      </a-card>
    </div>

    <a-card class="table-card" :body-style="{ padding: '0' }">
      <div class="table-toolbar">
        <div class="table-toolbar-controls">
          <a-input-search
            v-model:value="searchText"
            class="search-input"
            allow-clear
            placeholder="Search campaigns or brands"
          />
          <a-select
            v-model:value="statusFilter"
            class="status-filter"
            allow-clear
            placeholder="All statuses"
            :options="statusOptions"
          />
          <a-select
            v-model:value="tagFilter"
            class="tag-filter"
            allow-clear
            placeholder="All tags"
            :options="tagOptions"
          />
          <label class="archive-toggle">
            <span>Include deleted</span>
            <a-switch v-model:checked="includeArchived" />
          </label>
        </div>
        <div class="table-toolbar-actions">
          <a-button
            danger
            :disabled="!selectedRowKeys.length || archiving"
            :loading="archiving"
            @click="confirmBulkArchive"
          >
            Delete selected
          </a-button>
          <a-button type="primary" @click="openCreateModal">New campaign</a-button>
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="visibleCampaigns"
        :loading="loading"
        :pagination="{ pageSize: 10, showSizeChanger: true }"
        :row-key="(record: CampaignResponse) => record.id"
        :row-selection="rowSelection"
        :scroll="{ x: 1300 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'campaign'">
            <div class="campaign-cell">
              <RouterLink :to="{ name: 'campaignWorkspace', params: { campaignId: record.id } }">
                {{ record.name }}
              </RouterLink>
              <span v-if="record.brief">{{ record.brief }}</span>
            </div>
          </template>

          <template v-else-if="column.key === 'brands'">
            <div v-if="record.brands.length" class="tag-row">
              <a-tag v-for="link in record.brands" :key="link.id">{{ link.brand.name }}</a-tag>
            </div>
            <span v-else class="muted">No brands</span>
          </template>

          <template v-else-if="column.key === 'tags'">
            <div v-if="record.tags.length" class="tag-row">
              <a-tag v-for="tag in record.tags" :key="tag">{{ tag }}</a-tag>
            </div>
            <span v-else class="muted">No tags</span>
          </template>

          <template v-else-if="column.key === 'status'">
            <div class="tag-row">
              <a-tag :color="statusColor(record.status)">
                {{ statusLabel(record.status) }}
              </a-tag>
              <a-tag v-if="record.archived_at" color="red">Deleted</a-tag>
            </div>
          </template>

          <template v-else-if="column.key === 'budget'">
            <span>{{ formatCurrency(record.budget) }}</span>
          </template>

          <template v-else-if="column.key === 'updated'">
            <span>{{ formatDate(record.updated_at) }}</span>
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-popconfirm
              v-if="!record.archived_at"
              title="Delete this campaign?"
              ok-text="Delete"
              cancel-text="Cancel"
              @confirm="archiveOne(record)"
            >
              <a-button danger type="link">Delete</a-button>
            </a-popconfirm>
            <span v-else class="muted">Deleted</span>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="createModalOpen"
      title="New campaign"
      ok-text="Create campaign"
      cancel-text="Cancel"
      :confirm-loading="creating"
      destroy-on-close
      @ok="submitCreate"
    >
      <a-form ref="formRef" :model="createForm" layout="vertical">
        <a-form-item
          label="Name"
          name="name"
          :rules="[{ required: true, message: 'Campaign name is required.' }]"
        >
          <a-input v-model:value="createForm.name" placeholder="Spring launch" />
        </a-form-item>

        <a-form-item label="Status" name="status">
          <a-select v-model:value="createForm.status" :options="statusOptions" />
        </a-form-item>

        <a-form-item label="Budget" name="budget">
          <a-input-number
            v-model:value="createForm.budget"
            :min="0"
            :precision="2"
            placeholder="0"
            class="full-width"
          />
        </a-form-item>

        <div class="form-grid">
          <a-form-item label="Start date" name="startDate">
            <a-date-picker
              v-model:value="createForm.startDate"
              value-format="YYYY-MM-DD"
              class="full-width"
            />
          </a-form-item>
          <a-form-item label="End date" name="endDate">
            <a-date-picker
              v-model:value="createForm.endDate"
              value-format="YYYY-MM-DD"
              class="full-width"
            />
          </a-form-item>
        </div>

        <a-form-item label="Brief" name="brief">
          <a-textarea v-model:value="createForm.brief" :rows="3" />
        </a-form-item>

        <a-form-item label="Notes" name="notes">
          <a-textarea v-model:value="createForm.notes" :rows="3" />
        </a-form-item>

        <a-form-item label="Tags" name="tags">
          <a-select
            v-model:value="createForm.tags"
            mode="tags"
            placeholder="Add campaign tags"
            :max-tag-count="8"
          />
          <p class="form-help">
            Use up to 20 tags. Tags support letters, numbers, spaces, -, _, /, ., and &.
          </p>
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>

<style scoped>
.campaign-list-page {
  display: grid;
  gap: 18px;
}

.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

h1 {
  margin: 0;
  color: #20262d;
  font-size: 30px;
}

.page-description {
  max-width: 720px;
  margin: 8px 0 0;
  color: #58636f;
  line-height: 1.5;
}

.page-alert {
  border-radius: 8px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr));
  gap: 12px;
}

.summary-grid :deep(.ant-card-body) {
  display: grid;
  gap: 6px;
}

.summary-grid span,
.muted {
  color: #697582;
}

.summary-grid strong {
  color: #20262d;
  font-size: 26px;
}

.table-card {
  overflow: hidden;
}

.table-card :deep(.ant-card-body) {
  min-width: 0;
  overflow-x: auto;
}

.table-card :deep(.ant-table-wrapper) {
  max-width: 100%;
  min-width: 0;
}

.table-card :deep(.ant-table-pagination) {
  padding-inline: 14px;
}

.table-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-bottom: 1px solid #edf0f5;
}

.table-toolbar-controls,
.table-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.table-toolbar-controls {
  flex-wrap: nowrap;
}

.table-toolbar-actions {
  flex-wrap: nowrap;
  justify-content: flex-end;
}

.search-input {
  width: min(300px, 100%);
}

.status-filter,
.tag-filter {
  width: 160px;
}

.archive-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #4e5965;
  white-space: nowrap;
}

.campaign-cell {
  display: grid;
  gap: 4px;
}

.campaign-cell a {
  color: #175fcb;
  font-weight: 700;
}

.campaign-cell span {
  max-width: 420px;
  overflow: hidden;
  color: #697582;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.full-width {
  width: 100%;
}

.form-help {
  margin: 6px 0 0;
  color: #697582;
  font-size: 12px;
  line-height: 1.4;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .table-toolbar {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .table-toolbar-controls,
  .table-toolbar-actions {
    flex-wrap: wrap;
  }

  .search-input,
  .status-filter,
  .tag-filter,
  .archive-toggle,
  .table-toolbar-actions,
  .table-toolbar-actions button {
    width: 100%;
  }
}

@media (max-width: 560px) {
  .summary-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
