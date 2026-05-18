<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { message, Modal, type FormInstance, type TableColumnsType } from 'ant-design-vue'
import { Mail, Paperclip, Pencil, Plus, Trash2, User } from '@lucide/vue'
import type {
  CompensationItemResponse,
  CompensationItemStatus,
  CompensationItemType,
  DealStatus,
  DeliverableResponse,
  DeliverableStatus,
  PrimaryPlatformSummary,
} from '../api/types'
import { dealStatuses, dealStatusLabels } from '../campaigns/useCampaignWorkspace'
import { platformColor } from '../influencers/useInfluencers'
import EmptyState from '../shared/EmptyState.vue'
import { normalizeTags } from '../shared/tags'
import { useDealDetail } from './useDealDetail'

interface DealEditForm {
  status: DealStatus
  lostReason: string
  internalNotes: string
}

interface TagsForm {
  tags: string[]
}

interface DeliverableForm {
  type: string
  quantity: number
  dueDate: string | null
  status: DeliverableStatus
  publishedUrl: string
  notes: string
}

interface CompensationForm {
  type: CompensationItemType
  description: string
  amount: number | null
  currency: string
  recipientName: string
  status: CompensationItemStatus
  dueDate: string | null
  notes: string
}

const route = useRoute()
const router = useRouter()
const campaignId = computed(() => String(route.params.campaignId ?? ''))
const dealId = computed(() => String(route.params.dealId ?? ''))

const dealFormRef = ref<FormInstance>()
const deliverableFormRef = ref<FormInstance>()
const compensationFormRef = ref<FormInstance>()

const editDealOpen = ref(false)
const tagsModalOpen = ref(false)
const deliverableModalOpen = ref(false)
const compensationModalOpen = ref(false)
const editingDeliverable = ref<DeliverableResponse | null>(null)
const editingCompensationItem = ref<CompensationItemResponse | null>(null)

const {
  campaign,
  deal,
  deliverables,
  compensationItems,
  loading,
  mutating,
  error,
  campaignName,
  influencerName,
  loadDealDetail,
  updateDealDetail,
  createDeliverable,
  updateDeliverable,
  deleteDeliverable,
  createCompensationItem,
  updateCompensationItem,
  deleteCompensationItem,
  archiveProfile,
} = useDealDetail(() => dealId.value, () => campaignId.value)

const dealForm = reactive<DealEditForm>({
  status: 'DRAFT',
  lostReason: '',
  internalNotes: '',
})

const tagsForm = reactive<TagsForm>({
  tags: [],
})

const deliverableForm = reactive<DeliverableForm>({
  type: '',
  quantity: 1,
  dueDate: null,
  status: 'TODO',
  publishedUrl: '',
  notes: '',
})

const compensationForm = reactive<CompensationForm>({
  type: 'CASH_STIPEND',
  description: '',
  amount: null,
  currency: 'USD',
  recipientName: '',
  status: 'PLANNED',
  dueDate: null,
  notes: '',
})

const deliverableColumns: TableColumnsType<DeliverableResponse> = [
  {
    title: 'Item',
    key: 'item',
    width: 180,
  },
  {
    title: 'Status',
    key: 'status',
    width: 140,
  },
  {
    title: 'Due',
    key: 'due',
    dataIndex: 'due_date',
    width: 130,
  },
  {
    title: 'Link',
    key: 'link',
    width: 180,
  },
  {
    title: 'Actions',
    key: 'actions',
    fixed: 'right',
    width: 150,
  },
]

const compensationColumns: TableColumnsType<CompensationItemResponse> = [
  {
    title: 'Type',
    key: 'type',
    width: 220,
  },
  {
    title: 'Amount',
    key: 'amount',
    width: 130,
  },
  {
    title: 'Status',
    key: 'status',
    width: 140,
  },
  {
    title: 'Due',
    key: 'due',
    dataIndex: 'due_date',
    width: 130,
  },
  {
    title: 'Actions',
    key: 'actions',
    fixed: 'right',
    width: 150,
  },
]

const statusOptions = computed(() =>
  dealStatuses.map((status) => ({
    label: dealStatusLabels[status],
    value: status,
  })),
)

const deliverableStatusOptions = [
  { label: 'Todo', value: 'TODO' },
  { label: 'In progress', value: 'IN_PROGRESS' },
  { label: 'Submitted', value: 'SUBMITTED' },
  { label: 'Posted', value: 'POSTED' },
  { label: 'Completed', value: 'COMPLETED' },
  { label: 'Cancelled', value: 'CANCELLED' },
]

const compensationTypeOptions = [
  { label: 'Cash stipend', value: 'CASH_STIPEND' },
  { label: 'Product gift', value: 'PRODUCT_GIFT' },
  { label: 'Sample product', value: 'SAMPLE_PRODUCT' },
  { label: 'Flight reimbursement', value: 'FLIGHT_REIMBURSEMENT' },
  { label: 'Hotel reimbursement', value: 'HOTEL_REIMBURSEMENT' },
  { label: 'Local transport reimbursement', value: 'LOCAL_TRANSPORT_REIMBURSEMENT' },
  { label: 'Meal or per diem', value: 'MEAL_OR_PER_DIEM' },
  { label: 'Other', value: 'OTHER' },
]

const compensationStatusOptions = [
  { label: 'Planned', value: 'PLANNED' },
  { label: 'Promised', value: 'PROMISED' },
  { label: 'In progress', value: 'IN_PROGRESS' },
  { label: 'Completed', value: 'COMPLETED' },
  { label: 'Cancelled', value: 'CANCELLED' },
]

const statusLabel = (status: DealStatus) => dealStatusLabels[status]

const statusColor = (status: DealStatus) => {
  if (status === 'ACTIVE') return 'green'
  if (status === 'COMPLETED') return 'blue'
  if (status === 'LOST') return 'red'
  return 'default'
}

const formatDate = (value: string | null | undefined) => {
  if (!value) return 'Not set'
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))
}

const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return null
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(
    value,
  )
}

const platformLabel = (platform: PrimaryPlatformSummary) => {
  const username = platform.username ? ` @${platform.username}` : ''
  const followers = formatNumber(platform.follower_count)
  return `${platform.platform}${username}${followers ? ` · ${followers}` : ''}`
}

const deliverableStatusLabel = (status: DeliverableStatus) =>
  deliverableStatusOptions.find((option) => option.value === status)?.label ?? status

const compensationTypeLabel = (type: CompensationItemType) =>
  compensationTypeOptions.find((option) => option.value === type)?.label ?? type

const compensationStatusLabel = (status: CompensationItemStatus) =>
  compensationStatusOptions.find((option) => option.value === status)?.label ?? status

const formatMoney = (amount: string | number | null | undefined, currency: string | null | undefined) => {
  if (amount === null || amount === undefined || amount === '') return 'Non-cash'
  const numericAmount = typeof amount === 'number' ? amount : Number(amount)
  if (!Number.isFinite(numericAmount)) return String(amount)
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD',
    maximumFractionDigits: 2,
  }).format(numericAmount)
}

const locationLabel = computed(() => {
  if (!deal.value) return 'Not set'
  return [deal.value.influencer.city, deal.value.influencer.country].filter(Boolean).join(', ') || 'Not set'
})

const nextActionLabel = computed(() => {
  if (!deal.value) return 'Load deal'
  if (deal.value.status === 'LOST') return deal.value.lost_reason ?? 'Review lost reason'
  if (deal.value.completion_suggested) return 'Review completion'
  if (deal.value.deliverables.next_due_date) {
    return `Next deliverable due ${formatDate(deal.value.deliverables.next_due_date)}`
  }
  if (!deal.value.primary_contact) return 'Add contact'
  return 'Review deal'
})

const deliverableSummary = computed(() => deal.value?.deliverables.label ?? 'No deliverables')

const compensationSummary = computed(() => deal.value?.compensation.label ?? 'No cost items')

const nextDueLabel = computed(() => {
  const dueDate = deal.value?.deliverables.next_due_date
  return dueDate ? formatDate(dueDate) : 'Not set'
})

const lostReasonInputEnabled = computed(
  () => deal.value?.status === 'LOST' || dealForm.status === 'LOST',
)

const resetDealForm = () => {
  dealForm.status = deal.value?.status ?? 'DRAFT'
  dealForm.lostReason = deal.value?.lost_reason ?? ''
  dealForm.internalNotes = deal.value?.internal_notes ?? ''
  dealFormRef.value?.clearValidate()
}

const resetTagsForm = () => {
  tagsForm.tags = [...(deal.value?.labels ?? [])]
}

const resetDeliverableForm = () => {
  deliverableForm.type = ''
  deliverableForm.quantity = 1
  deliverableForm.dueDate = null
  deliverableForm.status = 'TODO'
  deliverableForm.publishedUrl = ''
  deliverableForm.notes = ''
  deliverableFormRef.value?.clearValidate()
}

const resetCompensationForm = () => {
  compensationForm.type = 'CASH_STIPEND'
  compensationForm.description = ''
  compensationForm.amount = null
  compensationForm.currency = 'USD'
  compensationForm.recipientName = ''
  compensationForm.status = 'PLANNED'
  compensationForm.dueDate = null
  compensationForm.notes = ''
  compensationFormRef.value?.clearValidate()
}

const openDealEdit = () => {
  resetDealForm()
  editDealOpen.value = true
}

const openTagsEdit = () => {
  resetTagsForm()
  tagsModalOpen.value = true
}

const openCreateDeliverable = () => {
  editingDeliverable.value = null
  resetDeliverableForm()
  deliverableModalOpen.value = true
}

const openEditDeliverable = (deliverable: DeliverableResponse) => {
  editingDeliverable.value = deliverable
  deliverableForm.type = deliverable.type
  deliverableForm.quantity = deliverable.quantity
  deliverableForm.dueDate = deliverable.due_date ?? null
  deliverableForm.status = deliverable.status
  deliverableForm.publishedUrl = deliverable.published_url ?? ''
  deliverableForm.notes = deliverable.notes ?? ''
  deliverableModalOpen.value = true
}

const openCreateCompensation = () => {
  editingCompensationItem.value = null
  resetCompensationForm()
  compensationModalOpen.value = true
}

const openEditCompensation = (item: CompensationItemResponse) => {
  editingCompensationItem.value = item
  compensationForm.type = item.type
  compensationForm.description = item.description ?? ''
  compensationForm.amount = item.amount === null || item.amount === undefined ? null : Number(item.amount)
  compensationForm.currency = item.currency ?? 'USD'
  compensationForm.recipientName = item.recipient_name ?? ''
  compensationForm.status = item.status
  compensationForm.dueDate = item.due_date ?? null
  compensationForm.notes = item.notes ?? ''
  compensationModalOpen.value = true
}

const submitDealEdit = async () => {
  await dealFormRef.value?.validate()

  try {
    await updateDealDetail({
      status: dealForm.status,
      lost_reason: lostReasonInputEnabled.value ? dealForm.lostReason.trim() || null : null,
      internal_notes: dealForm.internalNotes.trim() || null,
    })
    message.success('Deal updated.')
    editDealOpen.value = false
  } catch {
    message.error('Deal could not be updated.')
  }
}

const submitTags = async () => {
  try {
    const tags = normalizeTags(tagsForm.tags)
    await updateDealDetail({ labels: tags })
    message.success('Tags updated.')
    tagsModalOpen.value = false
  } catch (tagError) {
    message.error(tagError instanceof Error ? tagError.message : 'Tags could not be saved.')
  }
}

const submitDeliverable = async () => {
  await deliverableFormRef.value?.validate()

  const payload = {
    type: deliverableForm.type.trim(),
    quantity: deliverableForm.quantity,
    due_date: deliverableForm.dueDate,
    status: deliverableForm.status,
    published_url: deliverableForm.publishedUrl.trim() || null,
    notes: deliverableForm.notes.trim() || null,
  }

  try {
    if (editingDeliverable.value) {
      await updateDeliverable(editingDeliverable.value.id, payload)
      message.success('Deliverable updated.')
    } else {
      await createDeliverable(payload)
      message.success('Deliverable added.')
    }
    deliverableModalOpen.value = false
  } catch {
    message.error('Deliverable could not be saved.')
  }
}

const submitCompensation = async () => {
  await compensationFormRef.value?.validate()

  const payload = {
    type: compensationForm.type,
    description: compensationForm.description.trim() || null,
    amount: compensationForm.amount,
    currency: compensationForm.currency.trim().toUpperCase() || null,
    recipient_name: compensationForm.recipientName.trim() || null,
    status: compensationForm.status,
    due_date: compensationForm.dueDate,
    notes: compensationForm.notes.trim() || null,
  }

  try {
    if (editingCompensationItem.value) {
      await updateCompensationItem(editingCompensationItem.value.id, payload)
      message.success('Compensation item updated.')
    } else {
      await createCompensationItem(payload)
      message.success('Compensation item added.')
    }
    compensationModalOpen.value = false
  } catch {
    message.error('Compensation item could not be saved.')
  }
}

const removeDeliverable = async (deliverable: DeliverableResponse) => {
  try {
    await deleteDeliverable(deliverable.id)
    message.success('Deliverable deleted.')
  } catch {
    message.error('Deliverable could not be deleted.')
  }
}

const removeCompensationItem = async (item: CompensationItemResponse) => {
  try {
    await deleteCompensationItem(item.id)
    message.success('Compensation item deleted.')
  } catch {
    message.error('Compensation item could not be deleted.')
  }
}

const confirmArchive = () => {
  if (!deal.value) return

  Modal.confirm({
    title: 'Delete this deal?',
    content: 'Deleted deals are hidden from campaign workspaces but remain available in history.',
    okText: 'Delete',
    okType: 'danger',
    cancelText: 'Cancel',
    async onOk() {
      try {
        await archiveProfile()
        message.success(`${influencerName.value} deal deleted.`)
        await router.push({ name: 'campaignWorkspace', params: { campaignId: campaignId.value } })
      } catch {
        message.error('Deal could not be deleted.')
      }
    },
  })
}

watch([campaignId, dealId], () => {
  void loadDealDetail()
})

void loadDealDetail()
</script>

<template>
  <section class="deal-detail-page">
    <a-breadcrumb>
      <a-breadcrumb-item>
        <RouterLink :to="{ name: 'campaigns' }">Campaigns</RouterLink>
      </a-breadcrumb-item>
      <a-breadcrumb-item>
        <RouterLink :to="{ name: 'campaignWorkspace', params: { campaignId } }">
          {{ campaignName }}
        </RouterLink>
      </a-breadcrumb-item>
      <a-breadcrumb-item>{{ influencerName }} deal</a-breadcrumb-item>
    </a-breadcrumb>

    <a-alert v-if="error" class="page-alert" type="error" :message="error" show-icon />

    <a-spin :spinning="loading">
      <template v-if="deal">
        <section class="deal-hero">
          <div class="hero-main">
            <div class="hero-title-row">
              <h1>{{ deal.influencer.display_name }} deal</h1>
              <div class="heading-meta">
                <a-tag :color="statusColor(deal.status)">{{ statusLabel(deal.status) }}</a-tag>
                <a-tag v-if="deal.archived_at" color="red">Deleted</a-tag>
              </div>
            </div>
            <p class="hero-brief">{{ nextActionLabel }}</p>
            <div class="hero-meta">
              <strong>{{ campaignName }}</strong>
              <span>{{ deal.primary_contact?.email ?? 'No contact' }}</span>
              <span>Updated {{ formatDate(deal.updated_at) }}</span>
            </div>
          </div>
          <div class="page-actions">
            <a-button class="action-button-edit" @click="openDealEdit">
              <Pencil class="button-leading-icon" aria-hidden="true" />
              Edit deal
            </a-button>
            <RouterLink :to="{ name: 'email', query: { campaignId, dealId } }">
              <a-button>
                <Mail class="button-leading-icon" aria-hidden="true" />
                Open email
              </a-button>
            </RouterLink>
            <a-button
              danger
              :disabled="Boolean(deal.archived_at)"
              :loading="mutating"
              @click="confirmArchive"
            >
              <Trash2 class="button-leading-icon" aria-hidden="true" />
              Delete
            </a-button>
          </div>
        </section>

        <div class="deal-workspace-layout">
          <main class="deal-main">
            <section class="metrics-strip" aria-label="Deal metrics">
              <div class="metric-item">
                <span>Deliverables</span>
                <strong>{{ deliverableSummary }}</strong>
              </div>
              <div class="metric-item">
                <span>Compensation</span>
                <strong>{{ compensationSummary }}</strong>
              </div>
              <div class="metric-item">
                <span>Next due</span>
                <strong>{{ nextDueLabel }}</strong>
              </div>
              <div class="metric-item">
                <span>Completion</span>
                <strong>{{ deal.completion_suggested ? 'Review' : 'Open' }}</strong>
              </div>
            </section>

        <div class="work-grid">
          <a-card class="section-card">
            <template #title>Deliverables</template>
            <template #extra>
              <a-button class="action-button-add" @click="openCreateDeliverable">
                <Plus class="button-leading-icon" aria-hidden="true" />
                Add item
              </a-button>
            </template>
            <a-table
              :columns="deliverableColumns"
              :data-source="deliverables"
              :pagination="false"
              :row-key="(record: DeliverableResponse) => record.id"
              :scroll="{ x: 820 }"
              size="small"
            >
              <template #emptyText>
                <EmptyState
                  title="No deliverables yet"
                  description="Add deliverables to track what this creator owes for the campaign."
                >
                  <template #actions>
                    <a-button class="action-button-add" @click="openCreateDeliverable">
                      <Plus class="button-leading-icon" aria-hidden="true" />
                      Add item
                    </a-button>
                  </template>
                </EmptyState>
              </template>
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'item'">
                  <strong>{{ record.quantity }} {{ record.type }}</strong>
                  <p v-if="record.notes" class="cell-note">{{ record.notes }}</p>
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-tag>{{ deliverableStatusLabel(record.status) }}</a-tag>
                </template>
                <template v-else-if="column.key === 'due'">
                  {{ formatDate(record.due_date) }}
                </template>
                <template v-else-if="column.key === 'link'">
                  <a v-if="record.published_url" :href="record.published_url" target="_blank" rel="noreferrer">
                    Published
                  </a>
                  <span v-else class="muted">Not posted</span>
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button
                      class="table-action-icon"
                      type="text"
                      title="Edit deliverable"
                      aria-label="Edit deliverable"
                      @click="openEditDeliverable(record)"
                    >
                      <Pencil aria-hidden="true" />
                    </a-button>
                    <a-popconfirm
                      title="Delete this deliverable?"
                      ok-text="Delete"
                      cancel-text="Cancel"
                      @confirm="removeDeliverable(record)"
                    >
                      <a-button
                        class="table-action-icon"
                        danger
                        type="text"
                        title="Delete deliverable"
                        aria-label="Delete deliverable"
                      >
                        <Trash2 aria-hidden="true" />
                      </a-button>
                    </a-popconfirm>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-card>

          <a-card class="section-card">
            <template #title>Compensation</template>
            <template #extra>
              <a-button class="action-button-add" @click="openCreateCompensation">
                <Plus class="button-leading-icon" aria-hidden="true" />
                Add item
              </a-button>
            </template>
            <a-table
              :columns="compensationColumns"
              :data-source="compensationItems"
              :pagination="false"
              :row-key="(record: CompensationItemResponse) => record.id"
              :scroll="{ x: 820 }"
              size="small"
            >
              <template #emptyText>
                <EmptyState
                  title="No compensation items yet"
                  description="Add cash, gifts, samples, reimbursements, or other costs for this deal."
                >
                  <template #actions>
                    <a-button class="action-button-add" @click="openCreateCompensation">
                      <Plus class="button-leading-icon" aria-hidden="true" />
                      Add item
                    </a-button>
                  </template>
                </EmptyState>
              </template>
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'type'">
                  <strong>{{ compensationTypeLabel(record.type) }}</strong>
                  <p v-if="record.description" class="cell-note">{{ record.description }}</p>
                </template>
                <template v-else-if="column.key === 'amount'">
                  {{ formatMoney(record.amount, record.currency) }}
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-tag>{{ compensationStatusLabel(record.status) }}</a-tag>
                </template>
                <template v-else-if="column.key === 'due'">
                  {{ formatDate(record.due_date) }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button
                      class="table-action-icon"
                      type="text"
                      title="Edit compensation item"
                      aria-label="Edit compensation item"
                      @click="openEditCompensation(record)"
                    >
                      <Pencil aria-hidden="true" />
                    </a-button>
                    <a-popconfirm
                      title="Delete this compensation item?"
                      ok-text="Delete"
                      cancel-text="Cancel"
                      @confirm="removeCompensationItem(record)"
                    >
                      <a-button
                        class="table-action-icon"
                        danger
                        type="text"
                        title="Delete compensation item"
                        aria-label="Delete compensation item"
                      >
                        <Trash2 aria-hidden="true" />
                      </a-button>
                    </a-popconfirm>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-card>
        </div>
          </main>

          <aside class="deal-sidebar">
            <a-card class="side-card influencer-card">
              <template #title>Influencer</template>
              <template #extra>
                <RouterLink :to="{ name: 'influencerDetail', params: { influencerId: deal.influencer.id } }">
                  <a-button>
                    <User class="button-leading-icon" aria-hidden="true" />
                    Open
                  </a-button>
                </RouterLink>
              </template>
              <h2>{{ deal.influencer.display_name }}</h2>
              <p>{{ locationLabel }}</p>
              <div v-if="deal.platforms.length" class="tag-row">
                <a-tag
                  v-for="platform in deal.platforms"
                  :key="`${platform.platform}:${platform.username}`"
                  :color="platformColor(platform.platform)"
                >
                  {{ platformLabel(platform) }}
                </a-tag>
              </div>
              <span v-else class="muted">No platforms</span>
            </a-card>

            <a-card class="side-card">
              <template #title>Deal Summary</template>
              <div class="property-list">
                <div v-if="deal.status === 'LOST'">
                  <span>Lost reason</span>
                  <strong>{{ deal.lost_reason || 'Reason not recorded' }}</strong>
                </div>
                <div>
                  <span>Campaign</span>
                  <strong>{{ campaignName }}</strong>
                </div>
                <div>
                  <span>Created</span>
                  <strong>{{ formatDate(deal.created_at) }}</strong>
                </div>
                <div>
                  <span>Updated</span>
                  <strong>{{ formatDate(deal.updated_at) }}</strong>
                </div>
              </div>
            </a-card>

            <a-card class="side-card">
              <template #title>Tags</template>
              <template #extra>
                <a-button class="action-button-edit" @click="openTagsEdit">
                  <Pencil class="button-leading-icon" aria-hidden="true" />
                  Edit
                </a-button>
              </template>
              <div v-if="deal.labels.length" class="tag-row">
                <a-tag v-for="tag in deal.labels" :key="tag">{{ tag }}</a-tag>
              </div>
              <span v-else class="muted">No tags yet.</span>
            </a-card>

            <a-card class="side-card">
              <template #title>Notes</template>
              <template #extra>
                <a-button class="action-button-edit" @click="openDealEdit">
                  <Pencil class="button-leading-icon" aria-hidden="true" />
                  Edit
                </a-button>
              </template>
              <p class="notes">{{ deal.internal_notes || 'No internal notes yet.' }}</p>
            </a-card>

            <a-card class="side-card attachments-card">
              <template #title>Attachments</template>
              <div class="attachments-placeholder">
                <Paperclip class="attachments-icon" aria-hidden="true" />
                <div>
                  <strong>No attachments yet</strong>
                  <span>Deal-scoped attachments are not available yet.</span>
                </div>
              </div>
              <a-button disabled block>
                <Plus class="button-leading-icon" aria-hidden="true" />
                Attach
              </a-button>
            </a-card>
          </aside>
        </div>
      </template>

      <a-empty v-else-if="!loading" description="Deal detail could not be loaded." />
    </a-spin>

    <a-modal
      v-model:open="editDealOpen"
      title="Edit deal"
      ok-text="Save"
      cancel-text="Cancel"
      :confirm-loading="mutating"
      destroy-on-close
      @ok="submitDealEdit"
    >
      <a-form ref="dealFormRef" :model="dealForm" layout="vertical">
        <a-form-item label="Status" name="status">
          <a-select v-model:value="dealForm.status" :options="statusOptions" />
        </a-form-item>
        <a-form-item v-if="lostReasonInputEnabled" label="Lost reason" name="lostReason">
          <a-input
            v-model:value="dealForm.lostReason"
          />
        </a-form-item>
        <a-form-item label="Internal notes" name="internalNotes">
          <a-textarea v-model:value="dealForm.internalNotes" :rows="4" />
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
            placeholder="Add deal tags"
            :max-tag-count="8"
          />
          <p class="form-help">Use up to 20 tags. Tags support letters, numbers, spaces, -, _, /, ., and &.</p>
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="deliverableModalOpen"
      :title="editingDeliverable ? 'Edit deliverable' : 'Add deliverable'"
      ok-text="Save"
      cancel-text="Cancel"
      :confirm-loading="mutating"
      destroy-on-close
      @ok="submitDeliverable"
    >
      <a-form ref="deliverableFormRef" :model="deliverableForm" layout="vertical">
        <a-form-item
          label="Type"
          name="type"
          :rules="[{ required: true, message: 'Deliverable type is required.' }]"
        >
          <a-input v-model:value="deliverableForm.type" placeholder="reel, story, post" />
        </a-form-item>
        <div class="form-grid">
          <a-form-item label="Quantity" name="quantity">
            <a-input-number
              v-model:value="deliverableForm.quantity"
              :min="1"
              :precision="0"
              class="full-width"
            />
          </a-form-item>
          <a-form-item label="Status" name="status">
            <a-select v-model:value="deliverableForm.status" :options="deliverableStatusOptions" />
          </a-form-item>
        </div>
        <a-form-item label="Due date" name="dueDate">
          <a-date-picker
            v-model:value="deliverableForm.dueDate"
            value-format="YYYY-MM-DD"
            class="full-width"
          />
        </a-form-item>
        <a-form-item label="Published URL" name="publishedUrl">
          <a-input v-model:value="deliverableForm.publishedUrl" placeholder="https://..." />
        </a-form-item>
        <a-form-item label="Notes" name="notes">
          <a-textarea v-model:value="deliverableForm.notes" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="compensationModalOpen"
      :title="editingCompensationItem ? 'Edit compensation item' : 'Add compensation item'"
      ok-text="Save"
      cancel-text="Cancel"
      :confirm-loading="mutating"
      destroy-on-close
      @ok="submitCompensation"
    >
      <a-form ref="compensationFormRef" :model="compensationForm" layout="vertical">
        <a-form-item label="Type" name="type">
          <a-select v-model:value="compensationForm.type" :options="compensationTypeOptions" />
        </a-form-item>
        <a-form-item label="Description" name="description">
          <a-input v-model:value="compensationForm.description" placeholder="Optional description" />
        </a-form-item>
        <div class="form-grid">
          <a-form-item label="Amount" name="amount">
            <a-input-number
              v-model:value="compensationForm.amount"
              :min="0"
              :precision="2"
              class="full-width"
              placeholder="0"
            />
          </a-form-item>
          <a-form-item label="Currency" name="currency">
            <a-input v-model:value="compensationForm.currency" placeholder="USD" />
          </a-form-item>
        </div>
        <div class="form-grid">
          <a-form-item label="Status" name="status">
            <a-select v-model:value="compensationForm.status" :options="compensationStatusOptions" />
          </a-form-item>
          <a-form-item label="Due date" name="dueDate">
            <a-date-picker
              v-model:value="compensationForm.dueDate"
              value-format="YYYY-MM-DD"
              class="full-width"
            />
          </a-form-item>
        </div>
        <a-form-item label="Recipient" name="recipientName">
          <a-input v-model:value="compensationForm.recipientName" placeholder="Creator or manager" />
        </a-form-item>
        <a-form-item label="Notes" name="notes">
          <a-textarea v-model:value="compensationForm.notes" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>

<style scoped>
.deal-detail-page {
  display: grid;
  gap: 18px;
}

.deal-detail-page :deep(.ant-spin-container) {
  display: grid;
  gap: 18px;
}

.page-alert {
  border-radius: 8px;
}

h1,
h2 {
  margin: 0;
  color: #20262d;
  font-weight: 600;
}

h1 {
  font-size: 30px;
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

h2 {
  font-size: 26px;
}

.heading-meta,
.page-actions,
.tag-row,
.card-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.page-actions {
  align-items: flex-start;
  justify-content: flex-end;
  flex-shrink: 0;
}

.heading-meta {
  color: #58636f;
}

.deal-hero {
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

.deal-workspace-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  align-items: start;
  gap: 18px;
}

.deal-main,
.deal-sidebar {
  display: grid;
  gap: 14px;
  min-width: 0;
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
  font-size: 18px;
  font-weight: 500;
  line-height: 1.25;
}

.work-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18px;
}

.section-card {
  min-width: 0;
  overflow: hidden;
}

.section-card :deep(.ant-card-body) {
  min-width: 0;
  overflow-x: auto;
}

.section-card :deep(.ant-table-wrapper) {
  max-width: 100%;
  min-width: 0;
}

.side-card {
  min-width: 0;
  overflow: hidden;
}

.side-card :deep(.ant-card-head) {
  min-height: 42px;
}

.side-card :deep(.ant-card-head-title) {
  font-size: 13px;
  font-weight: 550;
}

.section-card :deep(.ant-card-head-title) {
  font-weight: 600;
}

.side-card :deep(.ant-card-body) {
  min-width: 0;
}

.influencer-card {
  display: grid;
  gap: 10px;
}

.influencer-card p,
.cell-note,
.notes,
.muted {
  color: #697582;
}

.influencer-card p,
.notes,
.cell-note {
  margin: 0;
  line-height: 1.5;
}

.property-list {
  display: grid;
  gap: 12px;
}

.property-list div {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.property-list span {
  color: #697582;
  font-size: 12px;
  font-weight: 500;
}

.property-list strong {
  min-width: 0;
  overflow-wrap: anywhere;
  color: #20262d;
  font-weight: 500;
  line-height: 1.35;
}

.section-card strong {
  font-weight: 500;
}

.notes {
  white-space: pre-wrap;
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

.cell-note {
  margin-top: 4px;
  font-size: 12px;
}

.form-help {
  margin: 6px 0 0;
  color: #697582;
  font-size: 12px;
  line-height: 1.4;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.full-width {
  width: 100%;
}

@media (max-width: 1100px) {
  .deal-hero,
  .deal-workspace-layout,
  .work-grid {
    display: grid;
    grid-template-columns: 1fr;
  }

  .page-actions {
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

@media (max-width: 720px) {
  .deal-hero {
    padding: 18px;
  }

  .metrics-strip {
    grid-template-columns: 1fr;
  }

  .page-actions {
    display: grid;
  }

  .page-actions a,
  .page-actions button {
    width: 100%;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
