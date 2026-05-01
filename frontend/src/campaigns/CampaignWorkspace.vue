<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { message, Modal, type TableColumnsType } from 'ant-design-vue'
import type {
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

const route = useRoute()
const campaignId = computed(() => String(route.params.campaignId ?? ''))
const addFromLibraryOpen = ref(false)
const bulkStatus = ref<DealStatus | undefined>()

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
  hasEmailThreadFilter,
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
    title: 'Email',
    key: 'email',
    width: 120,
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
    width: 190,
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

const emailFilterOptions = [
  { label: 'Has email thread', value: true },
  { label: 'No email thread', value: false },
]

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

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)

const formatDate = (value: string) =>
  new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))

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
        <p class="page-description">
          Manage campaign deals, add influencers from the library, and export the current campaign view.
        </p>
      </div>
      <div class="page-actions">
        <a-button @click="openAddFromLibrary">Add from library</a-button>
        <RouterLink :to="{ name: 'email', query: { campaignId } }">
          <a-button>Open email</a-button>
        </RouterLink>
        <a-button type="primary" :loading="exporting" @click="downloadExport">Export view</a-button>
      </div>
    </div>

    <a-alert v-if="error" class="page-alert" type="error" :message="error" show-icon />

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
          <a-select
            v-model:value="hasEmailThreadFilter"
            class="email-filter"
            allow-clear
            placeholder="Email state"
            :options="emailFilterOptions"
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
        :scroll="{ x: 1340 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'creator'">
            <div class="creator-cell">
              <RouterLink :to="{ name: 'influencerDetail', params: { influencerId: record.influencer.id } }">
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

          <template v-else-if="column.key === 'email'">
            <span>{{ record.email_threads.thread_count }} threads</span>
          </template>

          <template v-else-if="column.key === 'updated'">
            <span>{{ formatDate(record.updated_at) }}</span>
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" @click="selectDeal(record)">Review</a-button>
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
.email-filter,
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

@media (max-width: 980px) {
  .page-heading,
  .table-toolbar {
    display: grid;
  }

  .page-actions,
  .table-toolbar-actions {
    justify-content: flex-start;
  }

  .summary-grid {
    grid-template-columns: repeat(2, minmax(140px, 1fr));
  }
}

@media (max-width: 640px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .page-actions,
  .table-toolbar-actions,
  .modal-toolbar {
    display: grid;
  }

  .page-actions a,
  .page-actions button,
  .table-toolbar-actions button,
  .search-input,
  .status-filter,
  .platform-filter,
  .email-filter,
  .bulk-status {
    width: 100%;
  }
}
</style>
