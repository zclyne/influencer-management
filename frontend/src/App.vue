<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { apiRoot, errorMessage, listCampaigns } from './api/client'
import type { CampaignResponse } from './api/types'
import { navigationItems, type NavigationKey } from './app/navigation'

const route = useRoute()
const campaigns = ref<CampaignResponse[]>([])
const selectedCampaignId = ref<string | null>(null)
const antTheme = {
  token: {
    borderRadius: 8,
    colorPrimary: '#216b55',
    colorInfo: '#216b55',
  },
}

const activeNavigationKey = computed<NavigationKey>(() => {
  const path = route.path
  if (path.startsWith('/influencers')) return 'influencers'
  if (path.startsWith('/brands')) return 'brands'
  if (path.startsWith('/email')) return 'email'
  if (path.startsWith('/templates')) return 'templates'
  return 'campaigns'
})

const loadCampaignContext = async () => {
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
  } catch (contextError) {
    console.error(errorMessage(contextError))
  }
}

const selectCampaign = (campaignId: string) => {
  selectedCampaignId.value = campaignId || null
}

onMounted(loadCampaignContext)
</script>

<template>
  <a-config-provider :theme="antTheme">
    <a-layout class="app-shell">
      <a-layout-sider class="sidebar" width="244">
        <div class="brand-block">
          <span class="brand-mark">IRM</span>
          <div>
            <strong>Desktop IRM</strong>
            <span>Local workbench</span>
          </div>
        </div>

        <a-menu class="nav-menu" theme="dark" mode="inline" :selected-keys="[activeNavigationKey]">
          <a-menu-item v-for="item in navigationItems" :key="item.key">
            <RouterLink :to="item.path" class="nav-link">
              <span>{{ item.label }}</span>
              <small>{{ item.detail }}</small>
            </RouterLink>
          </a-menu-item>
        </a-menu>
      </a-layout-sider>

      <a-layout>
        <a-layout-header class="top-bar">
          <div>
            <strong>Desktop IRM</strong>
            <span>Campaign-first workspace</span>
          </div>
          <div class="api-box">
            <span>API base</span>
            <code>{{ apiRoot }}</code>
          </div>
        </a-layout-header>

        <a-layout-content class="content-area">
          <RouterView v-slot="{ Component, route: matchedRoute }">
            <component
              :is="Component"
              v-if="matchedRoute.meta.campaignContext"
              :campaigns="campaigns"
              :selected-campaign-id="selectedCampaignId"
              @campaign-changed="selectCampaign"
            />
            <component :is="Component" v-else />
          </RouterView>
        </a-layout-content>
      </a-layout>
    </a-layout>
  </a-config-provider>
</template>

<style>
:root {
  color: #20262d;
  background: #f2f5f8;
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
  min-height: 100vh;
  background: #f2f5f8;
}

.sidebar {
  background: #202624;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 64px;
  padding: 14px 18px;
  color: #ffffff;
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
  color: #bac8c0;
  font-size: 12px;
}

.nav-menu {
  border-inline-end: 0;
  background: transparent;
}

.nav-link {
  display: grid;
  gap: 2px;
  line-height: 1.2;
}

.nav-link small {
  color: #b8c3be;
  font-size: 11px;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 64px;
  padding: 0 24px;
  border-bottom: 1px solid #dce2ea;
  background: #ffffff;
}

.top-bar div:first-child {
  display: grid;
  gap: 2px;
}

.top-bar strong {
  color: #20262d;
}

.top-bar span {
  color: #697582;
  font-size: 12px;
}

.api-box {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #697582;
  font-size: 12px;
}

.api-box code {
  max-width: 420px;
  overflow: hidden;
  color: #20262d;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content-area {
  min-width: 0;
  padding: 24px;
}

@media (max-width: 760px) {
  .app-shell {
    display: block;
  }

  .sidebar {
    width: 100% !important;
    max-width: none !important;
    min-width: 0 !important;
  }

  .top-bar {
    align-items: flex-start;
    height: auto;
    padding: 14px 16px;
  }

  .api-box {
    display: none;
  }

  .content-area {
    padding: 16px;
  }
}
</style>
