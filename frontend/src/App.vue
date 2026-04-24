<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiRoot, createCampaign, errorMessage, listCampaigns } from './api/client'
import type { CampaignCreateRequest, CampaignResponse, WorkbenchDeal } from './api/types'
import { navigationItems, type WorkbenchView } from './app/navigation'
import CampaignWorkspace from './campaigns/CampaignWorkspace.vue'
import DealDetailDrawer from './deals/DealDetailDrawer.vue'
import ImportWizard from './ingestion/ImportWizard.vue'
import InfluencerLibrary from './influencers/InfluencerLibrary.vue'

const activeView = ref<WorkbenchView>('campaigns')
const campaigns = ref<CampaignResponse[]>([])
const selectedCampaignId = ref<string | null>(null)
const campaignsLoading = ref(false)
const campaignsError = ref<string | null>(null)
const drawerOpen = ref(false)
const selectedDeal = ref<WorkbenchDeal | null>(null)

const selectedCampaign = computed(
  () => campaigns.value.find((campaign) => campaign.id === selectedCampaignId.value) ?? null,
)

const loadCampaigns = async () => {
  campaignsLoading.value = true
  campaignsError.value = null

  try {
    const response = await listCampaigns()
    campaigns.value = response.campaigns

    if (!selectedCampaignId.value && response.campaigns.length > 0) {
      selectedCampaignId.value = response.campaigns[0].id
    }

    if (
      selectedCampaignId.value &&
      !response.campaigns.some((campaign) => campaign.id === selectedCampaignId.value)
    ) {
      selectedCampaignId.value = response.campaigns[0]?.id ?? null
    }
  } catch (error) {
    campaignsError.value = errorMessage(error)
  } finally {
    campaignsLoading.value = false
  }
}

const handleCreateCampaign = async (payload: CampaignCreateRequest) => {
  campaignsError.value = null

  try {
    const created = await createCampaign(payload)
    campaigns.value = [created, ...campaigns.value]
    selectedCampaignId.value = created.id
  } catch (error) {
    campaignsError.value = errorMessage(error)
  }
}

const selectCampaign = (campaignId: string) => {
  selectedCampaignId.value = campaignId
}

const importForCampaign = (campaignId: string) => {
  selectedCampaignId.value = campaignId
  activeView.value = 'imports'
}

const openDealDetail = (deal: WorkbenchDeal | null) => {
  selectedDeal.value =
    deal ??
    ({
      id: 'pending-api',
      influencerName: 'Deal detail scaffold',
      status: 'DRAFT',
      labels: ['deliverables', 'compensation', 'email'],
      nextAction: 'Load a campaign deal once the Deal Pipeline API is available.',
    } satisfies WorkbenchDeal)
  drawerOpen.value = true
}

onMounted(loadCampaigns)
</script>

<template>
  <main class="app-shell">
    <aside class="sidebar" aria-label="Desktop IRM navigation">
      <div class="brand-block">
        <span class="brand-mark">IRM</span>
        <div>
          <strong>Desktop IRM</strong>
          <span>Local workbench</span>
        </div>
      </div>

      <nav class="nav-list">
        <button
          v-for="item in navigationItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: activeView === item.key }"
          type="button"
          @click="activeView = item.key"
        >
          <span>{{ item.label }}</span>
          <small>{{ item.detail }}</small>
        </button>
      </nav>

      <div class="api-box">
        <span>API base</span>
        <code>{{ apiRoot }}</code>
      </div>
    </aside>

    <section class="content-area">
      <CampaignWorkspace
        v-if="activeView === 'campaigns'"
        :campaigns="campaigns"
        :selected-campaign-id="selectedCampaignId"
        :loading="campaignsLoading"
        :error="campaignsError"
        @refresh="loadCampaigns"
        @select-campaign="selectCampaign"
        @create-campaign="handleCreateCampaign"
        @import-for-campaign="importForCampaign"
        @open-deal="openDealDetail"
      />

      <InfluencerLibrary
        v-else-if="activeView === 'influencers'"
        :campaigns="campaigns"
        :selected-campaign-id="selectedCampaignId"
        @campaign-changed="selectCampaign"
      />

      <ImportWizard
        v-else
        :campaigns="campaigns"
        :selected-campaign-id="selectedCampaignId"
        @campaign-changed="selectCampaign"
      />
    </section>

    <DealDetailDrawer
      :open="drawerOpen"
      :campaign-name="selectedCampaign?.name"
      :deal="selectedDeal"
      @close="drawerOpen = false"
    />
  </main>
</template>

<style>
:root {
  color: #242826;
  background: #eef2f6;
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button,
input,
select,
textarea {
  letter-spacing: 0;
}
</style>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 244px minmax(0, 1fr);
  min-height: 100vh;
  background: #eef2f6;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-width: 0;
  padding: 18px;
  border-right: 1px solid #d7dee8;
  background: #242826;
  color: #ffffff;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 8px;
  background: #e8f5ef;
  color: #215f4e;
  font-weight: 900;
}

.brand-block div {
  display: grid;
  gap: 3px;
}

.brand-block strong {
  font-size: 15px;
}

.brand-block span:last-child {
  color: #bcc7bd;
  font-size: 12px;
}

.nav-list {
  display: grid;
  gap: 8px;
}

.nav-item {
  display: grid;
  gap: 3px;
  width: 100%;
  min-height: 54px;
  padding: 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #e1e8e1;
  text-align: left;
  cursor: pointer;
}

.nav-item span {
  font-weight: 800;
}

.nav-item small {
  color: #bcc7bd;
}

.nav-item.active {
  border-color: #8dbfaf;
  background: #303a33;
  color: #ffffff;
}

.api-box {
  display: grid;
  gap: 6px;
  margin-top: auto;
  padding: 10px;
  border: 1px solid #414941;
  border-radius: 8px;
  color: #bcc7bd;
  font-size: 12px;
}

.api-box code {
  overflow-wrap: anywhere;
  color: #ffffff;
}

.content-area {
  min-width: 0;
  padding: 24px;
}

@media (max-width: 760px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: sticky;
    top: 0;
    z-index: 5;
    gap: 12px;
  }

  .nav-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .api-box {
    display: none;
  }

  .content-area {
    padding: 16px;
  }
}
</style>
