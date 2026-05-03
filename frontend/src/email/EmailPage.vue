<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  disconnectEmail,
  errorMessage,
  getEmailAuthStatus,
  getEmailThread,
  linkEmailThread,
  listCampaignDeals,
  listCampaigns,
  listEmailLabels,
  listEmailThreads,
  startEmailAuth,
  unlinkEmailThread,
} from '../api/client'
import type {
  CampaignResponse,
  DealPipelineRow,
  EmailCrmLink,
  GmailAuthStatusResponse,
  GmailLabelResponse,
  GmailThreadDetailResponse,
  GmailThreadSummary,
} from '../api/types'

const route = useRoute()
const router = useRouter()

const authStatus = ref<GmailAuthStatusResponse | null>(null)
const campaigns = ref<CampaignResponse[]>([])
const deals = ref<DealPipelineRow[]>([])
const labels = ref<GmailLabelResponse[]>([])
const threads = ref<GmailThreadSummary[]>([])
const selectedThread = ref<GmailThreadDetailResponse | null>(null)
const nextPageToken = ref<string | null>(null)
const selectedCampaignId = ref<string | undefined>(route.query.campaignId as string | undefined)
const selectedDealId = ref<string | undefined>(route.query.dealId as string | undefined)
const selectedLabel = ref<string | undefined>()
const query = ref('')
const loading = ref(false)
const detailLoading = ref(false)
const authLoading = ref(false)
const error = ref<string | null>(null)

const connected = computed(() => authStatus.value?.connected === true)

const campaignOptions = computed(() =>
  campaigns.value.map((campaign) => ({ label: campaign.name, value: campaign.id })),
)

const dealOptions = computed(() =>
  deals.value.map((deal) => ({
    label: deal.influencer.display_name,
    value: deal.id,
  })),
)

const labelOptions = computed(() =>
  labels.value
    .filter((label) => label.type !== 'system')
    .map((label) => ({ label: label.name, value: label.name })),
)

const selectedThreadId = computed(() => selectedThread.value?.id ?? (route.query.threadId as string | undefined))

const loadAuthStatus = async () => {
  authStatus.value = await getEmailAuthStatus()
}

const connectGmail = async () => {
  authLoading.value = true
  try {
    const response = await startEmailAuth()
    window.location.href = response.authorization_url
  } catch (authError) {
    message.error(errorMessage(authError))
  } finally {
    authLoading.value = false
  }
}

const disconnect = async () => {
  authLoading.value = true
  try {
    await disconnectEmail()
    authStatus.value = await getEmailAuthStatus()
    threads.value = []
    selectedThread.value = null
    message.success('Gmail disconnected.')
  } catch (disconnectError) {
    message.error(errorMessage(disconnectError))
  } finally {
    authLoading.value = false
  }
}

const syncQueryToRoute = () => {
  const nextQuery: Record<string, string> = {}
  if (selectedCampaignId.value) nextQuery.campaignId = selectedCampaignId.value
  if (selectedDealId.value) nextQuery.dealId = selectedDealId.value
  if (selectedThread.value?.id) nextQuery.threadId = selectedThread.value.id
  void router.replace({ name: 'email', query: nextQuery })
}

const loadCampaigns = async () => {
  const response = await listCampaigns()
  campaigns.value = response.campaigns
}

const loadDeals = async () => {
  if (!selectedCampaignId.value) {
    deals.value = []
    selectedDealId.value = undefined
    return
  }
  const response = await listCampaignDeals(selectedCampaignId.value)
  deals.value = response.deals
  if (selectedDealId.value && !response.deals.some((deal) => deal.id === selectedDealId.value)) {
    selectedDealId.value = undefined
  }
}

const loadLabels = async () => {
  labels.value = (await listEmailLabels()).labels
}

const loadThreads = async (pageToken?: string) => {
  if (!connected.value) return
  loading.value = true
  error.value = null
  try {
    const response = await listEmailThreads({
      campaignId: selectedCampaignId.value,
      dealId: selectedDealId.value,
      query: query.value.trim() || undefined,
      label: selectedLabel.value,
      pageToken,
      pageSize: 20,
    })
    threads.value = pageToken ? [...threads.value, ...response.threads] : response.threads
    nextPageToken.value = response.next_page_token ?? null
    if (!pageToken && response.threads.length > 0) {
      await openThread(response.threads[0].id)
    }
    if (!pageToken && response.threads.length === 0) {
      selectedThread.value = null
    }
    syncQueryToRoute()
  } catch (loadError) {
    error.value = errorMessage(loadError)
  } finally {
    loading.value = false
  }
}

const openThread = async (threadId: string) => {
  detailLoading.value = true
  try {
    selectedThread.value = await getEmailThread(threadId)
    syncQueryToRoute()
  } catch (threadError) {
    message.error(errorMessage(threadError))
  } finally {
    detailLoading.value = false
  }
}

const linkSelectedThread = async () => {
  if (!selectedThread.value) return
  if (!selectedCampaignId.value && !selectedDealId.value) {
    message.error('Select a campaign or deal before linking.')
    return
  }
  try {
    await linkEmailThread(selectedThread.value.id, {
      campaign_id: selectedCampaignId.value,
      deal_id: selectedDealId.value,
    })
    selectedThread.value = await getEmailThread(selectedThread.value.id)
    await loadThreads()
    message.success('Thread linked.')
  } catch (linkError) {
    message.error(errorMessage(linkError))
  }
}

const unlink = async (link: EmailCrmLink) => {
  if (!selectedThread.value) return
  try {
    await unlinkEmailThread(selectedThread.value.id, {
      campaignId: link.campaign_id ?? undefined,
      dealId: link.deal_id ?? undefined,
    })
    selectedThread.value = await getEmailThread(selectedThread.value.id)
    await loadThreads()
    message.success('Thread unlinked.')
  } catch (unlinkError) {
    message.error(errorMessage(unlinkError))
  }
}

const participantLabel = (thread: GmailThreadSummary) => {
  const first = thread.participants[0]
  return first?.name || first?.email || 'Unknown sender'
}

const formatDate = (value?: string | null) => {
  if (!value) return 'No date'
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

const threadLinkLabel = (link: EmailCrmLink) => {
  if (link.type === 'campaign') return 'Campaign'
  if (link.type === 'deal') return 'Deal'
  return link.type
}

watch(selectedCampaignId, async () => {
  selectedDealId.value = undefined
  await loadDeals()
  await loadThreads()
})

watch([selectedDealId, selectedLabel], async () => {
  await loadThreads()
})

onMounted(async () => {
  try {
    await Promise.all([loadAuthStatus(), loadCampaigns()])
    await loadDeals()
    if (connected.value) {
      await loadLabels()
      const threadId = route.query.threadId as string | undefined
      await loadThreads()
      if (threadId) await openThread(threadId)
    }
  } catch (pageError) {
    error.value = errorMessage(pageError)
  }
})
</script>

<template>
  <section class="email-page">
    <div class="page-header">
      <div>
        <h1>Email</h1>
        <p>Gmail threads with campaign and deal labels.</p>
      </div>
      <a-space>
        <a-tag v-if="connected" color="green">{{ authStatus?.email }}</a-tag>
        <a-button v-if="connected" :loading="authLoading" @click="disconnect">Disconnect</a-button>
        <a-button v-else type="primary" :loading="authLoading" @click="connectGmail">
          Connect Gmail
        </a-button>
      </a-space>
    </div>

    <a-alert
      v-if="!connected"
      type="info"
      show-icon
      message="Connect Gmail"
      description="Desktop IRM stores only the local OAuth credential. Threads and CRM links stay in Gmail labels."
    />

    <a-alert v-if="error" class="page-alert" type="error" show-icon :message="error" />

    <template v-if="connected">
      <div class="filters">
        <a-input-search
          v-model:value="query"
          class="query-input"
          placeholder="Search Gmail"
          enter-button="Search"
          @search="() => loadThreads()"
        />
        <a-select
          v-model:value="selectedCampaignId"
          class="filter-select"
          allow-clear
          placeholder="Campaign"
          :options="campaignOptions"
        />
        <a-select
          v-model:value="selectedDealId"
          class="filter-select"
          allow-clear
          placeholder="Deal"
          :disabled="!selectedCampaignId"
          :options="dealOptions"
        />
        <a-select
          v-model:value="selectedLabel"
          class="filter-select"
          allow-clear
          show-search
          placeholder="Gmail label"
          :options="labelOptions"
        />
      </div>

      <div class="email-workspace">
        <a-card class="thread-list-card" :body-style="{ padding: 0 }">
          <div class="thread-list-header">
            <strong>Threads</strong>
            <a-button size="small" :loading="loading" @click="() => loadThreads()">Refresh</a-button>
          </div>
          <a-list :loading="loading" :data-source="threads" item-layout="vertical">
            <template #renderItem="{ item }">
              <a-list-item
                class="thread-row"
                :class="{ active: item.id === selectedThreadId }"
                @click="openThread(item.id)"
              >
                <div class="thread-row-top">
                  <strong>{{ participantLabel(item) }}</strong>
                  <span>{{ formatDate(item.last_message_at) }}</span>
                </div>
                <div class="thread-subject">{{ item.subject || '(No subject)' }}</div>
                <p>{{ item.snippet }}</p>
                <div v-if="item.crm_links.length" class="tag-row">
                  <a-tag v-for="link in item.crm_links" :key="link.label_id">
                    {{ threadLinkLabel(link) }}
                  </a-tag>
                </div>
              </a-list-item>
            </template>
          </a-list>
          <div class="load-more" v-if="nextPageToken">
            <a-button :loading="loading" @click="loadThreads(nextPageToken)">Load more</a-button>
          </div>
        </a-card>

        <a-card class="thread-detail-card">
          <a-spin :spinning="detailLoading">
            <template v-if="selectedThread">
              <div class="thread-detail-header">
                <div>
                  <h2>{{ selectedThread.subject || '(No subject)' }}</h2>
                  <p>{{ selectedThread.message_count }} messages</p>
                </div>
                <a-button type="primary" @click="linkSelectedThread">Link current filter</a-button>
              </div>

              <div class="link-panel">
                <strong>CRM labels</strong>
                <div v-if="selectedThread.crm_links.length" class="tag-row">
                  <a-tag
                    v-for="link in selectedThread.crm_links"
                    :key="link.label_id"
                    closable
                    @close.prevent="unlink(link)"
                  >
                    {{ threadLinkLabel(link) }}
                  </a-tag>
                </div>
                <span v-else class="muted">No campaign or deal label yet.</span>
              </div>

              <div class="message-stack">
                <article v-for="mail in selectedThread.messages" :key="mail.id" class="message-card">
                  <header>
                    <div>
                      <strong>{{ mail.sender?.name || mail.sender?.email || 'Unknown sender' }}</strong>
                      <span>{{ mail.sender?.email }}</span>
                    </div>
                    <time>{{ formatDate(mail.sent_at) }}</time>
                  </header>
                  <pre v-if="mail.body_text">{{ mail.body_text }}</pre>
                  <iframe
                    v-else-if="mail.body_html"
                    sandbox=""
                    class="html-frame"
                    :srcdoc="mail.body_html"
                  />
                  <p v-else class="muted">{{ mail.snippet || 'No readable message body.' }}</p>
                </article>
              </div>
            </template>
            <a-empty v-else description="Select a Gmail thread." />
          </a-spin>
        </a-card>
      </div>
    </template>
  </section>
</template>

<style scoped>
.email-page {
  display: grid;
  gap: 18px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header h1,
.thread-detail-header h2 {
  margin: 0;
  color: #20262d;
}

.page-header p,
.thread-detail-header p,
.thread-row p,
.muted {
  margin: 0;
  color: #697582;
}

.page-alert {
  margin-top: -4px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.query-input {
  width: min(420px, 100%);
}

.filter-select {
  width: 220px;
}

.email-workspace {
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  gap: 16px;
  min-height: 660px;
}

.thread-list-card,
.thread-detail-card {
  min-width: 0;
  overflow: hidden;
}

.thread-list-header,
.thread-detail-header,
.link-panel,
.message-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.thread-list-header {
  padding: 14px 16px;
  border-bottom: 1px solid #edf0f3;
}

.thread-row {
  cursor: pointer;
  padding: 14px 16px;
}

.thread-row.active {
  background: #eef8f4;
}

.thread-row-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #20262d;
}

.thread-row-top span {
  color: #697582;
  font-size: 12px;
  white-space: nowrap;
}

.thread-subject {
  margin-top: 4px;
  color: #20262d;
  font-weight: 600;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.load-more {
  padding: 14px 16px;
  text-align: center;
}

.thread-detail-card {
  min-height: 660px;
}

.thread-detail-header {
  align-items: flex-start;
  margin-bottom: 16px;
}

.link-panel {
  align-items: flex-start;
  padding: 12px;
  border: 1px solid #dce5df;
  border-radius: 8px;
  background: #f7fbf9;
}

.message-stack {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.message-card {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid #e0e5eb;
  border-radius: 8px;
  background: #ffffff;
}

.message-card header div {
  display: grid;
  gap: 2px;
}

.message-card header span,
.message-card time {
  color: #697582;
  font-size: 12px;
}

.message-card pre {
  margin: 0;
  overflow-x: auto;
  color: #20262d;
  font-family: inherit;
  line-height: 1.55;
  white-space: pre-wrap;
}

.html-frame {
  width: 100%;
  min-height: 260px;
  border: 1px solid #edf0f3;
  border-radius: 8px;
  background: #ffffff;
}

@media (max-width: 1100px) {
  .email-workspace {
    grid-template-columns: 1fr;
  }

  .filter-select,
  .query-input {
    width: 100%;
  }
}
</style>
