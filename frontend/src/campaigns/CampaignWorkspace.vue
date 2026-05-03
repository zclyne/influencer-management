<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { message, Modal, type FormInstance, type TableColumnsType } from 'ant-design-vue'
import type {
  CampaignStatus,
  CampaignUpdateRequest,
  DealPipelineRow,
  DealStatus,
  InfluencerListItem,
  PrimaryPlatformSummary,
} from '../api/types'
import DealDetailDrawer from '../deals/DealDetailDrawer.vue'
import {
  platformColor,
  platformOptions as libraryPlatformOptions,
  useInfluencers,
} from '../influencers/useInfluencers'
import {
  dealStatuses,
  dealStatusLabels,
  useCampaignWorkspace,
} from './useCampaignWorkspace'
import { campaignStatusLabels, campaignStatuses } from './useCampaigns'

interface CampaignEditForm {
  name: string
  status: CampaignStatus
  budget: number | null
  startDate: string | null
  endDate: string | null
  brief: string
  notes: string
}

const route = useRoute()
const router = useRouter()
const campaignId = computed(() => String(route.params.campaignId ?? ''))
const campaignFormRef = ref<FormInstance>()
const addFromLibraryOpen = ref(false)
const campaignEditOpen = ref(false)
const bulkStatus = ref<DealStatus | undefined>()

const campaignForm = reactive<CampaignEditForm>({
  name: '',
  status: 'PLANNING',
  budget: null,
  startDate: null,
  endDate: null,
  brief: '',
  notes: '',
})

const {
  campaign,
  visibleDeals,
  loading,
  mutating,
  exporting,
  error,
  searchText,
  statusFilter,
  platformFilter,
  includeArchived,
  selectedRowKeys,
  selectedDeal,
  totalDealCount,
  inProgressDealCount,
  pendingReviewCount,
  plannedSpend,
  platformOptions,
  loadWorkspace,
  selectDeal,
  updateCampaignProfile,
  archiveCampaignProfile,
  addInfluencersToCampaign,
  bulkUpdateSelectedDeals,
  archiveDeal,
  archiveSelectedDeals,
  exportCurrentView,
} = useCampaignWorkspace(() => campaignId.value)

const {
  influencers,
  loading: influencersLoading,
  searchText: influencerSearchText,
  platformFilter: influencerPlatformFilter,
  selectedRowKeys: selectedInfluencerRowKeys,
  loadInfluencers,
} = useInfluencers()

const columns: TableColumnsType<DealPipelineRow> = [
  {
    title: 'Creator',
    key: 'creator',
    width: 260,
  },
  {
    title: 'Platforms',
    key: 'platforms',
    width: 300,
  },
  {
    title: 'Status',
    key: 'status',
    dataIndex: 'status',
    width: 150,
    filters: dealStatuses.map((status) => ({
      text: dealStatusLabels[status],
      value: status,
    })),
    onFilter: (value, record) => record.status === value,
  },
  {
    title: 'Deliverables',
    key: 'deliverables',
    width: 180,
  },
  {
    title: 'Cost',
    key: 'cost',
    width: 170,
  },
  {
    title: 'Updated',
    key: 'updated',
    dataIndex: 'updated_at',
    sorter: (left, right) =>
      new Date(left.updated_at).getTime() - new Date(right.updated_at).getTime(),
    width: 140,
  },
  {
    title: 'Actions',
    key: 'actions',
    fixed: 'right',
    width: 250,
  },
]

const influencerColumns: TableColumnsType<InfluencerListItem> = [
  {
    title: 'Influencer',
    key: 'influencer',
    dataIndex: 'display_name',
  },
  {
    title: 'Platforms',
    key: 'platforms',
  },
  {
    title: 'Contact',
    key: 'contact',
  },
  {
    title: 'Location',
    key: 'location',
  },
]

const statusOptions = computed(() =>
  dealStatuses.map((status) => ({
    label: dealStatusLabels[status],
    value: status,
  })),
)

const campaignStatusOptions = computed(() =>
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
  getCheckboxProps: (record: DealPipelineRow) => ({
    disabled: Boolean(record.archived_at),
  }),
}))

const influencerRowSelection = computed(() => ({
  selectedRowKeys: selectedInfluencerRowKeys.value,
  onChange: (keys: (string | number)[]) => {
    selectedInfluencerRowKeys.value = keys.map(String)
  },
  getCheckboxProps: (record: InfluencerListItem) => ({
    disabled: Boolean(record.archived_at),
  }),
}))

const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return null
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(
    value,
  )
}

const formatCurrency = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === '') return 'Not set'
  const amount = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(amount)) return String(value)

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount)
}

const formatDate = (value: string | null | undefined) => {
  if (!value) return 'Not set'
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))
}

const formatDateRange = () => {
  const start = formatDate(campaign.value?.start_date)
  const end = formatDate(campaign.value?.end_date)
  if (start === 'Not set' && end === 'Not set') return 'Not set'
  if (start === 'Not set') return `Ends ${end}`
  if (end === 'Not set') return `Starts ${start}`
  return `${start} - ${end}`
}

const formatLocation = (record: InfluencerListItem) =>
  [record.city, record.country].filter(Boolean).join(', ') || 'Not set'

const platformDisplayName = (platform: PrimaryPlatformSummary) => {
  const username = platform.username ? ` @${platform.username}` : ''
  const followers = formatNumber(platform.follower_count)
  return `${platform.platform}${username}${followers ? ` · ${followers}` : ''}`
}

const libraryPlatformDisplayName = (platform: InfluencerListItem['platforms'][number]) => {
  const followers = formatNumber(platform.follower_count)
  return `${platform.platform}${platform.username ? ` @${platform.username}` : ''}${followers ? ` · ${followers}` : ''}`
}

const statusColor = (status: DealStatus) => {
  if (status === 'ACTIVE' || status === 'COMPLETED') return 'green'
  if (status === 'NEGOTIATING' || status === 'RESPONDED') return 'gold'
  if (status === 'LOST') return 'red'
  if (status === 'OUTREACHED') return 'blue'
  return 'default'
}

const statusLabel = (status: DealStatus) => dealStatusLabels[status]

const campaignStatusColor = (status: CampaignStatus) => {
  if (status === 'ACTIVE') return 'green'
  if (status === 'EVALUATING') return 'gold'
  if (status === 'CLOSED') return 'default'
  return 'blue'
}

const campaignStatusLabel = (status: CampaignStatus) => campaignStatusLabels[status]

const brandLabel = computed(() => {
  if (!campaign.value?.brands.length) return 'No brands'
  return campaign.value.brands.map((link) => link.brand.name).join(', ')
})

const resetCampaignForm = () => {
  const budgetValue =
    campaign.value?.budget === null || campaign.value?.budget === undefined
      ? null
      : Number(campaign.value.budget)
  campaignForm.name = campaign.value?.name ?? ''
  campaignForm.status = campaign.value?.status ?? 'PLANNING'
  campaignForm.budget = budgetValue === null || !Number.isFinite(budgetValue) ? null : budgetValue
  campaignForm.startDate = campaign.value?.start_date ?? null
  campaignForm.endDate = campaign.value?.end_date ?? null
  campaignForm.brief = campaign.value?.brief ?? ''
  campaignForm.notes = campaign.value?.notes ?? ''
  campaignFormRef.value?.clearValidate()
}

const buildCampaignPayload = (): CampaignUpdateRequest => ({
  name: campaignForm.name.trim(),
  status: campaignForm.status,
  budget: campaignForm.budget,
  start_date: campaignForm.startDate,
  end_date: campaignForm.endDate,
  brief: campaignForm.brief.trim() || null,
  notes: campaignForm.notes.trim() || null,
})

const openCampaignEdit = () => {
  resetCampaignForm()
  campaignEditOpen.value = true
}

const submitCampaignEdit = async () => {
  await campaignFormRef.value?.validate()

  try {
    await updateCampaignProfile(buildCampaignPayload())
    message.success('Campaign updated.')
    campaignEditOpen.value = false
  } catch {
    message.error('Campaign could not be updated.')
  }
}

const confirmCampaignDelete = () => {
  if (!campaign.value) return

  Modal.confirm({
    title: 'Delete this campaign?',
    content: 'Deleted campaigns are hidden from the default list but remain available in history.',
    okText: 'Delete',
    okType: 'danger',
    cancelText: 'Cancel',
    async onOk() {
      try {
        await archiveCampaignProfile()
        message.success(`${campaign.value?.name ?? 'Campaign'} deleted.`)
        await router.push({ name: 'campaigns' })
      } catch {
        message.error('Campaign could not be deleted.')
      }
    },
  })
}

const openAddFromLibrary = async () => {
  selectedInfluencerRowKeys.value = []
  addFromLibraryOpen.value = true
  await loadInfluencers()
}

const submitAddFromLibrary = async () => {
  try {
    const result = await addInfluencersToCampaign(selectedInfluencerRowKeys.value)
    if (!result) return

    message.success(
      `${result.created_count} deal(s) created, ${result.skipped_count} already existed.`,
    )
    addFromLibraryOpen.value = false
    selectedInfluencerRowKeys.value = []
  } catch {
    message.error('Influencers could not be added to this campaign.')
  }
}

const applyBulkStatus = async () => {
  if (!bulkStatus.value || !selectedRowKeys.value.length) return

  try {
    const result = await bulkUpdateSelectedDeals({
      status: bulkStatus.value,
    })
    if (result) {
      message.success(`${result.updated_count} deal(s) updated.`)
      bulkStatus.value = undefined
    }
  } catch {
    message.error('Selected deals could not be updated.')
  }
}

const archiveOne = async (deal: DealPipelineRow) => {
  try {
    await archiveDeal(deal.id)
    message.success(`${deal.influencer.display_name} deleted from campaign.`)
  } catch {
    message.error(`${deal.influencer.display_name} could not be deleted.`)
  }
}

const confirmBulkArchive = () => {
  if (!selectedRowKeys.value.length) return

  Modal.confirm({
    title: 'Delete selected deals?',
    content: 'Deleted deals are hidden unless Include deleted is turned on.',
    okText: 'Delete selected',
    okType: 'danger',
    cancelText: 'Cancel',
    onOk: async () => {
      const result = await archiveSelectedDeals()
      if (result.failed) {
        message.error(`${result.failed} deal(s) could not be deleted.`)
      }
      if (result.archived) {
        message.success(`${result.archived} deal(s) deleted.`)
      }
    },
  })
}

const downloadExport = async () => {
  try {
    const blob = await exportCurrentView()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `campaign-${campaignId.value}.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch {
    message.error('Campaign export could not be generated.')
  }
}

watch(campaignId, () => {
  selectedRowKeys.value = []
  selectDeal(null)
  void loadWorkspace()
})

void loadWorkspace()
</script>

<template>
  <section class="workspace-page">
    <a-breadcrumb>
      <a-breadcrumb-item>
        <RouterLink :to="{ name: 'campaigns' }">Campaigns</RouterLink>
      </a-breadcrumb-item>
      <a-breadcrumb-item>{{ campaign?.name ?? 'Campaign workspace' }}</a-breadcrumb-item>
    </a-breadcrumb>

    <div class="page-heading">
      <div>
        <h1>{{ campaign?.name ?? 'Campaign workspace' }}</h1>
        <div v-if="campaign" class="campaign-status-row">
          <a-tag :color="campaignStatusColor(campaign.status)">
            {{ campaignStatusLabel(campaign.status) }}
          </a-tag>
          <a-tag v-if="campaign.archived_at" color="red">Deleted</a-tag>
          <span>Updated {{ formatDate(campaign.updated_at) }}</span>
        </div>
      </div>
      <div class="page-actions">
        <a-button :disabled="!campaign || Boolean(campaign.archived_at)" @click="openCampaignEdit">
          Edit campaign
        </a-button>
        <a-button
          danger
          :disabled="!campaign || Boolean(campaign.archived_at)"
          :loading="mutating"
          @click="confirmCampaignDelete"
        >
          Delete campaign
        </a-button>
        <RouterLink :to="{ name: 'email', query: { campaignId } }">
          <a-button>Open email</a-button>
        </RouterLink>
        <a-button type="primary" :loading="exporting" @click="downloadExport">Export view</a-button>
      </div>
    </div>

    <a-alert v-if="error" class="page-alert" type="error" :message="error" show-icon />

    <div v-if="campaign" class="campaign-overview">
      <a-card size="small">
        <span>Budget</span>
        <strong>{{ formatCurrency(campaign.budget) }}</strong>
      </a-card>
      <a-card size="small">
        <span>Timeline</span>
        <strong>{{ formatDateRange() }}</strong>
      </a-card>
      <a-card size="small">
        <span>Brands</span>
        <strong>{{ brandLabel }}</strong>
      </a-card>
      <a-card size="small">
        <span>Notes</span>
        <strong>{{ campaign.notes || 'No notes' }}</strong>
      </a-card>
    </div>

    <a-card v-if="campaign" class="campaign-brief-card" size="small">
      <template #title>Brief</template>
      <p>{{ campaign.brief || 'No brief yet.' }}</p>
    </a-card>

    <div class="summary-grid">
      <a-card size="small">
        <span>Deals</span>
        <strong>{{ totalDealCount }}</strong>
      </a-card>
      <a-card size="small">
        <span>In progress</span>
        <strong>{{ inProgressDealCount }}</strong>
      </a-card>
      <a-card size="small">
        <span>Pending review</span>
        <strong>{{ pendingReviewCount }}</strong>
      </a-card>
      <a-card size="small">
        <span>Planned spend</span>
        <strong>{{ formatCurrency(plannedSpend) }}</strong>
      </a-card>
    </div>

    <a-card class="table-card" :body-style="{ padding: '0' }">
      <div class="table-title-row">
        <div>
          <h2>Deals</h2>
          <p>Add influencers from the library to create campaign deals.</p>
        </div>
        <a-button
          type="primary"
          :disabled="!campaign || Boolean(campaign.archived_at)"
          @click="openAddFromLibrary"
        >
          Add influencers from library
        </a-button>
      </div>

      <div class="table-toolbar">
        <div class="table-toolbar-controls">
          <a-input-search
            v-model:value="searchText"
            class="search-input"
            allow-clear
            placeholder="Search deals"
          />
          <a-select
            v-model:value="statusFilter"
            class="status-filter"
            allow-clear
            placeholder="All statuses"
            :options="statusOptions"
          />
          <a-select
            v-model:value="platformFilter"
            class="platform-filter"
            allow-clear
            placeholder="All platforms"
            :options="platformOptions"
          />
          <label class="archive-toggle">
            <span>Include deleted</span>
            <a-switch v-model:checked="includeArchived" />
          </label>
        </div>
        <div class="table-toolbar-actions">
          <a-select
            v-model:value="bulkStatus"
            class="bulk-status"
            allow-clear
            placeholder="Set status"
            :disabled="!selectedRowKeys.length"
            :options="statusOptions"
          />
          <a-button :disabled="!bulkStatus || !selectedRowKeys.length || mutating" @click="applyBulkStatus">
            Apply
          </a-button>
          <a-button
            danger
            :disabled="!selectedRowKeys.length || mutating"
            :loading="mutating"
            @click="confirmBulkArchive"
          >
            Delete selected
          </a-button>
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="visibleDeals"
        :loading="loading"
        :pagination="{ pageSize: 10, showSizeChanger: true }"
        :row-key="(record: DealPipelineRow) => record.id"
        :row-selection="rowSelection"
        :scroll="{ x: 1400 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'creator'">
            <div class="creator-cell">
              <RouterLink
                :to="{
                  name: 'dealDetail',
                  params: { campaignId: record.campaign_id, dealId: record.id },
                }"
              >
                {{ record.influencer.display_name }}
              </RouterLink>
              <span v-if="record.primary_contact">{{ record.primary_contact.email }}</span>
              <span v-else class="muted">No contact</span>
              <a-tag v-if="record.archived_at" color="red">Deleted</a-tag>
            </div>
          </template>

          <template v-else-if="column.key === 'platforms'">
            <div v-if="record.platforms.length" class="tag-row">
              <a-tag
                v-for="platform in record.platforms"
                :key="`${platform.platform}:${platform.username}`"
                :color="platformColor(platform.platform)"
              >
                {{ platformDisplayName(platform) }}
              </a-tag>
            </div>
            <span v-else class="muted">No platforms</span>
          </template>

          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
          </template>

          <template v-else-if="column.key === 'deliverables'">
            <span>{{ record.deliverables.label ?? 'No deliverables' }}</span>
          </template>

          <template v-else-if="column.key === 'cost'">
            <span>{{ record.compensation.label ?? 'No cost items' }}</span>
          </template>

          <template v-else-if="column.key === 'updated'">
            <span>{{ formatDate(record.updated_at) }}</span>
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" @click="selectDeal(record)">Quick review</a-button>
              <RouterLink
                :to="{
                  name: 'dealDetail',
                  params: { campaignId: record.campaign_id, dealId: record.id },
                }"
              >
                <a-button type="link">Open deal</a-button>
              </RouterLink>
              <a-popconfirm
                v-if="!record.archived_at"
                title="Delete this deal?"
                ok-text="Delete"
                cancel-text="Cancel"
                @confirm="archiveOne(record)"
              >
                <a-button danger type="link">Delete</a-button>
              </a-popconfirm>
              <span v-else class="muted">Deleted</span>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="campaignEditOpen"
      title="Edit campaign"
      ok-text="Save"
      cancel-text="Cancel"
      :confirm-loading="mutating"
      destroy-on-close
      @ok="submitCampaignEdit"
    >
      <a-form ref="campaignFormRef" :model="campaignForm" layout="vertical">
        <a-form-item
          label="Name"
          name="name"
          :rules="[{ required: true, message: 'Campaign name is required.' }]"
        >
          <a-input v-model:value="campaignForm.name" />
        </a-form-item>

        <a-form-item label="Status" name="status">
          <a-select v-model:value="campaignForm.status" :options="campaignStatusOptions" />
        </a-form-item>

        <a-form-item label="Budget" name="budget">
          <a-input-number
            v-model:value="campaignForm.budget"
            :min="0"
            :precision="2"
            class="full-width"
          />
        </a-form-item>

        <div class="form-grid">
          <a-form-item label="Start date" name="startDate">
            <a-date-picker
              v-model:value="campaignForm.startDate"
              value-format="YYYY-MM-DD"
              class="full-width"
            />
          </a-form-item>
          <a-form-item label="End date" name="endDate">
            <a-date-picker
              v-model:value="campaignForm.endDate"
              value-format="YYYY-MM-DD"
              class="full-width"
            />
          </a-form-item>
        </div>

        <a-form-item label="Brief" name="brief">
          <a-textarea v-model:value="campaignForm.brief" :rows="3" />
        </a-form-item>

        <a-form-item label="Notes" name="notes">
          <a-textarea v-model:value="campaignForm.notes" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="addFromLibraryOpen"
      title="Add influencers from library"
      ok-text="Add to campaign"
      cancel-text="Cancel"
      width="920px"
      :confirm-loading="mutating"
      :ok-button-props="{ disabled: !selectedInfluencerRowKeys.length }"
      destroy-on-close
      @ok="submitAddFromLibrary"
    >
      <div class="modal-toolbar">
        <a-input-search
          v-model:value="influencerSearchText"
          class="search-input"
          allow-clear
          placeholder="Search influencers"
        />
        <a-select
          v-model:value="influencerPlatformFilter"
          class="platform-filter"
          allow-clear
          placeholder="All platforms"
          :options="libraryPlatformOptions"
        />
      </div>

      <a-table
        :columns="influencerColumns"
        :data-source="influencers"
        :loading="influencersLoading"
        :pagination="{ pageSize: 6 }"
        :row-key="(record: InfluencerListItem) => record.id"
        :row-selection="influencerRowSelection"
        :scroll="{ x: 760 }"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'influencer'">
            <div class="creator-cell">
              <RouterLink :to="{ name: 'influencerDetail', params: { influencerId: record.id } }">
                {{ record.display_name }}
              </RouterLink>
              <span v-if="record.full_name">{{ record.full_name }}</span>
            </div>
          </template>

          <template v-else-if="column.key === 'platforms'">
            <div v-if="record.platforms.length" class="tag-row">
              <a-tag
                v-for="platform in record.platforms"
                :key="platform.id"
                :color="platformColor(platform.platform)"
              >
                {{ libraryPlatformDisplayName(platform) }}
              </a-tag>
            </div>
            <span v-else class="muted">No platforms</span>
          </template>

          <template v-else-if="column.key === 'contact'">
            <span v-if="record.primary_contact">{{ record.primary_contact.email }}</span>
            <span v-else class="muted">No contact</span>
          </template>

          <template v-else-if="column.key === 'location'">
            <span>{{ formatLocation(record) }}</span>
          </template>
        </template>
      </a-table>
    </a-modal>

    <DealDetailDrawer
      :open="Boolean(selectedDeal)"
      :campaign-name="campaign?.name"
      :deal="selectedDeal"
      @close="selectDeal(null)"
    />
  </section>
</template>

<style scoped>
.workspace-page {
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

.page-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.campaign-status-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  color: #697582;
}

.page-alert {
  border-radius: 8px;
}

.campaign-overview {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr));
  gap: 12px;
}

.campaign-overview :deep(.ant-card-body) {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.campaign-overview span {
  color: #697582;
}

.campaign-overview strong {
  min-width: 0;
  overflow-wrap: anywhere;
  color: #20262d;
  font-size: 15px;
  line-height: 1.4;
}

.campaign-brief-card p {
  margin: 0;
  color: #3f4954;
  line-height: 1.6;
  white-space: pre-wrap;
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

.table-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 14px;
  border-bottom: 1px solid #edf0f5;
}

.table-title-row h2 {
  margin: 0;
  color: #20262d;
  font-size: 18px;
}

.table-title-row p {
  margin: 4px 0 0;
  color: #697582;
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
.table-toolbar-actions,
.modal-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.table-toolbar-controls {
  flex-wrap: wrap;
}

.table-toolbar-actions {
  flex-wrap: nowrap;
  justify-content: flex-end;
}

.modal-toolbar {
  margin-bottom: 12px;
}

.search-input {
  width: min(300px, 100%);
}

.status-filter,
.platform-filter,
.bulk-status {
  width: 160px;
}

.archive-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #4e5965;
  white-space: nowrap;
}

.creator-cell {
  display: grid;
  gap: 4px;
}

.creator-cell a {
  color: #175fcb;
  font-weight: 700;
}

.creator-cell span {
  color: #697582;
  font-size: 12px;
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

@media (max-width: 980px) {
  .page-heading,
  .table-title-row,
  .table-toolbar {
    display: grid;
  }

  .page-actions,
  .table-title-row {
    justify-content: flex-start;
  }

  .page-actions,
  .table-toolbar-actions {
    justify-content: flex-start;
  }

  .campaign-overview,
  .summary-grid {
    grid-template-columns: repeat(2, minmax(140px, 1fr));
  }
}

@media (max-width: 640px) {
  .campaign-overview,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .page-actions,
  .table-title-row,
  .table-toolbar-actions,
  .modal-toolbar {
    display: grid;
  }

  .page-actions a,
  .page-actions button,
  .table-title-row button,
  .table-toolbar-actions button,
  .search-input,
  .status-filter,
  .platform-filter,
  .bulk-status {
    width: 100%;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
