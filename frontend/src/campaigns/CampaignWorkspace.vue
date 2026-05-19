<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  message,
  Modal,
  type FormInstance,
  type TableColumnsType,
  type UploadProps,
} from 'ant-design-vue'
import { Download, Mail, Paperclip, Pencil, Plus, Trash2 } from '@lucide/vue'
import type {
  CampaignAttachmentResponse,
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
import EmptyState from '../shared/EmptyState.vue'
import { normalizeTags } from '../shared/tags'
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

interface TagsForm {
  tags: string[]
}

interface NotesForm {
  notes: string
}

const route = useRoute()
const router = useRouter()
const campaignId = computed(() => String(route.params.campaignId ?? ''))
const campaignFormRef = ref<FormInstance>()
const addFromLibraryOpen = ref(false)
const addFromLibraryMembershipLoading = ref(false)
const showOnlyAvailableInfluencers = ref(true)
const campaignEditOpen = ref(false)
const tagsModalOpen = ref(false)
const notesModalOpen = ref(false)
const bulkStatus = ref<DealStatus | undefined>()
const notesExpanded = ref(false)
const notesPreviewLimit = 180

const campaignForm = reactive<CampaignEditForm>({
  name: '',
  status: 'PLANNING',
  budget: null,
  startDate: null,
  endDate: null,
  brief: '',
  notes: '',
})

const tagsForm = reactive<TagsForm>({
  tags: [],
})

const notesForm = reactive<NotesForm>({
  notes: '',
})

const {
  campaign,
  attachments,
  campaignInfluencerDeals,
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
  loadCampaignInfluencerMembership,
  selectDeal,
  updateCampaignProfile,
  archiveCampaignProfile,
  uploadAttachment,
  deleteAttachment,
  attachmentDownloadUrl,
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
    width: 170,
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
    selectedInfluencerRowKeys.value = keys
      .map(String)
      .filter((key) => {
        const influencer = influencers.value.find((record) => record.id === key)
        return influencer ? isInfluencerSelectable(influencer) : false
      })
  },
  getCheckboxProps: (record: InfluencerListItem) => ({
    disabled: !isInfluencerSelectable(record),
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

const formatDateTime = (value: string) => {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

const formatBytes = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 'Unknown size'
  if (value < 1024) return `${value} B`
  const units = ['KB', 'MB', 'GB']
  let size = value / 1024
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unitIndex]}`
}

const attachmentTypeLabel = (attachment: CampaignAttachmentResponse) =>
  attachment.file.mime_type || 'Unknown type'

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

const isInfluencerAlreadyInCampaign = (influencerId: string) =>
  Boolean(campaignInfluencerDeals.value[influencerId])

const isInfluencerSelectable = (influencer: InfluencerListItem) =>
  !influencer.archived_at && !isInfluencerAlreadyInCampaign(influencer.id)

const addFromLibraryLoading = computed(
  () => influencersLoading.value || addFromLibraryMembershipLoading.value,
)

const filteredInfluencers = computed(() => {
  if (!showOnlyAvailableInfluencers.value) return influencers.value
  return influencers.value.filter((influencer) => !isInfluencerAlreadyInCampaign(influencer.id))
})

const hasDealFilters = computed(() =>
  Boolean(searchText.value.trim() || statusFilter.value || platformFilter.value || includeArchived.value),
)

const hasLibraryFilters = computed(() =>
  Boolean(
    influencerSearchText.value.trim() ||
      influencerPlatformFilter.value ||
      (showOnlyAvailableInfluencers.value && influencers.value.length > 0),
  ),
)

const statusColor = (status: DealStatus) => {
  if (status === 'ACTIVE') return 'green'
  if (status === 'COMPLETED') return 'blue'
  if (status === 'LOST') return 'red'
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

const campaignNotes = computed(() => campaign.value?.notes?.trim() ?? '')

const hasLongNotes = computed(() => campaignNotes.value.length > notesPreviewLimit)

const displayedNotes = computed(() => {
  if (!campaignNotes.value) return 'No notes yet.'
  if (!hasLongNotes.value || notesExpanded.value) return campaignNotes.value
  return `${campaignNotes.value.slice(0, notesPreviewLimit).trim()}...`
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

const resetTagsForm = () => {
  tagsForm.tags = [...(campaign.value?.tags ?? [])]
}

const resetNotesForm = () => {
  notesForm.notes = campaign.value?.notes ?? ''
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

const openTagsEdit = () => {
  resetTagsForm()
  tagsModalOpen.value = true
}

const openNotesEdit = () => {
  resetNotesForm()
  notesModalOpen.value = true
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

const submitTags = async () => {
  try {
    const tags = normalizeTags(tagsForm.tags)
    await updateCampaignProfile({ tags })
    message.success('Tags updated.')
    tagsModalOpen.value = false
  } catch (tagError) {
    message.error(tagError instanceof Error ? tagError.message : 'Tags could not be saved.')
  }
}

const submitNotes = async () => {
  try {
    await updateCampaignProfile({ notes: notesForm.notes.trim() || null })
    notesExpanded.value = false
    message.success('Notes updated.')
    notesModalOpen.value = false
  } catch {
    message.error('Notes could not be updated.')
  }
}

const beforeAttachmentUpload: UploadProps['beforeUpload'] = async (selectedFile) => {
  try {
    await uploadAttachment(selectedFile as File)
    message.success('Attachment uploaded.')
  } catch {
    message.error('Attachment could not be uploaded.')
  }
  return false
}

const removeAttachment = async (attachment: CampaignAttachmentResponse) => {
  try {
    await deleteAttachment(attachment.id)
    message.success('Attachment deleted.')
  } catch {
    message.error('Attachment could not be deleted.')
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
  showOnlyAvailableInfluencers.value = true
  addFromLibraryOpen.value = true
  addFromLibraryMembershipLoading.value = true

  try {
    await Promise.all([loadCampaignInfluencerMembership(), loadInfluencers()])
  } catch {
    addFromLibraryOpen.value = false
    message.error('Campaign membership could not be loaded.')
  } finally {
    addFromLibraryMembershipLoading.value = false
  }
}

const submitAddFromLibrary = async () => {
  selectedInfluencerRowKeys.value = selectedInfluencerRowKeys.value.filter(
    (influencerId) => !isInfluencerAlreadyInCampaign(influencerId),
  )
  if (!selectedInfluencerRowKeys.value.length) return

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
  notesExpanded.value = false
  selectDeal(null)
  void loadWorkspace()
})

watch([filteredInfluencers, campaignInfluencerDeals], () => {
  const selectableIds = new Set(
    filteredInfluencers.value
      .filter((influencer) => isInfluencerSelectable(influencer))
      .map((influencer) => influencer.id),
  )
  selectedInfluencerRowKeys.value = selectedInfluencerRowKeys.value.filter((key) =>
    selectableIds.has(key),
  )
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

    <a-alert v-if="error" class="page-alert" type="error" :message="error" show-icon />

    <section v-if="campaign" class="campaign-hero">
      <div class="hero-main">
        <div class="hero-title-row">
          <h1>{{ campaign.name }}</h1>
          <div class="campaign-status-row">
            <a-tag :color="campaignStatusColor(campaign.status)">
              {{ campaignStatusLabel(campaign.status) }}
            </a-tag>
            <a-tag v-if="campaign.archived_at" color="red">Deleted</a-tag>
          </div>
        </div>
        <p class="hero-brief">{{ campaign.brief || 'No brief yet.' }}</p>
        <div class="hero-meta">
          <strong>{{ brandLabel }}</strong>
          <span>{{ formatDateRange() }}</span>
          <span>Updated {{ formatDate(campaign.updated_at) }}</span>
        </div>
      </div>
      <div class="page-actions">
        <RouterLink :to="{ name: 'email', query: { campaignId } }">
          <a-button>
            <Mail class="button-leading-icon" aria-hidden="true" />
            Open email
          </a-button>
        </RouterLink>
        <a-button
          class="action-button-edit"
          :disabled="Boolean(campaign.archived_at)"
          @click="openCampaignEdit"
        >
          <Pencil class="button-leading-icon" aria-hidden="true" />
          Edit
        </a-button>
        <a-button
          danger
          :disabled="Boolean(campaign.archived_at)"
          :loading="mutating"
          @click="confirmCampaignDelete"
        >
          <Trash2 class="button-leading-icon" aria-hidden="true" />
          Delete
        </a-button>
      </div>
    </section>

    <div class="campaign-workspace-layout" :class="{ 'without-sidebar': !campaign }">
      <main class="campaign-main">
        <section class="metrics-strip" aria-label="Campaign metrics">
          <div class="metric-item">
            <span>Deals</span>
            <strong>{{ totalDealCount }}</strong>
          </div>
          <div class="metric-item">
            <span>In progress</span>
            <strong>{{ inProgressDealCount }}</strong>
          </div>
          <div class="metric-item">
            <span>Pending review</span>
            <strong>{{ pendingReviewCount }}</strong>
          </div>
          <div class="metric-item">
            <span>Planned spend</span>
            <strong>{{ formatCurrency(plannedSpend) }}</strong>
          </div>
        </section>

        <a-card class="table-card" :body-style="{ padding: '0' }">
      <div class="table-title-row">
        <div>
          <h2>Deals</h2>
          <p>Add influencers from the library to create campaign deals.</p>
        </div>
        <div class="table-title-actions">
          <a-button :loading="exporting" @click="downloadExport">
            <Download class="button-leading-icon" aria-hidden="true" />
            Export view
          </a-button>
          <a-button
            class="action-button-add"
            :disabled="!campaign || Boolean(campaign.archived_at)"
            @click="openAddFromLibrary"
          >
            <Plus class="button-leading-icon" aria-hidden="true" />
            Add influencers from library
          </a-button>
        </div>
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
            <Trash2 class="button-leading-icon" aria-hidden="true" />
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
        <template #emptyText>
          <EmptyState
            v-if="hasDealFilters"
            title="No deals match these filters"
            description="Clear search, status, platform, or deleted filters to broaden this campaign view."
          />
          <EmptyState
            v-else
            title="No deals yet"
            description="Add influencers from the library to create campaign-specific deal rows."
          >
            <template #actions>
              <a-button
                class="action-button-add"
                :disabled="!campaign || Boolean(campaign.archived_at)"
                @click="openAddFromLibrary"
              >
                <Plus class="button-leading-icon" aria-hidden="true" />
                Add influencers from library
              </a-button>
            </template>
          </EmptyState>
        </template>
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
              <a-popconfirm
                v-if="!record.archived_at"
                title="Delete this deal?"
                ok-text="Delete"
                cancel-text="Cancel"
                @confirm="archiveOne(record)"
              >
                <a-button
                  class="table-action-icon"
                  danger
                  type="text"
                  title="Delete deal"
                  aria-label="Delete deal"
                >
                  <Trash2 aria-hidden="true" />
                </a-button>
              </a-popconfirm>
              <span v-else class="muted">Deleted</span>
            </a-space>
          </template>
        </template>
      </a-table>
        </a-card>
      </main>

      <aside v-if="campaign" class="campaign-sidebar">
        <a-card class="side-card budget-card" size="small">
          <template #title>Budget</template>
          <strong>{{ formatCurrency(campaign.budget) }}</strong>
        </a-card>

        <a-card class="side-card" size="small">
          <template #title>Tags</template>
          <template #extra>
            <a-tooltip title="Edit tags">
              <a-button
                type="text"
                class="side-card-icon-button"
                :disabled="Boolean(campaign.archived_at)"
                aria-label="Edit tags"
                @click="openTagsEdit"
              >
                <Pencil aria-hidden="true" />
              </a-button>
            </a-tooltip>
          </template>
          <div v-if="campaign.tags.length" class="tag-row">
            <a-tag v-for="tag in campaign.tags" :key="tag">{{ tag }}</a-tag>
          </div>
          <span v-else class="muted">No tags</span>
        </a-card>

        <a-card class="side-card" size="small">
          <template #title>Notes</template>
          <template #extra>
            <a-tooltip title="Edit notes">
              <a-button
                type="text"
                class="side-card-icon-button"
                :disabled="Boolean(campaign.archived_at)"
                aria-label="Edit notes"
                @click="openNotesEdit"
              >
                <Pencil aria-hidden="true" />
              </a-button>
            </a-tooltip>
          </template>
          <p class="notes-preview">{{ displayedNotes }}</p>
          <a-button
            v-if="hasLongNotes"
            type="link"
            class="notes-toggle"
            @click="notesExpanded = !notesExpanded"
          >
            {{ notesExpanded ? 'Show less' : 'Show more' }}
          </a-button>
        </a-card>

        <a-card class="side-card attachments-card" size="small">
          <template #title>Attachments</template>
          <template #extra>
            <a-upload
              name="file"
              class="attachment-upload-trigger"
              :before-upload="beforeAttachmentUpload"
              :show-upload-list="false"
              :disabled="Boolean(campaign.archived_at) || mutating"
            >
              <a-tooltip title="Attach file">
                <a-button
                  type="text"
                  class="side-card-icon-button"
                  :loading="mutating"
                  :disabled="Boolean(campaign.archived_at)"
                  aria-label="Attach file"
                >
                  <Plus aria-hidden="true" />
                </a-button>
              </a-tooltip>
            </a-upload>
          </template>
          <div v-if="!attachments.length" class="attachments-placeholder">
            <Paperclip class="attachments-icon" aria-hidden="true" />
            <div>
              <strong>No attachments yet</strong>
              <span>Attach briefs, references, campaign docs, or other working files.</span>
            </div>
          </div>
          <div v-else class="attachment-list">
            <div
              v-for="attachment in attachments"
              :key="attachment.id"
              class="attachment-row"
            >
              <Paperclip class="attachment-row-icon" aria-hidden="true" />
              <div class="attachment-details">
                <strong>{{ attachment.file.original_name }}</strong>
                <span>
                  {{ formatBytes(attachment.file.size_bytes) }} ·
                  {{ attachmentTypeLabel(attachment) }}
                </span>
                <span>
                  Uploaded {{ formatDateTime(attachment.created_at) }}
                  <template v-if="!attachment.file.exists"> · Missing locally</template>
                </span>
              </div>
              <div class="attachment-actions">
                <a
                  v-if="attachment.file.exists"
                  :href="attachmentDownloadUrl(attachment.file.id)"
                  target="_blank"
                  rel="noreferrer"
                >
                  <a-button
                    class="table-action-icon"
                    type="text"
                    title="Download attachment"
                    aria-label="Download attachment"
                  >
                    <Download aria-hidden="true" />
                  </a-button>
                </a>
                <a-button
                  v-else
                  class="table-action-icon"
                  type="text"
                  disabled
                  title="File missing locally"
                  aria-label="File missing locally"
                >
                  <Download aria-hidden="true" />
                </a-button>
                <a-popconfirm
                  title="Delete this attachment?"
                  ok-text="Delete"
                  cancel-text="Cancel"
                  @confirm="removeAttachment(attachment)"
                >
                  <a-button
                    class="table-action-icon"
                    danger
                    type="text"
                    title="Delete attachment"
                    aria-label="Delete attachment"
                    :disabled="Boolean(campaign.archived_at)"
                  >
                    <Trash2 aria-hidden="true" />
                  </a-button>
                </a-popconfirm>
              </div>
            </div>
          </div>
        </a-card>
      </aside>
    </div>

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
      v-model:open="tagsModalOpen"
      title="Edit tags"
      ok-text="Save"
      cancel-text="Cancel"
      :confirm-loading="mutating"
      destroy-on-close
      @ok="submitTags"
    >
      <a-form :model="tagsForm" layout="vertical">
        <a-form-item label="Tags" name="tags">
          <a-select
            v-model:value="tagsForm.tags"
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

    <a-modal
      v-model:open="notesModalOpen"
      title="Edit notes"
      ok-text="Save"
      cancel-text="Cancel"
      :confirm-loading="mutating"
      destroy-on-close
      @ok="submitNotes"
    >
      <a-form :model="notesForm" layout="vertical">
        <a-form-item label="Notes" name="notes">
          <a-textarea v-model:value="notesForm.notes" :rows="5" />
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
      :ok-button-props="{ disabled: addFromLibraryLoading || !selectedInfluencerRowKeys.length }"
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
        <label class="archive-toggle">
          <span>Only not added</span>
          <a-switch v-model:checked="showOnlyAvailableInfluencers" />
        </label>
      </div>

      <a-table
        :columns="influencerColumns"
        :data-source="filteredInfluencers"
        :loading="addFromLibraryLoading"
        :pagination="{ pageSize: 6 }"
        :row-key="(record: InfluencerListItem) => record.id"
        :row-selection="influencerRowSelection"
        :scroll="{ x: 760 }"
        size="small"
      >
        <template #emptyText>
          <EmptyState
            v-if="hasLibraryFilters"
            title="No available influencers match"
            description="Clear the modal search, platform filter, or Only not added toggle to see more library profiles."
          />
          <EmptyState
            v-else
            title="No influencers in the library"
            description="Create or import influencers before adding them to a campaign."
          />
        </template>
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'influencer'">
            <div class="creator-cell">
              <RouterLink :to="{ name: 'influencerDetail', params: { influencerId: record.id } }">
                {{ record.display_name }}
              </RouterLink>
              <span v-if="record.full_name">{{ record.full_name }}</span>
              <a-tag v-if="isInfluencerAlreadyInCampaign(record.id)" color="default">
                Already in campaign
              </a-tag>
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

h1 {
  margin: 0;
  color: #20262d;
  font-size: 30px;
  font-weight: 600;
  line-height: 1.15;
}

.button-leading-icon {
  width: 16px;
  height: 16px;
  margin-right: 6px;
  vertical-align: -3px;
}

.table-action-icon {
  width: 30px;
  height: 30px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.table-action-icon :deep(svg) {
  width: 16px;
  height: 16px;
}

.side-card-icon-button {
  width: 28px;
  height: 28px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.side-card-icon-button :deep(svg) {
  width: 15px;
  height: 15px;
}

.page-actions {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  flex-shrink: 0;
}

.campaign-status-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  color: #697582;
}

.page-alert {
  border-radius: 8px;
}

.campaign-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 22px 24px;
  border: 1px solid #dde6ef;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgb(25 45 70 / 6%);
}

.hero-main {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.hero-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-brief {
  max-width: 820px;
  margin: 0;
  color: #2f3a45;
  font-size: 16px;
  line-height: 1.55;
  white-space: pre-wrap;
}

.hero-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  color: #697582;
}

.hero-meta strong {
  color: #34424f;
  font-weight: 500;
}

.hero-meta span::before {
  content: "·";
  margin-right: 8px;
  color: #9aa6b2;
}

.campaign-workspace-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  align-items: start;
  gap: 18px;
}

.campaign-workspace-layout.without-sidebar {
  grid-template-columns: minmax(0, 1fr);
}

.campaign-main,
.campaign-sidebar {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.muted {
  color: #697582;
}

.metrics-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(120px, 1fr));
  gap: 1px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #e2e8f0;
}

.metric-item {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 12px 14px;
  background: #ffffff;
}

.metric-item span {
  color: #697582;
  font-size: 12px;
  font-weight: 500;
}

.metric-item strong {
  min-width: 0;
  overflow-wrap: anywhere;
  color: #20262d;
  font-size: 21px;
  font-weight: 500;
  line-height: 1.2;
}

.side-card {
  min-width: 0;
}

.side-card :deep(.ant-card-head) {
  min-height: 42px;
}

.side-card :deep(.ant-card-head-title) {
  font-size: 13px;
  font-weight: 550;
}

.side-card :deep(.ant-card-body) {
  min-width: 0;
}

.budget-card strong {
  color: #20262d;
  font-size: 24px;
  font-weight: 500;
  line-height: 1.2;
}

.notes-preview {
  margin: 0;
  color: #3f4954;
  line-height: 1.55;
  white-space: pre-wrap;
}

.notes-toggle {
  height: auto;
  margin-top: 6px;
  padding: 0;
}

.attachments-card :deep(.ant-card-body) {
  display: grid;
  gap: 12px;
}

.attachments-placeholder {
  display: flex;
  gap: 10px;
  color: #697582;
}

.attachments-placeholder div {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.attachments-placeholder strong {
  color: #34424f;
  font-size: 13px;
  font-weight: 500;
}

.attachments-placeholder span {
  font-size: 12px;
  line-height: 1.4;
}

.attachments-icon {
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  margin-top: 1px;
}

.attachment-list {
  display: grid;
  gap: 10px;
}

.attachment-row {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: start;
  min-width: 0;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
}

.attachment-row-icon {
  width: 18px;
  height: 18px;
  margin-top: 2px;
  color: #697582;
}

.attachment-details {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.attachment-details strong {
  min-width: 0;
  overflow-wrap: anywhere;
  color: #34424f;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
}

.attachment-details span {
  min-width: 0;
  overflow-wrap: anywhere;
  color: #697582;
  font-size: 12px;
  line-height: 1.35;
}

.attachment-actions {
  display: flex;
  align-items: center;
  gap: 2px;
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
  font-weight: 600;
}

.table-title-row p {
  margin: 4px 0 0;
  color: #697582;
}

.table-title-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
  flex-shrink: 0;
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
  font-weight: 600;
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

.form-help {
  margin: 6px 0 0;
  color: #697582;
  font-size: 12px;
  line-height: 1.4;
}

@media (max-width: 980px) {
  .campaign-hero,
  .campaign-workspace-layout,
  .table-title-row,
  .table-toolbar {
    display: grid;
    grid-template-columns: 1fr;
  }

  .page-actions,
  .table-title-row {
    justify-content: flex-start;
  }

  .page-actions,
  .table-toolbar-actions {
    justify-content: flex-start;
  }

  .metrics-strip {
    grid-template-columns: repeat(2, minmax(140px, 1fr));
  }

  .hero-meta span::before {
    content: none;
    margin-right: 0;
  }
}

@media (max-width: 640px) {
  .campaign-hero {
    padding: 18px;
  }

  .metrics-strip {
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
