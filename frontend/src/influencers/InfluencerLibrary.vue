<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { message, Modal, type FormInstance, type TableColumnsType } from 'ant-design-vue'
import type {
  CampaignResponse,
  InfluencerListItem,
  InfluencerPlatformSummary,
  ManualInfluencerInput,
} from '../api/types'
import {
  normalizeInfluencerTags,
  platformColor,
  platformOptions,
  useInfluencers,
} from './useInfluencers'

interface ManualInfluencerForm {
  displayName: string
  fullName: string
  platforms: ManualInfluencerPlatformForm[]
  email: string
  country: string
  city: string
  notes: string
  tags: string[]
  targetCampaignId: string
}

interface ManualInfluencerPlatformForm {
  key: string
  platform: string
  username: string
  followerCount: number | null
}

const props = defineProps<{
  campaigns: CampaignResponse[]
  selectedCampaignId: string | null
}>()

const emit = defineEmits<{
  campaignChanged: [campaignId: string]
}>()

const formRef = ref<FormInstance>()
const createModalOpen = ref(false)
let platformKeySeed = 0

const newPlatformRow = (): ManualInfluencerPlatformForm => {
  platformKeySeed += 1
  return {
    key: `platform-${platformKeySeed}`,
    platform: 'instagram',
    username: '',
    followerCount: null,
  }
}

const createForm = reactive<ManualInfluencerForm>({
  displayName: '',
  fullName: '',
  platforms: [newPlatformRow()],
  email: '',
  country: '',
  city: '',
  notes: '',
  tags: [],
  targetCampaignId: props.selectedCampaignId ?? '',
})

const {
  influencers,
  loading,
  creating,
  archiving,
  error,
  searchText,
  platformFilter,
  countryFilter,
  cityFilter,
  tagFilter,
  includeArchived,
  selectedRowKeys,
  activeInfluencerCount,
  platformCount,
  withContactCount,
  archivedInfluencerCount,
  tagOptions,
  loadInfluencers,
  createInfluencer,
  archiveInfluencer,
  archiveSelectedInfluencers,
} = useInfluencers()

const columns: TableColumnsType<InfluencerListItem> = [
  {
    title: 'Influencer',
    key: 'influencer',
    dataIndex: 'display_name',
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
    title: 'Tags',
    key: 'tags',
    width: 220,
  },
  {
    title: 'Deals',
    key: 'deals',
    dataIndex: 'recent_deal_count',
    align: 'right',
    width: 100,
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
    width: 110,
  },
]

const campaignSelectOptions = computed(() => [
  { label: 'Library only', value: '' },
  ...props.campaigns.map((campaign) => ({
    label: campaign.name,
    value: campaign.id,
  })),
])

const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: (string | number)[]) => {
    selectedRowKeys.value = keys.map(String)
  },
  getCheckboxProps: (record: InfluencerListItem) => ({
    disabled: Boolean(record.archived_at),
  }),
}))

const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 'Not set'
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(
    value,
  )
}

const formatDate = (value: string) =>
  new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))

const formatLocation = (record: InfluencerListItem) =>
  [record.city, record.country].filter(Boolean).join(', ') || 'Not set'

const platformLabel = (value: string) => {
  const option = platformOptions.find((item) => item.value === value)
  return option?.label ?? value
}

const platformDisplayName = (platform: InfluencerPlatformSummary) =>
  platform.username ? `${platformLabel(platform.platform)} @${platform.username}` : platformLabel(platform.platform)

const normalizeFormUsername = (value: string) => value.trim().replace(/^@+/, '')

const addPlatformRow = () => {
  createForm.platforms.push(newPlatformRow())
}

const removePlatformRow = (key: string) => {
  createForm.platforms = createForm.platforms.filter((platform) => platform.key !== key)
  if (!createForm.platforms.length) {
    createForm.platforms.push(newPlatformRow())
  }
}

const resetCreateForm = () => {
  createForm.displayName = ''
  createForm.fullName = ''
  createForm.platforms = [newPlatformRow()]
  createForm.email = ''
  createForm.country = ''
  createForm.city = ''
  createForm.notes = ''
  createForm.tags = []
  createForm.targetCampaignId = props.selectedCampaignId ?? ''
  formRef.value?.clearValidate()
}

const buildPlatformPayload = () =>
  createForm.platforms
    .map((platform) => ({
      platform: platform.platform,
      username: normalizeFormUsername(platform.username),
      follower_count: platform.followerCount,
    }))
    .filter((platform) => platform.username)

const validatePlatformRows = () => {
  const incompleteMetricRows = createForm.platforms.filter(
    (platform) => !normalizeFormUsername(platform.username) && platform.followerCount !== null,
  )
  if (incompleteMetricRows.length > 0) {
    message.error('Platform follower count requires a username.')
    return false
  }

  const seen = new Set<string>()
  for (const platform of buildPlatformPayload()) {
    const key = `${platform.platform}:${platform.username.toLowerCase()}`
    if (seen.has(key)) {
      message.error('Duplicate platform usernames are not allowed.')
      return false
    }
    seen.add(key)
  }
  return true
}

const buildCreatePayload = (): ManualInfluencerInput => ({
  display_name: createForm.displayName.trim(),
  full_name: createForm.fullName.trim() || null,
  platforms: buildPlatformPayload(),
  emails: createForm.email.trim() ? [createForm.email.trim()] : [],
  country: createForm.country.trim() || null,
  city: createForm.city.trim() || null,
  notes: createForm.notes.trim() || null,
  tags: normalizeInfluencerTags(createForm.tags),
  target_campaign_id: createForm.targetCampaignId || null,
})

const openCreateModal = () => {
  createForm.targetCampaignId = props.selectedCampaignId ?? ''
  createModalOpen.value = true
}

const submitCreate = async () => {
  await formRef.value?.validate()
  if (!validatePlatformRows()) return

  try {
    const created = await createInfluencer(buildCreatePayload())
    if (createForm.targetCampaignId) {
      emit('campaignChanged', createForm.targetCampaignId)
    }
    message.success(`${created.display_name} created.`)
    createModalOpen.value = false
    resetCreateForm()
  } catch (createError) {
    message.error(
      createError instanceof Error ? createError.message : 'Influencer could not be created.',
    )
  }
}

const archiveOne = async (influencer: InfluencerListItem) => {
  try {
    await archiveInfluencer(influencer.id)
    message.success(`${influencer.display_name} deleted.`)
  } catch {
    message.error(`${influencer.display_name} could not be deleted.`)
  }
}

const confirmBulkArchive = () => {
  if (!selectedRowKeys.value.length) return

  Modal.confirm({
    title: 'Delete selected influencers?',
    content: 'Deleted influencers are hidden unless Include deleted is turned on.',
    okText: 'Delete selected',
    okType: 'danger',
    cancelText: 'Cancel',
    onOk: async () => {
      const result = await archiveSelectedInfluencers()
      if (result.failed) {
        message.error(`${result.failed} influencer(s) could not be deleted.`)
      }
      if (result.archived) {
        message.success(`${result.archived} influencer(s) deleted.`)
      }
    },
  })
}

watch(
  () => props.selectedCampaignId,
  (campaignId) => {
    if (!createModalOpen.value) {
      createForm.targetCampaignId = campaignId ?? ''
    }
  },
)

watch(createModalOpen, (open) => {
  if (!open) resetCreateForm()
})

void loadInfluencers()
</script>

<template>
  <section class="influencer-library-page">
    <div class="page-heading">
      <div>
        <h1>Influencer library</h1>
        <p class="page-description">
          Reuse global creator profiles across campaigns, review platforms, and add new profiles only
          when needed.
        </p>
      </div>
      <div class="page-actions">
        <RouterLink :to="{ name: 'influencerImport' }">
          <a-button>Import CSV</a-button>
        </RouterLink>
        <a-button type="primary" @click="openCreateModal">New influencer</a-button>
      </div>
    </div>

    <a-alert v-if="error" class="page-alert" type="error" :message="error" show-icon />

    <div class="summary-grid">
      <a-card size="small">
        <span>Library profiles</span>
        <strong>{{ activeInfluencerCount }}</strong>
      </a-card>
      <a-card size="small">
        <span>Platforms</span>
        <strong>{{ platformCount }}</strong>
      </a-card>
      <a-card size="small">
        <span>With contact</span>
        <strong>{{ withContactCount }}</strong>
      </a-card>
      <a-card v-if="includeArchived" size="small">
        <span>Deleted</span>
        <strong>{{ archivedInfluencerCount }}</strong>
      </a-card>
    </div>

    <a-card class="table-card" :body-style="{ padding: '0' }">
      <div class="table-toolbar">
        <div class="table-toolbar-controls">
          <a-input-search
            v-model:value="searchText"
            class="search-input"
            allow-clear
            placeholder="Search names"
          />
          <a-select
            v-model:value="platformFilter"
            class="platform-filter"
            allow-clear
            placeholder="All platforms"
            :options="platformOptions"
          />
          <a-input v-model:value="countryFilter" class="location-filter" allow-clear placeholder="Country" />
          <a-input v-model:value="cityFilter" class="location-filter" allow-clear placeholder="City" />
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
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="influencers"
        :loading="loading"
        :pagination="{ pageSize: 10, showSizeChanger: true }"
        :row-key="(record: InfluencerListItem) => record.id"
        :row-selection="rowSelection"
        :scroll="{ x: 1380 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'influencer'">
            <div class="influencer-cell">
              <RouterLink :to="{ name: 'influencerDetail', params: { influencerId: record.id } }">
                {{ record.display_name }}
              </RouterLink>
              <span v-if="record.full_name">{{ record.full_name }}</span>
              <a-tag v-if="record.archived_at" color="red">Deleted</a-tag>
            </div>
          </template>

          <template v-else-if="column.key === 'platforms'">
            <div v-if="record.platforms.length" class="platform-stack">
              <a-tag
                v-for="platform in record.platforms"
                :key="platform.id"
                :color="platformColor(platform.platform)"
              >
                {{ platformDisplayName(platform) }}
                <span v-if="platform.follower_count"> · {{ formatNumber(platform.follower_count) }}</span>
              </a-tag>
            </div>
            <span v-else class="muted">No platforms</span>
          </template>

          <template v-else-if="column.key === 'contact'">
            <div v-if="record.primary_contact" class="contact-cell">
              <span>{{ record.primary_contact.email }}</span>
              <small v-if="record.primary_contact.name">{{ record.primary_contact.name }}</small>
            </div>
            <span v-else class="muted">No contact</span>
          </template>

          <template v-else-if="column.key === 'location'">
            <span>{{ formatLocation(record) }}</span>
          </template>

          <template v-else-if="column.key === 'tags'">
            <div v-if="record.tags.length" class="tag-stack">
              <a-tag v-for="tag in record.tags" :key="tag">{{ tag }}</a-tag>
            </div>
            <span v-else class="muted">No tags</span>
          </template>

          <template v-else-if="column.key === 'deals'">
            <span>{{ record.recent_deal_count }}</span>
          </template>

          <template v-else-if="column.key === 'updated'">
            <span>{{ formatDate(record.updated_at) }}</span>
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-popconfirm
              v-if="!record.archived_at"
              title="Delete this influencer?"
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
      title="New influencer"
      ok-text="Create influencer"
      cancel-text="Cancel"
      width="720px"
      :confirm-loading="creating"
      destroy-on-close
      @ok="submitCreate"
    >
      <a-form ref="formRef" :model="createForm" layout="vertical">
        <a-form-item
          label="Display name"
          name="displayName"
          :rules="[{ required: true, message: 'Display name is required.' }]"
        >
          <a-input v-model:value="createForm.displayName" placeholder="Creator name" />
        </a-form-item>

        <a-form-item label="Full name" name="fullName">
          <a-input v-model:value="createForm.fullName" placeholder="Optional full name" />
        </a-form-item>

        <a-form-item label="Platforms">
          <div class="manual-platform-list">
            <div
              v-for="(platform, index) in createForm.platforms"
              :key="platform.key"
              class="manual-platform-row"
            >
              <a-select
                v-model:value="platform.platform"
                class="manual-platform-select"
                :options="platformOptions"
              />
              <a-input
                v-model:value="platform.username"
                class="manual-platform-username"
                placeholder="username"
              />
              <a-input-number
                v-model:value="platform.followerCount"
                :min="0"
                :precision="0"
                class="manual-platform-followers"
                placeholder="Followers"
              />
              <a-button
                danger
                type="link"
                :disabled="createForm.platforms.length === 1 && index === 0"
                @click="removePlatformRow(platform.key)"
              >
                Remove
              </a-button>
            </div>
            <a-button type="dashed" block @click="addPlatformRow">Add platform</a-button>
            <p class="form-help">
              Profile URLs are generated from platform and username, then normalized by the backend.
            </p>
          </div>
        </a-form-item>

        <div class="form-grid">
          <a-form-item label="Email" name="email">
            <a-input v-model:value="createForm.email" placeholder="name@example.com" />
          </a-form-item>
          <a-form-item label="Add to campaign" name="targetCampaignId">
            <a-select v-model:value="createForm.targetCampaignId" :options="campaignSelectOptions" />
          </a-form-item>
        </div>

        <div class="form-grid">
          <a-form-item label="Country" name="country">
            <a-input v-model:value="createForm.country" placeholder="US" />
          </a-form-item>
          <a-form-item label="City" name="city">
            <a-input v-model:value="createForm.city" placeholder="New York" />
          </a-form-item>
        </div>

        <a-form-item label="Notes" name="notes">
          <a-textarea v-model:value="createForm.notes" :rows="3" placeholder="Global library notes" />
        </a-form-item>

        <a-form-item label="Tags" name="tags">
          <a-select
            v-model:value="createForm.tags"
            mode="tags"
            placeholder="Add global tags"
            :max-tag-count="5"
          />
          <p class="form-help">Use up to 20 tags. Tags support letters, numbers, spaces, -, _, /, ., and &.</p>
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>

<style scoped>
.influencer-library-page {
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
.table-toolbar-actions {
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

.search-input {
  width: min(300px, 100%);
}

.platform-filter,
.tag-filter {
  width: 160px;
}

.location-filter {
  width: 130px;
}

.archive-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #4e5965;
  white-space: nowrap;
}

.influencer-cell,
.contact-cell {
  display: grid;
  gap: 4px;
}

.influencer-cell a {
  color: #175fcb;
  font-weight: 700;
}

.influencer-cell span,
.contact-cell small {
  max-width: 220px;
  overflow: hidden;
  color: #697582;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.platform-stack,
.tag-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.contact-cell span {
  max-width: 190px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.manual-platform-list {
  display: grid;
  gap: 10px;
}

.manual-platform-row {
  display: grid;
  grid-template-columns: minmax(140px, 0.8fr) minmax(160px, 1fr) minmax(120px, 0.7fr) auto;
  gap: 10px;
}

.manual-platform-select,
.manual-platform-username,
.manual-platform-followers {
  width: 100%;
}

.form-help {
  margin: 0;
  color: #697582;
  font-size: 12px;
  line-height: 1.4;
}

.full-width {
  width: 100%;
}

@media (max-width: 960px) {
  .page-heading,
  .table-toolbar {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .page-heading {
    display: grid;
  }

  .page-actions,
  .table-toolbar-actions {
    justify-content: flex-start;
  }

  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .search-input,
  .platform-filter,
  .tag-filter,
  .location-filter,
  .archive-toggle,
  .table-toolbar-actions,
  .table-toolbar-actions button {
    width: 100%;
  }

  .manual-platform-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .summary-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
