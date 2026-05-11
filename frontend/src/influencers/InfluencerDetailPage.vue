<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { message, Modal, type FormInstance, type TableColumnsType } from 'ant-design-vue'
import { Pencil, Plus, Trash2 } from '@lucide/vue'
import type {
  ContactRole,
  InfluencerContactCreateRequest,
  InfluencerContactResponse,
  InfluencerDealSummary,
  InfluencerPlatformCreateRequest,
  InfluencerPlatformResponse,
  InfluencerUpdateRequest,
} from '../api/types'
import { normalizeInfluencerTags, platformColor, platformOptions } from './useInfluencers'
import { useInfluencerDetail } from './useInfluencerDetail'

interface ProfileForm {
  displayName: string
  fullName: string
  country: string
  city: string
  bio: string
}

interface PlatformForm {
  platform: string
  username: string
  profileUrl: string
  followerCount: number | null
  engagementRatePercent: number | null
  bio: string
}

interface ContactForm {
  email: string
  name: string
  role: ContactRole
  isPrimary: boolean
  source: string
  notes: string
}

interface TagsForm {
  tags: string[]
}

const route = useRoute()
const influencerId = computed(() => String(route.params.influencerId ?? ''))

const profileFormRef = ref<FormInstance>()
const notesFormRef = ref<FormInstance>()
const platformFormRef = ref<FormInstance>()
const contactFormRef = ref<FormInstance>()

const profileModalOpen = ref(false)
const notesModalOpen = ref(false)
const tagsModalOpen = ref(false)
const platformModalOpen = ref(false)
const contactModalOpen = ref(false)
const editingPlatform = ref<InfluencerPlatformResponse | null>(null)
const editingContact = ref<InfluencerContactResponse | null>(null)

const {
  influencer,
  loading,
  mutating,
  error,
  primaryContact,
  loadInfluencerDetail,
  updateProfile,
  archiveProfile,
  createPlatform,
  updatePlatform,
  deletePlatform,
  createContact,
  updateContact,
  deleteContact,
} = useInfluencerDetail(() => influencerId.value)

const profileForm = reactive<ProfileForm>({
  displayName: '',
  fullName: '',
  country: '',
  city: '',
  bio: '',
})

const notesForm = reactive({
  notes: '',
})

const tagsForm = reactive<TagsForm>({
  tags: [],
})

const platformForm = reactive<PlatformForm>({
  platform: 'instagram',
  username: '',
  profileUrl: '',
  followerCount: null,
  engagementRatePercent: null,
  bio: '',
})

const contactForm = reactive<ContactForm>({
  email: '',
  name: '',
  role: 'unknown',
  isPrimary: false,
  source: '',
  notes: '',
})

const platformColumns: TableColumnsType<InfluencerPlatformResponse> = [
  {
    title: 'Platform',
    key: 'platform',
    width: 150,
  },
  {
    title: 'Username',
    key: 'username',
    width: 170,
  },
  {
    title: 'Profile URL',
    key: 'profileUrl',
    width: 240,
  },
  {
    title: 'Followers',
    key: 'followers',
    dataIndex: 'follower_count',
    width: 130,
  },
  {
    title: 'Eng.',
    key: 'engagement',
    dataIndex: 'engagement_rate',
    width: 110,
  },
  {
    title: 'Actions',
    key: 'actions',
    fixed: 'right',
    width: 150,
  },
]

const contactColumns: TableColumnsType<InfluencerContactResponse> = [
  {
    title: 'Contact',
    key: 'contact',
    width: 220,
  },
  {
    title: 'Role',
    key: 'role',
    width: 120,
  },
  {
    title: 'Primary',
    key: 'primary',
    width: 100,
  },
  {
    title: 'Source',
    key: 'source',
    width: 120,
  },
  {
    title: 'Actions',
    key: 'actions',
    fixed: 'right',
    width: 150,
  },
]

const dealColumns: TableColumnsType<InfluencerDealSummary> = [
  {
    title: 'Campaign',
    key: 'campaign',
    width: 240,
  },
  {
    title: 'Status',
    key: 'status',
    width: 150,
  },
  {
    title: 'Created',
    key: 'created',
    dataIndex: 'created_at',
    width: 150,
  },
  {
    title: 'Updated',
    key: 'updated',
    dataIndex: 'updated_at',
    width: 150,
  },
  {
    title: 'Actions',
    key: 'actions',
    fixed: 'right',
    width: 130,
  },
]

const contactRoleOptions: { label: string; value: ContactRole }[] = [
  { label: 'Creator', value: 'creator' },
  { label: 'Manager', value: 'manager' },
  { label: 'Agency', value: 'agency' },
  { label: 'Assistant', value: 'assistant' },
  { label: 'Business', value: 'business' },
  { label: 'Unknown', value: 'unknown' },
]

const pageTitle = computed(() => influencer.value?.display_name ?? 'Influencer detail')

const locationLabel = computed(() => {
  if (!influencer.value) return 'Not set'
  return [influencer.value.city, influencer.value.country].filter(Boolean).join(', ') || 'Not set'
})

const activeDeals = computed(
  () => influencer.value?.deals.filter((deal) => !deal.archived_at) ?? [],
)

const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 'Not set'
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(
    value,
  )
}

const formatDate = (value: string | null | undefined) => {
  if (!value) return 'Not set'
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))
}

const formatPercent = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === '') return 'Not set'
  const numericValue = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(numericValue)) return String(value)
  const percentValue = Math.abs(numericValue) <= 1 ? numericValue * 100 : numericValue
  return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(percentValue)}%`
}

const decimalToPercent = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === '') return null
  const numericValue = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(numericValue)) return null
  return Math.abs(numericValue) <= 1 ? numericValue * 100 : numericValue
}

const percentToDecimal = (value: number | null) => {
  if (value === null || value === undefined) return null
  return Number((value / 100).toFixed(6))
}

const trimOrNull = (value: string) => value.trim() || null

const platformDisplayName = (platform: string) => {
  const option = platformOptions.find((item) => item.value === platform)
  return option?.label ?? platform
}

const platformTagLabel = (platform: InfluencerPlatformResponse) => {
  const username = platform.username ? ` @${platform.username}` : ''
  const followers = platform.follower_count ? ` ${formatNumber(platform.follower_count)}` : ''
  return `${platformDisplayName(platform.platform)}${username}${followers}`
}

const roleLabel = (role: ContactRole) =>
  contactRoleOptions.find((option) => option.value === role)?.label ?? role

const statusColor = (status: string) => {
  if (status === 'ACTIVE') return 'green'
  if (status === 'COMPLETED') return 'blue'
  if (status === 'LOST') return 'red'
  return 'default'
}

const resetProfileForm = () => {
  profileForm.displayName = influencer.value?.display_name ?? ''
  profileForm.fullName = influencer.value?.full_name ?? ''
  profileForm.country = influencer.value?.country ?? ''
  profileForm.city = influencer.value?.city ?? ''
  profileForm.bio = influencer.value?.bio ?? ''
  profileFormRef.value?.clearValidate()
}

const resetNotesForm = () => {
  notesForm.notes = influencer.value?.notes ?? ''
  notesFormRef.value?.clearValidate()
}

const resetTagsForm = () => {
  tagsForm.tags = [...(influencer.value?.tags ?? [])]
}

const resetPlatformForm = () => {
  platformForm.platform = 'instagram'
  platformForm.username = ''
  platformForm.profileUrl = ''
  platformForm.followerCount = null
  platformForm.engagementRatePercent = null
  platformForm.bio = ''
  platformFormRef.value?.clearValidate()
}

const resetContactForm = () => {
  contactForm.email = ''
  contactForm.name = ''
  contactForm.role = 'unknown'
  contactForm.isPrimary = false
  contactForm.source = ''
  contactForm.notes = ''
  contactFormRef.value?.clearValidate()
}

const openProfileEdit = () => {
  resetProfileForm()
  profileModalOpen.value = true
}

const openNotesEdit = () => {
  resetNotesForm()
  notesModalOpen.value = true
}

const openTagsEdit = () => {
  resetTagsForm()
  tagsModalOpen.value = true
}

const openCreatePlatform = () => {
  editingPlatform.value = null
  resetPlatformForm()
  platformModalOpen.value = true
}

const openEditPlatform = (platform: InfluencerPlatformResponse) => {
  editingPlatform.value = platform
  platformForm.platform = platform.platform
  platformForm.username = platform.username ?? ''
  platformForm.profileUrl = platform.profile_url ?? ''
  platformForm.followerCount = platform.follower_count ?? null
  platformForm.engagementRatePercent = decimalToPercent(platform.engagement_rate)
  platformForm.bio = platform.bio ?? ''
  platformModalOpen.value = true
}

const openCreateContact = () => {
  editingContact.value = null
  resetContactForm()
  contactModalOpen.value = true
}

const openEditContact = (contact: InfluencerContactResponse) => {
  editingContact.value = contact
  contactForm.email = contact.email
  contactForm.name = contact.name ?? ''
  contactForm.role = contact.role
  contactForm.isPrimary = contact.is_primary
  contactForm.source = contact.source ?? ''
  contactForm.notes = contact.notes ?? ''
  contactModalOpen.value = true
}

const buildProfilePayload = (): InfluencerUpdateRequest => ({
  display_name: profileForm.displayName.trim(),
  full_name: trimOrNull(profileForm.fullName),
  country: trimOrNull(profileForm.country),
  city: trimOrNull(profileForm.city),
  bio: trimOrNull(profileForm.bio),
})

const buildPlatformPayload = (): InfluencerPlatformCreateRequest => ({
  platform: platformForm.platform.trim(),
  username: trimOrNull(platformForm.username),
  profile_url: trimOrNull(platformForm.profileUrl),
  follower_count: platformForm.followerCount,
  engagement_rate: percentToDecimal(platformForm.engagementRatePercent),
  bio: trimOrNull(platformForm.bio),
})

const buildContactPayload = (): InfluencerContactCreateRequest => ({
  email: contactForm.email.trim(),
  name: trimOrNull(contactForm.name),
  role: contactForm.role,
  is_primary: contactForm.isPrimary,
  source: trimOrNull(contactForm.source),
  notes: trimOrNull(contactForm.notes),
})

const submitProfile = async () => {
  await profileFormRef.value?.validate()

  try {
    await updateProfile(buildProfilePayload())
    message.success('Influencer updated.')
    profileModalOpen.value = false
  } catch {
    message.error('Influencer could not be updated.')
  }
}

const submitNotes = async () => {
  await notesFormRef.value?.validate()

  try {
    await updateProfile({ notes: trimOrNull(notesForm.notes) })
    message.success('Notes updated.')
    notesModalOpen.value = false
  } catch {
    message.error('Notes could not be saved.')
  }
}

const submitTags = async () => {
  try {
    const tags = normalizeInfluencerTags(tagsForm.tags)
    await updateProfile({ tags })
    message.success('Tags updated.')
    tagsModalOpen.value = false
  } catch (tagError) {
    message.error(tagError instanceof Error ? tagError.message : 'Tags could not be saved.')
  }
}

const submitPlatform = async () => {
  await platformFormRef.value?.validate()

  try {
    if (editingPlatform.value) {
      await updatePlatform(editingPlatform.value, buildPlatformPayload())
      message.success('Platform updated.')
    } else {
      await createPlatform(buildPlatformPayload())
      message.success('Platform added.')
    }
    platformModalOpen.value = false
  } catch {
    message.error('Platform could not be saved.')
  }
}

const submitContact = async () => {
  await contactFormRef.value?.validate()

  try {
    if (editingContact.value) {
      await updateContact(editingContact.value, buildContactPayload())
      message.success('Contact updated.')
    } else {
      await createContact(buildContactPayload())
      message.success('Contact added.')
    }
    contactModalOpen.value = false
  } catch {
    message.error('Contact could not be saved.')
  }
}

const confirmArchive = () => {
  if (!influencer.value) return

  Modal.confirm({
    title: 'Delete this influencer?',
    content: 'Deleted influencers are hidden from default lists but remain available in history.',
    okText: 'Delete',
    okType: 'danger',
    cancelText: 'Cancel',
    async onOk() {
      try {
        await archiveProfile()
        message.success(`${pageTitle.value} deleted.`)
      } catch {
        message.error('Influencer could not be deleted.')
      }
    },
  })
}

const removePlatform = async (platform: InfluencerPlatformResponse) => {
  try {
    await deletePlatform(platform)
    message.success('Platform deleted.')
  } catch {
    message.error('Platform could not be deleted.')
  }
}

const removeContact = async (contact: InfluencerContactResponse) => {
  try {
    await deleteContact(contact)
    message.success('Contact deleted.')
  } catch {
    message.error('Contact could not be deleted.')
  }
}

watch(influencerId, () => {
  void loadInfluencerDetail()
})

void loadInfluencerDetail()
</script>

<template>
  <section class="influencer-detail-page">
    <a-breadcrumb>
      <a-breadcrumb-item>
        <RouterLink :to="{ name: 'influencers' }">Influencers</RouterLink>
      </a-breadcrumb-item>
      <a-breadcrumb-item>{{ pageTitle }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-alert v-if="error" class="page-alert" type="error" :message="error" show-icon />

    <a-spin :spinning="loading">
      <template v-if="influencer">
        <div class="page-heading">
          <div>
            <h1>{{ influencer.display_name }}</h1>
            <div class="heading-meta">
              <a-tag v-if="influencer.archived_at" color="red">Deleted</a-tag>
              <a-tag v-else color="green">Active</a-tag>
              <span>Updated {{ formatDate(influencer.updated_at) }}</span>
            </div>
          </div>
          <div class="page-actions">
            <a-button
              danger
              :disabled="Boolean(influencer.archived_at)"
              :loading="mutating"
              @click="confirmArchive"
            >
              <Trash2 class="button-leading-icon" aria-hidden="true" />
              Delete
            </a-button>
            <a-button type="primary" @click="openProfileEdit">
              <Pencil class="button-leading-icon" aria-hidden="true" />
              Edit profile
            </a-button>
          </div>
        </div>

        <div class="influencer-overview">
          <a-card size="small">
            <span>Full name</span>
            <strong>{{ influencer.full_name || 'Not set' }}</strong>
          </a-card>
          <a-card size="small">
            <span>Location</span>
            <strong>{{ locationLabel }}</strong>
          </a-card>
          <a-card size="small">
            <span>Primary contact</span>
            <strong>{{ primaryContact?.email ?? 'No contact' }}</strong>
          </a-card>
          <a-card size="small">
            <span>Platforms</span>
            <strong>{{ influencer.platforms.length }} linked</strong>
          </a-card>
        </div>

        <div class="profile-info-grid">
          <a-card class="bio-card section-card" size="small">
            <template #title>Bio</template>
            <p>{{ influencer.bio || 'No bio yet.' }}</p>
          </a-card>

          <a-card class="section-card">
            <template #title>Tags</template>
            <template #extra>
              <a-button @click="openTagsEdit">
                <Pencil class="button-leading-icon" aria-hidden="true" />
                Edit
              </a-button>
            </template>
            <div v-if="influencer.tags.length" class="tag-row">
              <a-tag v-for="tag in influencer.tags" :key="tag">{{ tag }}</a-tag>
            </div>
            <span v-else class="muted">No tags</span>
          </a-card>

          <a-card class="section-card">
            <template #title>Contacts</template>
            <template #extra>
              <a-button @click="openCreateContact">
                <Plus class="button-leading-icon" aria-hidden="true" />
                Add contact
              </a-button>
            </template>
            <a-table
              :columns="contactColumns"
              :data-source="influencer.contacts"
              :pagination="false"
              :row-key="(record: InfluencerContactResponse) => record.id"
              :scroll="{ x: 720 }"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'contact'">
                  <strong>{{ record.email }}</strong>
                  <p v-if="record.name" class="cell-note">{{ record.name }}</p>
                  <p v-if="record.conflict_influencer_ids.length" class="cell-warning">
                    Same email on {{ record.conflict_influencer_ids.length }} other influencer(s)
                  </p>
                </template>
                <template v-else-if="column.key === 'role'">
                  {{ roleLabel(record.role) }}
                </template>
                <template v-else-if="column.key === 'primary'">
                  <a-tag v-if="record.is_primary" color="green">Yes</a-tag>
                  <span v-else>No</span>
                </template>
                <template v-else-if="column.key === 'source'">
                  {{ record.source || 'Not set' }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button
                      class="table-action-icon"
                      type="text"
                      title="Edit contact"
                      aria-label="Edit contact"
                      @click="openEditContact(record)"
                    >
                      <Pencil aria-hidden="true" />
                    </a-button>
                    <a-popconfirm
                      title="Delete this contact?"
                      ok-text="Delete"
                      cancel-text="Cancel"
                      @confirm="removeContact(record)"
                    >
                      <a-button
                        class="table-action-icon"
                        danger
                        type="text"
                        title="Delete contact"
                        aria-label="Delete contact"
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
            <template #title>Notes</template>
            <template #extra>
              <a-button @click="openNotesEdit">
                <Pencil class="button-leading-icon" aria-hidden="true" />
                Edit
              </a-button>
            </template>
            <p v-if="influencer.notes" class="notes-content">{{ influencer.notes }}</p>
            <span v-else class="muted">No notes yet.</span>
          </a-card>
        </div>

        <div class="content-grid">
          <a-card class="section-card platform-card">
            <template #title>Platform identities</template>
            <template #extra>
              <a-button @click="openCreatePlatform">
                <Plus class="button-leading-icon" aria-hidden="true" />
                Add platform
              </a-button>
            </template>
            <a-table
              :columns="platformColumns"
              :data-source="influencer.platforms"
              :pagination="false"
              :row-key="(record: InfluencerPlatformResponse) => record.id"
              :scroll="{ x: 900 }"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'platform'">
                  <a-tag :color="platformColor(record.platform)">
                    {{ platformDisplayName(record.platform) }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'username'">
                  {{ record.username ? `@${record.username}` : 'Not set' }}
                </template>
                <template v-else-if="column.key === 'profileUrl'">
                  <a
                    v-if="record.profile_url"
                    :href="record.profile_url"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open profile
                  </a>
                  <span v-else class="muted">Not set</span>
                </template>
                <template v-else-if="column.key === 'followers'">
                  {{ formatNumber(record.follower_count) }}
                </template>
                <template v-else-if="column.key === 'engagement'">
                  {{ formatPercent(record.engagement_rate) }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button
                      class="table-action-icon"
                      type="text"
                      title="Edit platform"
                      aria-label="Edit platform"
                      @click="openEditPlatform(record)"
                    >
                      <Pencil aria-hidden="true" />
                    </a-button>
                    <a-popconfirm
                      title="Delete this platform?"
                      ok-text="Delete"
                      cancel-text="Cancel"
                      @confirm="removePlatform(record)"
                    >
                      <a-button
                        class="table-action-icon"
                        danger
                        type="text"
                        title="Delete platform"
                        aria-label="Delete platform"
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
            <template #title>Campaign deals</template>
            <a-table
              :columns="dealColumns"
              :data-source="activeDeals"
              :pagination="false"
              :row-key="(record: InfluencerDealSummary) => record.id"
              :scroll="{ x: 760 }"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'campaign'">
                  <strong>{{ record.campaign_name || 'Campaign' }}</strong>
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
                </template>
                <template v-else-if="column.key === 'created'">
                  {{ formatDate(record.created_at) }}
                </template>
                <template v-else-if="column.key === 'updated'">
                  {{ formatDate(record.updated_at) }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <RouterLink
                    :to="{
                      name: 'dealDetail',
                      params: { campaignId: record.campaign_id, dealId: record.id },
                    }"
                  >
                    <a-button type="link">Open</a-button>
                  </RouterLink>
                </template>
              </template>
            </a-table>
          </a-card>
        </div>
      </template>

      <a-empty v-else-if="!loading" description="Influencer detail could not be loaded." />
    </a-spin>

    <a-modal
      v-model:open="profileModalOpen"
      title="Edit influencer"
      ok-text="Save"
      cancel-text="Cancel"
      :confirm-loading="mutating"
      destroy-on-close
      @ok="submitProfile"
    >
      <a-form ref="profileFormRef" :model="profileForm" layout="vertical">
        <a-form-item
          label="Display name"
          name="displayName"
          :rules="[{ required: true, message: 'Display name is required.' }]"
        >
          <a-input v-model:value="profileForm.displayName" />
        </a-form-item>
        <a-form-item label="Full name" name="fullName">
          <a-input v-model:value="profileForm.fullName" />
        </a-form-item>
        <div class="form-grid">
          <a-form-item label="Country" name="country">
            <a-input v-model:value="profileForm.country" />
          </a-form-item>
          <a-form-item label="City" name="city">
            <a-input v-model:value="profileForm.city" />
          </a-form-item>
        </div>
        <a-form-item label="Bio" name="bio">
          <a-textarea v-model:value="profileForm.bio" :rows="3" />
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
      <a-form ref="notesFormRef" :model="notesForm" layout="vertical">
        <a-form-item label="Notes" name="notes">
          <a-textarea v-model:value="notesForm.notes" :rows="5" placeholder="Global library notes" />
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
            placeholder="Add global tags"
            :max-tag-count="8"
          />
          <p class="form-help">Use up to 20 tags. Tags support letters, numbers, spaces, -, _, /, ., and &.</p>
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="platformModalOpen"
      :title="editingPlatform ? 'Edit platform' : 'Add platform'"
      ok-text="Save"
      cancel-text="Cancel"
      :confirm-loading="mutating"
      destroy-on-close
      @ok="submitPlatform"
    >
      <a-form ref="platformFormRef" :model="platformForm" layout="vertical">
        <a-form-item
          label="Platform"
          name="platform"
          :rules="[{ required: true, message: 'Platform is required.' }]"
        >
          <a-select v-model:value="platformForm.platform" :options="platformOptions" />
        </a-form-item>
        <a-form-item label="Username" name="username">
          <a-input v-model:value="platformForm.username" placeholder="without @" />
        </a-form-item>
        <a-form-item label="Profile URL" name="profileUrl">
          <a-input v-model:value="platformForm.profileUrl" placeholder="https://..." />
        </a-form-item>
        <div class="form-grid">
          <a-form-item label="Followers" name="followerCount">
            <a-input-number
              v-model:value="platformForm.followerCount"
              :min="0"
              :precision="0"
              class="full-width"
            />
          </a-form-item>
          <a-form-item label="Engagement rate (%)" name="engagementRatePercent">
            <a-input-number
              v-model:value="platformForm.engagementRatePercent"
              :min="0"
              :precision="2"
              class="full-width"
            />
          </a-form-item>
        </div>
        <a-form-item label="Platform bio" name="bio">
          <a-textarea v-model:value="platformForm.bio" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="contactModalOpen"
      :title="editingContact ? 'Edit contact' : 'Add contact'"
      ok-text="Save"
      cancel-text="Cancel"
      :confirm-loading="mutating"
      destroy-on-close
      @ok="submitContact"
    >
      <a-form ref="contactFormRef" :model="contactForm" layout="vertical">
        <a-form-item
          label="Email"
          name="email"
          :rules="[{ required: true, type: 'email', message: 'A valid email is required.' }]"
        >
          <a-input v-model:value="contactForm.email" />
        </a-form-item>
        <a-form-item label="Name" name="name">
          <a-input v-model:value="contactForm.name" />
        </a-form-item>
        <div class="form-grid">
          <a-form-item label="Role" name="role">
            <a-select v-model:value="contactForm.role" :options="contactRoleOptions" />
          </a-form-item>
          <a-form-item label="Source" name="source">
            <a-input v-model:value="contactForm.source" placeholder="manual, modash" />
          </a-form-item>
        </div>
        <a-form-item name="isPrimary">
          <a-checkbox v-model:checked="contactForm.isPrimary">Primary contact</a-checkbox>
        </a-form-item>
        <a-form-item label="Notes" name="notes">
          <a-textarea v-model:value="contactForm.notes" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>

<style scoped>
.influencer-detail-page {
  display: grid;
  gap: 18px;
}

.influencer-detail-page :deep(.ant-spin-container) {
  display: grid;
  gap: 18px;
}

.page-alert {
  border-radius: 8px;
}

.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.profile-main,
.profile-side {
  display: grid;
  align-content: start;
  gap: 14px;
}

h1 {
  margin: 0;
  color: #20262d;
  font-size: 30px;
  line-height: 1.2;
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

.heading-meta,
.page-actions,
.tag-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.heading-meta {
  margin-top: 10px;
  color: #58636f;
}

.page-actions {
  justify-content: flex-end;
}

.influencer-overview {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr));
  gap: 12px;
}

.influencer-overview :deep(.ant-card-body) {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.influencer-overview span {
  color: #697582;
}

.influencer-overview strong {
  min-width: 0;
  overflow-wrap: anywhere;
  color: #20262d;
  font-size: 15px;
  line-height: 1.4;
}

.bio-card p {
  margin: 0;
  color: #3f4954;
  line-height: 1.6;
  white-space: pre-wrap;
}

.cell-note,
.muted {
  color: #697582;
}

.cell-note,
.cell-warning {
  margin: 0;
  line-height: 1.5;
}

.profile-info-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
  align-items: stretch;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.section-card {
  min-width: 0;
  overflow: hidden;
}

.profile-info-grid .section-card {
  height: 100%;
}

.profile-info-grid .section-card :deep(.ant-card) {
  height: 100%;
}

.profile-info-grid .section-card :deep(.ant-card-body) {
  height: calc(100% - 48px);
}

.section-card :deep(.ant-card-body) {
  min-width: 0;
  overflow-x: auto;
}

.section-card :deep(.ant-table-wrapper) {
  max-width: 100%;
  min-width: 0;
}

.cell-note {
  margin-top: 4px;
  font-size: 12px;
}

.cell-warning {
  margin-top: 4px;
  color: #b42318;
  font-size: 12px;
}

.notes-content {
  margin: 0;
  color: #3f4954;
  line-height: 1.6;
  white-space: pre-wrap;
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

@media (max-width: 980px) {
  .influencer-overview {
    grid-template-columns: repeat(2, 1fr);
  }

  .profile-info-grid {
    grid-template-columns: 1fr;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .influencer-overview {
    grid-template-columns: 1fr;
  }
}
</style>
