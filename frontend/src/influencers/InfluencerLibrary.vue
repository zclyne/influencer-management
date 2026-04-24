<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { createManualInfluencer, errorMessage } from '../api/client'
import type { CampaignResponse, ManualInfluencerResponse } from '../api/types'
import StatusBadge from '../shared/StatusBadge.vue'

const props = defineProps<{
  campaigns: CampaignResponse[]
  selectedCampaignId: string | null
}>()

const emit = defineEmits<{
  campaignChanged: [campaignId: string]
}>()

const form = reactive({
  displayName: '',
  fullName: '',
  platform: 'instagram',
  username: '',
  profileUrl: '',
  followerCount: '',
  email: '',
  country: '',
  city: '',
  notes: '',
  targetCampaignId: props.selectedCampaignId ?? '',
})

const search = ref('')
const saving = ref(false)
const saveError = ref<string | null>(null)
const lastCreated = ref<ManualInfluencerResponse | null>(null)

const campaignOptions = computed(() => props.campaigns)

watch(
  () => props.selectedCampaignId,
  (campaignId) => {
    form.targetCampaignId = campaignId ?? ''
  },
)

const submitManualInfluencer = async () => {
  if (!form.displayName.trim()) return

  saving.value = true
  saveError.value = null
  lastCreated.value = null

  try {
    lastCreated.value = await createManualInfluencer({
      display_name: form.displayName.trim(),
      full_name: form.fullName.trim() || null,
      platform: form.platform.trim() || null,
      username: form.username.trim() || null,
      profile_url: form.profileUrl.trim() || null,
      follower_count: form.followerCount ? Number(form.followerCount) : null,
      emails: form.email.trim() ? [form.email.trim()] : [],
      country: form.country.trim() || null,
      city: form.city.trim() || null,
      notes: form.notes.trim() || null,
      target_campaign_id: form.targetCampaignId || null,
    })

    form.displayName = ''
    form.fullName = ''
    form.username = ''
    form.profileUrl = ''
    form.followerCount = ''
    form.email = ''
    form.country = ''
    form.city = ''
    form.notes = ''
  } catch (error) {
    saveError.value = errorMessage(error)
  } finally {
    saving.value = false
  }
}

const selectTargetCampaign = (campaignId: string) => {
  form.targetCampaignId = campaignId
  if (campaignId) emit('campaignChanged', campaignId)
}
</script>

<template>
  <section class="library-grid">
    <section class="library-main">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Influencer Library</p>
          <h1>Global profiles</h1>
        </div>
      </div>

      <div class="search-row">
        <input v-model="search" type="search" placeholder="Search by name, handle, email, or country" />
        <button type="button" class="secondary-button" disabled>Search</button>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Primary platform</th>
              <th>Contacts</th>
              <th>Location</th>
              <th>Library status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colspan="5">
                <div class="empty-state">
                  <strong>Library list endpoint pending</strong>
                  <span>
                    Manual creation is wired to the backend now. Search, platform management, contacts, and
                    audience snapshots will load here when the Influencer Library CRUD APIs land.
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <aside class="manual-panel">
      <div class="section-heading compact">
        <div>
          <p class="eyebrow">Manual entry</p>
          <h2>Add influencer</h2>
        </div>
        <StatusBadge label="Real API" tone="active" />
      </div>

      <form class="manual-form" @submit.prevent="submitManualInfluencer">
        <label>
          Display name
          <input v-model="form.displayName" type="text" placeholder="Creator name" />
        </label>
        <label>
          Full name
          <input v-model="form.fullName" type="text" placeholder="Optional legal or full name" />
        </label>
        <div class="form-row">
          <label>
            Platform
            <input v-model="form.platform" type="text" placeholder="instagram" />
          </label>
          <label>
            Username
            <input v-model="form.username" type="text" placeholder="handle" />
          </label>
        </div>
        <label>
          Profile URL
          <input v-model="form.profileUrl" type="url" placeholder="https://..." />
        </label>
        <div class="form-row">
          <label>
            Followers
            <input v-model="form.followerCount" type="number" min="0" step="1" placeholder="0" />
          </label>
          <label>
            Email
            <input v-model="form.email" type="email" placeholder="name@example.com" />
          </label>
        </div>
        <div class="form-row">
          <label>
            Country
            <input v-model="form.country" type="text" placeholder="US" />
          </label>
          <label>
            City
            <input v-model="form.city" type="text" placeholder="New York" />
          </label>
        </div>
        <label>
          Add to campaign
          <select
            :value="form.targetCampaignId"
            @change="selectTargetCampaign(($event.target as HTMLSelectElement).value)"
          >
            <option value="">Library only</option>
            <option v-for="campaign in campaignOptions" :key="campaign.id" :value="campaign.id">
              {{ campaign.name }}
            </option>
          </select>
        </label>
        <label>
          Notes
          <textarea v-model="form.notes" rows="4" placeholder="Global library notes"></textarea>
        </label>

        <button type="submit" class="primary-button" :disabled="saving">
          {{ saving ? 'Saving...' : 'Create influencer' }}
        </button>
      </form>

      <div v-if="saveError" class="error-box">{{ saveError }}</div>
      <div v-if="lastCreated" class="success-box">
        Created {{ lastCreated.display_name }} with {{ lastCreated.platform_count }} platform row(s) and
        {{ lastCreated.contact_count }} contact row(s).
      </div>
    </aside>
  </section>
</template>

<style scoped>
.library-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 380px);
  gap: 20px;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-heading.compact {
  margin-bottom: 12px;
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

.search-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  margin-bottom: 14px;
}

.manual-panel,
.table-wrap {
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
}

.manual-panel {
  padding: 16px;
}

.manual-form {
  display: grid;
  gap: 12px;
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
select,
textarea {
  width: 100%;
  min-width: 0;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0 10px;
  background: #ffffff;
  color: #242826;
  font: inherit;
}

input,
select {
  height: 36px;
}

textarea {
  padding-top: 9px;
  resize: vertical;
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

.primary-button:disabled,
.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 720px;
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
.success-box {
  margin-top: 12px;
  padding: 10px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.45;
}

.error-box {
  border: 1px solid #f1b4ae;
  background: #fff0ee;
  color: #9f2d20;
}

.success-box {
  border: 1px solid #9fc7ba;
  background: #e8f5ef;
  color: #17634d;
}

@media (max-width: 1020px) {
  .library-grid {
    grid-template-columns: 1fr;
  }
}
</style>
